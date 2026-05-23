import { json } from '@sveltejs/kit';
import { addCharacter, listCharacters } from '$lib/server/characters';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	return json({ characters: listCharacters() });
};

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const { name, nameVi, description, archetype, visualPrompt, referenceMemeId, id } = body;

	if (!name?.trim() || !description?.trim() || !visualPrompt?.trim()) {
		return json(
			{ error: 'name, description, and visualPrompt are required' },
			{ status: 400 }
		);
	}

	try {
		const character = addCharacter({
			id,
			name,
			nameVi,
			description,
			archetype,
			visualPrompt,
			referenceMemeId
		});
		return json({ character, persisted: true });
	} catch (e: unknown) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('already exists')) {
			return json({ error: msg }, { status: 409 });
		}
		return json({ error: msg }, { status: 500 });
	}
};
