// Server-only: Supabase admin client + OpenAI
import { createClient } from '@supabase/supabase-js';
import OpenAI from 'openai';
import { PUBLIC_SUPABASE_URL } from '$env/static/public';
import { SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, OPENAI_BASE_URL } from '$env/static/private';
import { env } from '$env/dynamic/private';
import { formatOpenAIError } from '$lib/server/openai-errors';

export const supabaseAdmin = createClient(PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

export const openai = new OpenAI({
	apiKey: OPENAI_API_KEY,
	baseURL: OPENAI_BASE_URL || 'https://api.openai.com/v1',
});

function embedModel(): string {
	return env.OPENAI_EMBED_MODEL || 'openai/text-embedding-3-small';
}

export async function embedText(text: string): Promise<number[]> {
	const resp = await openai.embeddings.create({
		model: embedModel(),
		input: [text],
	});
	return resp.data[0].embedding;
}

export interface MemeResult {
	id: string;
	image_path: string;
	layout: Record<string, unknown> | string;
	character_position: Record<string, unknown> | string;
	text_style: Record<string, unknown> | string;
	content_structure: string;
	description: string;
	similarity: number;
}

type MemeRow = Omit<MemeResult, 'similarity'>;

function queryTerms(query: string): string[] {
	return [...new Set(query.toLowerCase().match(/[a-z0-9\u00C0-\u1EF9]{3,}/gi) ?? [])].slice(0, 10);
}

function scoreKeywordMatch(row: MemeRow, terms: string[]): number {
	const haystack = `${row.description} ${row.content_structure} ${row.id}`.toLowerCase();
	if (!terms.length) return 0.35;
	const hits = terms.filter((t) => haystack.includes(t.toLowerCase())).length;
	return hits / terms.length;
}

async function searchMemesKeyword(query: string, k: number): Promise<MemeResult[]> {
	const terms = queryTerms(query);

	let rows: MemeRow[] = [];

	if (terms.length) {
		const orFilter = terms.map((t) => `description.ilike.%${t}%`).join(',');
		const { data, error } = await supabaseAdmin
			.from('memes')
			.select(
				'id, image_path, layout, character_position, text_style, content_structure, description'
			)
			.or(orFilter)
			.limit(Math.max(k * 4, 24));

		if (error) throw new Error(error.message);
		rows = (data ?? []) as MemeRow[];
	}

	if (!rows.length) {
		const { data, error } = await supabaseAdmin
			.from('memes')
			.select(
				'id, image_path, layout, character_position, text_style, content_structure, description'
			)
			.limit(k);
		if (error) throw new Error(error.message);
		rows = (data ?? []) as MemeRow[];
	}

	return rows
		.map((row) => ({
			...row,
			similarity: scoreKeywordMatch(row, terms)
		}))
		.sort((a, b) => b.similarity - a.similarity)
		.slice(0, k);
}

export type SearchMode = 'semantic' | 'keyword';

export async function searchMemes(
	query: string,
	k = 5
): Promise<{ results: MemeResult[]; mode: SearchMode; warning?: string }> {
	try {
		const embedding = await embedText(query);
		const { data, error } = await supabaseAdmin.rpc('match_memes', {
			query_embedding: embedding,
			match_count: k,
		});
		if (error) throw new Error(error.message);
		return { results: data as MemeResult[], mode: 'semantic' };
	} catch (e) {
		const warning = formatOpenAIError(e);
		const results = await searchMemesKeyword(query, k);
		if (!results.length) throw new Error(warning);
		return { results, mode: 'keyword', warning };
	}
}
