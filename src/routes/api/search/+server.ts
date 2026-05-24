import { json } from '@sveltejs/kit';
import { searchMemes } from '$lib/server/ai';
import { formatOpenAIError } from '$lib/server/openai-errors';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const { query, k = 5 } = await request.json();
	if (!query?.trim()) return json({ error: 'query required' }, { status: 400 });

	try {
		const { results, mode, warning } = await searchMemes(query.trim(), k);
		return json({ query, results, mode, warning });
	} catch (e: unknown) {
		return json({ error: formatOpenAIError(e) }, { status: 500 });
	}
};
