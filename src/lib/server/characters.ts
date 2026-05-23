import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import type { Character } from '$lib/types/meme';

const ROOT = process.cwd();
const FILES = join(ROOT, 'files');
const CHARACTERS_FILE = join(FILES, 'characters.json');
const CUSTOM_FILE = join(FILES, 'characters.custom.json');

type CharactersFile = { characters: Character[] };

function readJsonFile(path: string): CharactersFile {
	if (!existsSync(path)) return { characters: [] };
	return JSON.parse(readFileSync(path, 'utf-8')) as CharactersFile;
}

export function listCharacters(): Character[] {
	const base = readJsonFile(CHARACTERS_FILE).characters;
	const custom = readJsonFile(CUSTOM_FILE).characters;
	const byId = new Map<string, Character>();
	for (const c of [...base, ...custom]) byId.set(c.id, c);
	return [...byId.values()];
}

export function getCharactersByIds(ids: string[]): Character[] {
	const all = listCharacters();
	const map = new Map(all.map((c) => [c.id, c]));
	return ids.map((id) => map.get(id)).filter((c): c is Character => Boolean(c));
}

export function getCharacter(id: string): Character | undefined {
	return listCharacters().find((c) => c.id === id);
}

export function slugifyId(name: string): string {
	return name
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '')
		.slice(0, 48);
}

export function addCharacter(input: Omit<Character, 'id' | 'builtin'> & { id?: string }): Character {
	const id = input.id?.trim() || slugifyId(input.name);
	if (!id) throw new Error('Invalid character name');

	const character: Character = {
		id,
		name: input.name.trim(),
		nameVi: input.nameVi?.trim(),
		description: input.description.trim(),
		archetype: input.archetype?.trim(),
		visualPrompt: input.visualPrompt.trim(),
		referenceMemeId: input.referenceMemeId ?? null,
		referenceImagePath: input.referenceImagePath ?? null,
		builtin: false
	};

	if (getCharacter(id)) throw new Error(`Character "${id}" already exists`);

	try {
		mkdirSync(FILES, { recursive: true });
		const custom = readJsonFile(CUSTOM_FILE);
		custom.characters.push(character);
		writeFileSync(CUSTOM_FILE, JSON.stringify(custom, null, 2), 'utf-8');
	} catch {
		// Read-only FS (e.g. Vercel) — caller may persist client-side
	}

	return character;
}
