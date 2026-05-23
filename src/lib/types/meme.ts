export type Character = {
	id: string;
	name: string;
	nameVi?: string;
	description: string;
	archetype?: string;
	visualPrompt?: string;
	usagePercent?: number;
	referenceMemeId?: string | null;
	referenceImageUrl?: string | null;
	referenceImagePath?: string | null;
	builtin?: boolean;
};

export type MemeReference = {
	id: string;
	image_path: string;
	layout: unknown;
	character_position: unknown;
	text_style: unknown;
	content_structure: string;
	description: string;
	similarity?: number;
	score?: number;
};

export type PanelScript = {
	panelNumber: number;
	visualScene: string;
	characterPlacement: string;
	speechBubble: string;
	secondaryElements?: string;
};

export type MemeScript = {
	conceptAnalysis: string;
	layoutType: '1-Panel' | '2-Panel' | '3-Panel';
	primaryCharacter: string;
	panels: PanelScript[];
	imagePrompt: string;
	styleNotes: string;
};

export type GenerateScriptRequest = {
	trend: string;
	characterIds: string[];
	hint?: string;
	referenceCount?: number;
	/** Pre-fetched references from live trend suggestions (skips server search). */
	references?: MemeReference[];
};

export type GenerateScriptResponse = {
	trend: string;
	characters: Character[];
	references: MemeReference[];
	script: MemeScript;
	blueprintMarkdown: string;
};

export type GenerateImageRequest = {
	script: MemeScript;
	characterIds: string[];
	referenceIds: string[];
};

export type GenerateImageResponse = {
	imageUrl: string;
	imageBase64?: string;
	finalPrompt: string;
	model: string;
};
