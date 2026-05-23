import { json } from '@sveltejs/kit';
import { searchMemes } from '$lib/server/ai';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
	const { query, k = 5 } = await request.json();
	if (!query?.trim()) return json({ error: 'query required' }, { status: 400 });

	try {
		const results = await searchMemes(query.trim(), k);
		return json({ query, results });
	} catch (e: unknown) {
		const msg = e instanceof Error ? e.message : String(e);
		return json({ error: msg }, { status: 500 });
	}
};
