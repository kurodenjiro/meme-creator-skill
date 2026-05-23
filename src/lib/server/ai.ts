// Server-only: Supabase admin client + OpenAI
import { createClient } from '@supabase/supabase-js';
import OpenAI from 'openai';
import { PUBLIC_SUPABASE_URL } from '$env/static/public';
import { SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, OPENAI_BASE_URL } from '$env/static/private';

export const supabaseAdmin = createClient(PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

export const openai = new OpenAI({
	apiKey: OPENAI_API_KEY,
	baseURL: OPENAI_BASE_URL || 'https://api.openai.com/v1',
});

export async function embedText(text: string): Promise<number[]> {
	const resp = await openai.embeddings.create({
		model: 'text-embedding-3-small',
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

export async function searchMemes(query: string, k = 5): Promise<MemeResult[]> {
	const embedding = await embedText(query);
	const { data, error } = await supabaseAdmin.rpc('match_memes', {
		query_embedding: embedding,
		match_count: k,
	});
	if (error) throw new Error(error.message);
	return data as MemeResult[];
}
