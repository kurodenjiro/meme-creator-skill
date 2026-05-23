import { error } from '@sveltejs/kit';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { IMAGE_DIR } from '$env/static/private';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	const filename = params.id;
	if (!filename || filename.includes('..') || filename.includes('/')) {
		throw error(400, 'Invalid filename');
	}

	const filePath = join(process.cwd(), IMAGE_DIR, filename);

	if (!existsSync(filePath)) {
		throw error(404, `Image not found: ${filename}`);
	}

	const imageBuffer = readFileSync(filePath);
	const ext = filename.split('.').pop()?.toLowerCase();
	const mimeMap: Record<string, string> = {
		jpg: 'image/jpeg',
		jpeg: 'image/jpeg',
		png: 'image/png',
		gif: 'image/gif',
		webp: 'image/webp',
	};

	return new Response(imageBuffer, {
		headers: {
			'Content-Type': mimeMap[ext || 'jpg'] || 'image/jpeg',
			'Cache-Control': 'public, max-age=31536000, immutable',
		},
	});
};
