import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { openai, searchMemes, type MemeResult } from '$lib/server/ai';
import { getCharactersByIds } from '$lib/server/characters';
import type {
	Character,
	GenerateScriptRequest,
	GenerateScriptResponse,
	MemeScript,
	PanelScript,
	MemeReference
} from '$lib/types/meme';
import { IMAGE_DIR } from '$env/static/private';
import { env } from '$env/dynamic/private';

const ROOT = process.cwd();
const STYLE_FILE = join(ROOT, 'files', 'style.md');
const SKILL_FILE = join(ROOT, 'SKILL.md');

function readGuide(path: string): string {
	return existsSync(path) ? readFileSync(path, 'utf-8') : '';
}

function toReference(row: MemeResult): MemeReference {
	return {
		id: row.id,
		image_path: row.image_path,
		layout: row.layout,
		character_position: row.character_position,
		text_style: row.text_style,
		content_structure: row.content_structure,
		description: row.description,
		similarity: row.similarity
	};
}

export function resolveImagePath(filenameOrPath: string): string {
	const name = filenameOrPath.split('/').pop() || filenameOrPath;
	return join(ROOT, IMAGE_DIR, name);
}

export function loadImageBase64(filenameOrPath: string): string | null {
	const path = resolveImagePath(filenameOrPath);
	if (!existsSync(path)) return null;
	return readFileSync(path).toString('base64');
}

function panelsToMarkdown(script: MemeScript): string {
	const panelBlocks = script.panels
		.map(
			(p) => `**Panel ${p.panelNumber}:**
*   **Visual Scene:** ${p.visualScene}
*   **Character Placement & Size:** ${p.characterPlacement}
*   **Speech Bubble:** ${p.speechBubble}${p.secondaryElements ? `\n*   **Secondary Elements:** ${p.secondaryElements}` : ''}`
		)
		.join('\n\n');

	return `### Meme Blueprint

**Layout Type:** ${script.layoutType}
**Primary Character:** ${script.primaryCharacter}

---

${panelBlocks}

---

**Style notes:** ${script.styleNotes}

**Image prompt (EN):** ${script.imagePrompt}`;
}

function buildSearchQuery(trend: string, characters: Character[]): string {
	const names = characters.map((c) => c.name).join(' ');
	return `${names} ${trend}`.trim();
}

function chatModel(): string {
	return env.OPENAI_CHAT_MODEL || 'openai/gpt-4o-mini';
}

function imageModel(): string {
	if (env.OPENAI_IMAGE_MODEL) return env.OPENAI_IMAGE_MODEL;
	const base = env.OPENAI_BASE_URL || '';
	if (base.includes('ai-gateway.vercel')) return 'openai/gpt-image-1';
	return 'gpt-image-1';
}

/** Vercel AI Gateway rejects response_format json_object — parse from text instead. */
function parseJsonFromModel<T>(raw: string): T {
	const trimmed = raw.trim();
	try {
		return JSON.parse(trimmed) as T;
	} catch {
		const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
		if (fenced?.[1]) return JSON.parse(fenced[1].trim()) as T;
		const start = trimmed.indexOf('{');
		const end = trimmed.lastIndexOf('}');
		if (start >= 0 && end > start) {
			return JSON.parse(trimmed.slice(start, end + 1)) as T;
		}
		throw new Error('Model did not return valid JSON');
	}
}

function summarizeReference(r: MemeReference, i: number): string {
	const layout =
		typeof r.layout === 'string'
			? r.layout.slice(0, 200)
			: JSON.stringify(r.layout).slice(0, 200);
	return `Reference ${i + 1} (${r.id}, similarity ${(r.similarity ?? r.score ?? 0).toFixed(3)}):
  Description: ${(r.description || '').slice(0, 280)}
  Layout (summary): ${layout}
  Structure: ${String(r.content_structure || '').slice(0, 120)}`;
}

