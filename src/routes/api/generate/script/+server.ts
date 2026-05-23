import { json } from '@sveltejs/kit';
import { generateMemeScript } from '$lib/server/meme-pipeline';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const { trend, characterIds, hint, referenceCount, references } = body;

	if (!trend?.trim()) {
		return json({ error: 'trend is required' }, { status: 400 });
	}
	if (!Array.isArray(characterIds) || characterIds.length === 0) {
		return json({ error: 'characterIds must be a non-empty array' }, { status: 400 });
	}

	try {
		const result = await generateMemeScript({
			trend: trend.trim(),
			characterIds,
			hint: hint?.trim(),
			referenceCount: referenceCount ?? 3,
			references: Array.isArray(references) ? references : undefined
		});
		return json(result);
	} catch (e: unknown) {
		const msg = e instanceof Error ? e.message : String(e);
		return json({ error: msg }, { status: 500 });
	}
};
