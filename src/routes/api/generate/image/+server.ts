import { json } from '@sveltejs/kit';
import { generateMemeImage } from '$lib/server/meme-pipeline';
import type { MemeScript } from '$lib/types/meme';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const { script, characterIds, referenceIds } = body as {
		script?: MemeScript;
		characterIds?: string[];
		referenceIds?: string[];
	};

	if (!script?.panels?.length) {
		return json({ error: 'script with panels is required' }, { status: 400 });
	}
	if (!Array.isArray(characterIds) || characterIds.length === 0) {
		return json({ error: 'characterIds required' }, { status: 400 });
	}

	try {
		const { imageBase64, finalPrompt, model } = await generateMemeImage(
			script,
			characterIds,
			referenceIds ?? []
		);

		return json({
			imageUrl: `data:image/png;base64,${imageBase64}`,
			imageBase64,
			finalPrompt,
			model
		});
	} catch (e: unknown) {
		const msg = e instanceof Error ? e.message : String(e);
		return json({ error: msg }, { status: 500 });
	}
};