export async function generateMemeScript(
	req: GenerateScriptRequest
): Promise<GenerateScriptResponse> {
	const { trend, characterIds, hint, referenceCount = 3, references: presetRefs } = req;
	const characters = getCharactersByIds(characterIds);
	if (!characters.length) throw new Error('Select at least one character');

	const searchQuery = buildSearchQuery(trend, characters);
	let references: MemeReference[];
	if (presetRefs?.length) {
		references = presetRefs;
	} else {
		const { results } = await searchMemes(searchQuery, referenceCount);
		references = results.map(toReference);
	}

	const styleGuide = readGuide(STYLE_FILE).slice(0, 3500);
	const skillGuide = readGuide(SKILL_FILE).slice(0, 3500);

	const characterBlock = characters
		.map(
			(c) =>
				`- ${c.name} (${c.id}): ${c.description}. Visual: ${c.visualPrompt || c.description}`
		)
		.join('\n');

	const refBlock = references.map(summarizeReference).join('\n\n');

	const system = `You are a Boldleonidas comic meme writer. Output valid JSON only.

STYLE GUIDE:
${styleGuide}

SKILL:
${skillGuide}

Rules:
- Speech bubble text must be ALL CAPS
- Match panel layout patterns from references when appropriate
- imagePrompt must be English, detailed, hand-drawn comic style, flat gray backgrounds when suitable
- panels array length must match layoutType (1, 2, or 3 panels)`;

	const user = `Trend / topic:
${trend}

Characters to feature:
${characterBlock}

${hint ? `Extra direction:\n${hint}\n` : ''}

Similar memes from archive (use for layout and tone, do not copy verbatim):
${refBlock}

Return ONLY a single JSON object (no markdown fences) with keys:
conceptAnalysis, layoutType (1-Panel|2-Panel|3-Panel), primaryCharacter, panels (array with panelNumber, visualScene, characterPlacement, speechBubble, optional secondaryElements), imagePrompt, styleNotes`;

	const completion = await openai.chat.completions.create({
		model: chatModel(),
		messages: [
			{ role: 'system', content: system },
			{ role: 'user', content: user }
		],
		temperature: 0.75,
		max_tokens: 2000
	});

	const raw = completion.choices[0]?.message?.content;
	if (!raw) throw new Error('Empty script response from model');

	const script = parseJsonFromModel<MemeScript>(raw);
	if (!script.panels?.length) throw new Error('Invalid script: missing panels');

	return {
		trend,
		characters,
		references,
		script,
		blueprintMarkdown: panelsToMarkdown(script)
	};
}

type VisionMessage = {
	role: 'user';
	content: Array<
		| { type: 'text'; text: string }
		| { type: 'image_url'; image_url: { url: string; detail: 'high' | 'low' } }
	>;
};

export async function buildFinalImagePrompt(
	script: MemeScript,
	characters: Character[],
	references: MemeReference[]
): Promise<string> {
	const styleExcerpt = readGuide(STYLE_FILE).slice(0, 2500);

	const content: VisionMessage['content'] = [
		{
			type: 'text',
			text: `You write ONE image generation prompt for gpt-image-1.

Boldleonidas hand-drawn crypto comic style. Follow style guide excerpt:
${styleExcerpt}

Meme blueprint:
${panelsToMarkdown(script)}

Characters:
${characters.map((c) => `${c.name}: ${c.visualPrompt || c.description}`).join('\n')}

Study the attached reference memes for layout, bubble placement, and proportions.
Output ONLY the final English prompt (max 1200 chars), no markdown, no explanation.`
		}
	];

	for (const ref of references.slice(0, 3)) {
		const b64 = loadImageBase64(ref.id);
		if (b64) {
			content.push({
				type: 'image_url',
				image_url: { url: `data:image/jpeg;base64,${b64}`, detail: 'high' }
			});
		}
	}

	for (const c of characters) {
		if (c.referenceImageUrl) {
			content.push({
				type: 'image_url',
				image_url: { url: c.referenceImageUrl, detail: 'high' }
			});
		} else if (c.referenceMemeId) {
			const b64 = loadImageBase64(c.referenceMemeId);
			if (b64) {
				content.push({
					type: 'image_url',
					image_url: { url: `data:image/jpeg;base64,${b64}`, detail: 'high' }
				});
			}
		}
	}

	const completion = await openai.chat.completions.create({
		model: chatModel(),
		messages: [{ role: 'user', content }],
		max_tokens: 1500,
		temperature: 0.6
	});

	const prompt = completion.choices[0]?.message?.content?.trim();
	if (!prompt) throw new Error('Failed to build image prompt');
	return prompt.slice(0, 4000);
}

export async function generateMemeImage(
	script: MemeScript,
	characterIds: string[],
	referenceIds: string[]
): Promise<{ imageBase64: string; finalPrompt: string; model: string }> {
	const characters = getCharactersByIds(characterIds);
	const references: MemeReference[] = [];

	for (const id of referenceIds) {
		const b64 = loadImageBase64(id);
		if (b64) {
			references.push({
				id,
				image_path: id,
				layout: {},
				character_position: {},
				text_style: {},
				content_structure: '',
				description: ''
			});
		}
	}

	const finalPrompt = await buildFinalImagePrompt(script, characters, references);
	const model = imageModel();

	const resp = await openai.images.generate({
		model,
		prompt: finalPrompt,
		size: '1024x1024',
		quality: 'high',
		n: 1
	});

	const item = resp.data?.[0];
	if (!item) throw new Error('No image data returned from model');

	let imageBase64: string | undefined;

	if (item.b64_json) {
		imageBase64 = item.b64_json;
	} else if (item.url) {
		const imgRes = await fetch(item.url);
		if (!imgRes.ok) throw new Error('Failed to download generated image');
		const buf = Buffer.from(await imgRes.arrayBuffer());
		imageBase64 = buf.toString('base64');
	}

	if (!imageBase64) throw new Error('No image data returned from model');

	return { imageBase64, finalPrompt, model };
}
