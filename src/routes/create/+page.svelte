<script lang="ts">
	import type {
		Character,
		GenerateScriptResponse,
		MemeReference,
		MemeScript
	} from '$lib/types/meme';

	type Step = 'input' | 'script' | 'image';

	let step = $state<Step>('input');
	let trend = $state('Gas fee tăng vọt vì NFT drop, trader hoảng loạn');
	let hint = $state('');
	let characters = $state<Character[]>([]);
	let selectedIds = $state<string[]>(['wizard']);
	let customCharacters = $state<Character[]>([]);

	let scriptResult = $state<GenerateScriptResponse | null>(null);
	let generatedImageUrl = $state('');
	let finalPrompt = $state('');
	let imageModel = $state('');

	let loadingScript = $state(false);
	let loadingImage = $state(false);
	let errorMessage = $state('');

	let showAddCharacter = $state(false);
	let newChar = $state({
		name: '',
		nameVi: '',
		description: '',
		archetype: '',
		visualPrompt: '',
		referenceMemeId: ''
	});

	const allCharacters = $derived([...characters, ...customCharacters]);

	const selectedCharacters = $derived(
		allCharacters.filter((c) => selectedIds.includes(c.id))
	);

	const imageUrl = (id: string) => `/api/image/${encodeURIComponent(id)}`;

	function toggleCharacter(id: string) {
		if (selectedIds.includes(id)) {
			selectedIds = selectedIds.filter((x) => x !== id);
		} else {
			selectedIds = [...selectedIds, id];
		}
	}

	async function loadCharacters() {
		try {
			const res = await fetch('/api/characters');
			const data = await res.json();
			characters = data.characters ?? [];
		} catch {
			errorMessage = 'Không tải được danh sách nhân vật';
		}

		try {
			const stored = localStorage.getItem('customCharacters');
			if (stored) customCharacters = JSON.parse(stored);
		} catch {
			/* ignore */
		}
	}

	async function addCharacter() {
		errorMessage = '';
		try {
			const res = await fetch('/api/characters', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					...newChar,
					referenceMemeId: newChar.referenceMemeId || null
				})
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.error || 'Failed to add character');

			const char = data.character as Character;
			if (!data.persisted) {
				customCharacters = [...customCharacters.filter((c) => c.id !== char.id), char];
				localStorage.setItem('customCharacters', JSON.stringify(customCharacters));
			} else {
				await loadCharacters();
			}

			selectedIds = [...selectedIds, char.id];
			showAddCharacter = false;
			newChar = {
				name: '',
				nameVi: '',
				description: '',
				archetype: '',
				visualPrompt: '',
				referenceMemeId: ''
			};
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : String(e);
		}
	}

	async function generateScript() {
		if (!trend.trim() || !selectedIds.length) return;
		loadingScript = true;
		errorMessage = '';
		scriptResult = null;
		generatedImageUrl = '';

		try {
			const res = await fetch('/api/generate/script', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					trend: trend.trim(),
					characterIds: selectedIds,
					hint: hint.trim() || undefined,
					referenceCount: 3
				})
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.error || 'Script generation failed');
			scriptResult = data as GenerateScriptResponse;
			step = 'script';
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : String(e);
		} finally {
			loadingScript = false;
		}
	}

	async function generateImage() {
		if (!scriptResult) return;
		loadingImage = true;
		errorMessage = '';

		try {
			const res = await fetch('/api/generate/image', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					script: scriptResult.script,
					characterIds: selectedIds,
					referenceIds: scriptResult.references.map((r) => r.id)
				})
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.error || 'Image generation failed');
			generatedImageUrl = data.imageUrl;
			finalPrompt = data.finalPrompt ?? '';
			imageModel = data.model ?? '';
			step = 'image';
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : String(e);
		} finally {
			loadingImage = false;
		}
	}

	function downloadImage() {
		if (!generatedImageUrl) return;
		const a = document.createElement('a');
		a.href = generatedImageUrl;
		a.download = `meme-${Date.now()}.png`;
		a.click();
	}

	$effect(() => {
		loadCharacters();
	});
</script>

<svelte:head>
	<title>Tạo meme — Boldleonidas</title>
</svelte:head>

<main class="shell">
	<header class="top">
		<div>
			<p class="eyebrow">Meme creator</p>
			<h1>Trend → kịch bản → ảnh</h1>
			<p class="lede">
				Chọn nhân vật, nhập trend, AI tham chiếu archive + <code>style.md</code>, tạo kịch bản rồi
				render bằng gpt-image.
			</p>
		</div>
		<nav>
			<a href="/">Tìm kiếm</a>
			<a href="/create" class="active">Tạo meme</a>
		</nav>
	</header>

	{#if errorMessage}
		<div class="notice" role="alert">{errorMessage}</div>
	{/if}

	<section class="panel">
		<h2>1. Trend & nhân vật</h2>

		<label for="trend">Trend / chủ đề</label>
		<textarea id="trend" bind:value={trend} rows="3" placeholder="Mô tả trend, tình huống crypto..."></textarea>

		<label for="hint">Gợi ý thêm (tuỳ chọn)</label>
		<input id="hint" bind:value={hint} placeholder="Tone hài, 2 panel, punchline..." />

		<div class="char-header">
			<span>Nhân vật</span>
			<button type="button" class="ghost" onclick={() => (showAddCharacter = !showAddCharacter)}>
				{showAddCharacter ? 'Đóng' : '+ Thêm nhân vật'}
			</button>
		</div>

		{#if showAddCharacter}
			<form
				class="add-char"
				onsubmit={(e) => {
					e.preventDefault();
					addCharacter();
				}}
			>
				<input bind:value={newChar.name} placeholder="Tên (EN)" required />
				<input bind:value={newChar.nameVi} placeholder="Tên (VI)" />
				<textarea
					bind:value={newChar.description}
					placeholder="Mô tả ngoại hình"
					required
					rows="2"
				></textarea>
				<input bind:value={newChar.archetype} placeholder="Vai trò / archetype" />
				<textarea
					bind:value={newChar.visualPrompt}
					placeholder="Visual prompt (EN) cho AI vẽ"
					required
					rows="2"
				></textarea>
				<input
					bind:value={newChar.referenceMemeId}
					placeholder="ID ảnh tham chiếu nhân vật (vd: xxx_1.jpg)"
				/>
				<button type="submit">Lưu nhân vật</button>
			</form>
		{/if}

		<div class="char-grid">
			{#each allCharacters as char}
				<button
					type="button"
					class="char-card"
					class:selected={selectedIds.includes(char.id)}
					onclick={() => toggleCharacter(char.id)}
				>
					<strong>{char.nameVi || char.name}</strong>
					<span>{char.name}</span>
					<p>{char.description.slice(0, 90)}…</p>
				</button>
			{/each}
		</div>

		<button
			type="button"
			class="primary"
			disabled={loadingScript || !trend.trim() || !selectedIds.length}
			onclick={generateScript}
		>
			{loadingScript ? 'Đang tạo kịch bản…' : 'Tạo kịch bản'}
		</button>
	</section>

	{#if scriptResult}
		<section class="panel">
			<h2>2. Kịch bản & ảnh tham khảo</h2>
			<p class="analysis">{scriptResult.script.conceptAnalysis}</p>

			<div class="refs">
				{#each scriptResult.references as ref}
					<figure>
						<img src={imageUrl(ref.id)} alt={ref.description} loading="lazy" />
						<figcaption>{Math.round((ref.similarity ?? 0) * 100)}% — {ref.id}</figcaption>
					</figure>
				{/each}
			</div>

			<pre class="blueprint">{scriptResult.blueprintMarkdown}</pre>

			<details>
				<summary>Image prompt (EN)</summary>
				<p class="prompt">{scriptResult.script.imagePrompt}</p>
			</details>

			<button
				type="button"
				class="primary"
				disabled={loadingImage}
				onclick={generateImage}
			>
				{loadingImage ? 'Đang tạo ảnh (gpt-image)…' : 'Tạo ảnh với tham chiếu + kịch bản'}
			</button>
		</section>
	{/if}

	{#if generatedImageUrl}
		<section class="panel result">
			<h2>3. Kết quả</h2>
			{#if imageModel}
				<p class="meta">Model: {imageModel}</p>
			{/if}
			<img class="output" src={generatedImageUrl} alt="Generated meme" />
			{#if finalPrompt}
				<details>
					<summary>Prompt cuối gửi lên image model</summary>
					<p class="prompt">{finalPrompt}</p>
				</details>
			{/if}
			<button type="button" class="primary" onclick={downloadImage}>Tải ảnh</button>
		</section>
	{/if}
</main>

<style>
	:global(body) {
		margin: 0;
		background: #0b0c0c;
		color: #f8f3e6;
		font-family: Avenir Next, Gill Sans, sans-serif;
	}

	.shell {
		max-width: 1100px;
		margin: 0 auto;
		padding: 24px;
	}

	.top {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		align-items: flex-end;
		margin-bottom: 24px;
		border-left: 5px solid #e8ff65;
		padding-left: 20px;
	}

	.eyebrow {
		color: #e8ff65;
		font-size: 0.75rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		margin: 0 0 8px;
	}

	h1 {
		margin: 0 0 10px;
		font-family: Georgia, serif;
		font-size: clamp(2rem, 5vw, 3.2rem);
	}

	.lede {
		margin: 0;
		color: #cfc6ad;
		max-width: 520px;
		line-height: 1.5;
	}

	nav {
		display: flex;
		gap: 10px;
	}

	nav a {
		color: #f8f3e6;
		text-decoration: none;
		padding: 8px 14px;
		border: 1px solid rgba(248, 243, 230, 0.2);
		border-radius: 6px;
		font-weight: 700;
		font-size: 0.9rem;
	}

	nav a.active {
		background: #e8ff65;
		color: #111;
		border-color: #e8ff65;
	}

	.panel {
		border: 1px solid rgba(248, 243, 230, 0.14);
		border-radius: 8px;
		padding: 20px;
		margin-bottom: 20px;
		background: rgba(255, 255, 255, 0.03);
	}

	h2 {
		margin: 0 0 16px;
		font-size: 1.2rem;
		color: #e8ff65;
	}

	label {
		display: block;
		margin: 12px 0 6px;
		font-size: 0.8rem;
		font-weight: 800;
		text-transform: uppercase;
		color: #cfc6ad;
	}

	textarea,
	input {
		width: 100%;
		padding: 10px 12px;
		border-radius: 6px;
		border: 1px solid rgba(248, 243, 230, 0.2);
		background: #f8f3e6;
		color: #111;
		font: inherit;
		box-sizing: border-box;
	}

	.char-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 16px;
	}

	.char-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 10px;
		margin: 12px 0 20px;
	}

	.char-card {
		text-align: left;
		padding: 12px;
		border-radius: 6px;
		border: 1px solid rgba(248, 243, 230, 0.15);
		background: rgba(0, 0, 0, 0.3);
		color: #f8f3e6;
		cursor: pointer;
	}

	.char-card.selected {
		border-color: #e8ff65;
		box-shadow: 0 0 0 2px rgba(232, 255, 101, 0.2);
	}

	.char-card strong {
		display: block;
		color: #e8ff65;
	}

	.char-card span {
		font-size: 0.8rem;
		color: #aaa;
	}

	.char-card p {
		margin: 8px 0 0;
		font-size: 0.82rem;
		color: #ccc;
	}

	.add-char {
		display: grid;
		gap: 8px;
		margin-bottom: 12px;
		padding: 12px;
		border: 1px dashed rgba(232, 255, 101, 0.4);
		border-radius: 6px;
	}

	button {
		font: inherit;
		cursor: pointer;
		border-radius: 6px;
		border: none;
		font-weight: 800;
	}

	.primary {
		background: #e8ff65;
		color: #111;
		padding: 12px 20px;
		margin-top: 8px;
	}

	.primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.ghost {
		background: transparent;
		color: #e8ff65;
		border: 1px solid rgba(232, 255, 101, 0.5);
		padding: 6px 12px;
	}

	.notice {
		background: rgba(255, 100, 80, 0.15);
		border: 1px solid rgba(255, 120, 100, 0.4);
		padding: 12px;
		border-radius: 6px;
		margin-bottom: 16px;
	}

	.analysis {
		line-height: 1.6;
		color: #efe8d5;
	}

	.refs {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 10px;
		margin: 16px 0;
	}

	.refs img {
		width: 100%;
		height: 120px;
		object-fit: cover;
		border-radius: 4px;
	}

	.refs figcaption {
		font-size: 0.7rem;
		color: #aaa;
		margin-top: 4px;
	}

	.blueprint {
		white-space: pre-wrap;
		font-size: 0.85rem;
		line-height: 1.5;
		background: #111;
		padding: 14px;
		border-radius: 6px;
		overflow-x: auto;
	}

	.prompt {
		font-size: 0.9rem;
		line-height: 1.5;
		color: #ccc;
	}

	.output {
		width: 100%;
		max-width: 640px;
		border-radius: 8px;
		display: block;
		margin: 12px 0;
	}

	.meta {
		font-size: 0.85rem;
		color: #aaa;
	}

	@media (max-width: 700px) {
		.top {
			flex-direction: column;
			align-items: flex-start;
		}
	}
</style>
