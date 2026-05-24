<script lang="ts">
	import type { Character, GenerateScriptResponse, MemeReference } from '$lib/types/meme';

	const SUGGEST_DEBOUNCE_MS = 450;
	const SUGGEST_MIN_CHARS = 2;
	const SUGGEST_COUNT = 6;

	let trend = $state('');
	let hint = $state('');
	let characters = $state<Character[]>([]);
	let selectedIds = $state<string[]>(['wizard']);
	let customCharacters = $state<Character[]>([]);

	let suggestions = $state<MemeReference[]>([]);
	let selectedRefIds = $state<string[]>([]);
	let loadingSuggestions = $state(false);
	let suggestionQuery = $state('');
	let suggestionError = $state('');
	let suggestionWarning = $state('');

	let scriptResult = $state<GenerateScriptResponse | null>(null);
	let generatedImageUrl = $state('');
	let finalPrompt = $state('');
	let imageModel = $state('');
	let loadingScript = $state(false);
	let loadingImage = $state(false);
	let errorMessage = $state('');
	let newChar = $state({
		name: '',
		description: '',
		referenceImageUrl: ''
	});

	const allCharacters = $derived([...characters, ...customCharacters]);
	const selectedCharacters = $derived(allCharacters.filter((c) => selectedIds.includes(c.id)));
	const selectedReferences = $derived(
		suggestions.filter((r) => selectedRefIds.includes(r.id))
	);

	const imageUrl = (id: string) => `/api/image/${encodeURIComponent(id)}`;
	const scoreFor = (r: MemeReference) => r.similarity ?? r.score ?? 0;

	function buildSuggestQuery(): string {
		const names = selectedCharacters.map((c) => c.name).join(' ');
		return `${names} ${trend}`.trim();
	}

	function toggleCharacter(id: string) {
		selectedIds = selectedIds.includes(id)
			? selectedIds.filter((x) => x !== id)
			: [...selectedIds, id];
	}

	function toggleReference(id: string) {
		selectedRefIds = selectedRefIds.includes(id)
			? selectedRefIds.filter((x) => x !== id)
			: [...selectedRefIds, id];
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

	async function fetchSuggestions(query: string) {
		loadingSuggestions = true;
		suggestionQuery = query;
		suggestionError = '';
		suggestionWarning = '';
		try {
			const res = await fetch('/api/search', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query, k: SUGGEST_COUNT })
			});
			const data = await res.json();
			if (suggestionQuery !== query) return;
			if (!res.ok) throw new Error(data.error || 'Search failed');
			suggestions = (data.results ?? []).map((r: MemeReference) => ({
				...r,
				similarity: r.similarity ?? r.score
			}));
			selectedRefIds = suggestions.slice(0, 3).map((r) => r.id);
			if (data.warning) suggestionWarning = data.warning;
		} catch (e) {
			if (suggestionQuery === query) {
				suggestions = [];
				selectedRefIds = [];
				suggestionError = e instanceof Error ? e.message : String(e);
			}
		} finally {
			if (suggestionQuery === query) loadingSuggestions = false;
		}
	}

	async function addCharacter() {
		errorMessage = '';
		try {
			const res = await fetch('/api/characters', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newChar)
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
			newChar = { name: '', description: '', referenceImageUrl: '' };
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

		const refs =
			selectedReferences.length > 0
				? selectedReferences
				: suggestions.slice(0, 3);

		try {
			const res = await fetch('/api/generate/script', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					trend: trend.trim(),
					characterIds: selectedIds,
					hint: hint.trim() || undefined,
					references: refs.length ? refs : undefined
				})
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.error || 'Script generation failed');
			scriptResult = data as GenerateScriptResponse;
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

	$effect(() => {
		const trimmedTrend = trend.trim();
		trend;
		selectedIds;
		allCharacters;

		if (trimmedTrend.length < SUGGEST_MIN_CHARS) {
			suggestions = [];
			selectedRefIds = [];
			suggestionError = '';
			suggestionWarning = '';
			loadingSuggestions = false;
			return;
		}

		const query = buildSuggestQuery();
		const timer = setTimeout(() => fetchSuggestions(query), SUGGEST_DEBOUNCE_MS);
		return () => clearTimeout(timer);
	});
</script>

<svelte:head>
	<title>Boldleonidas — Tạo meme</title>
	<meta name="description" content="Tạo meme Boldleonidas từ trend và nhân vật, gợi ý tham chiếu từ archive." />
</svelte:head>

<main class="shell">
	<header class="hero">
		<p class="eyebrow">Boldleonidas meme creator</p>
		<h1>Trend → kịch bản → ảnh</h1>
		<p class="lede">
			Nhập trend — meme tương tự hiện ngay bên dưới. Chọn nhân vật, tạo kịch bản theo
			<code>style.md</code>, rồi render ảnh.
		</p>
	</header>

	{#if errorMessage}
		<section class="notice" role="alert">
			<strong>Lỗi</strong>
			<span>{errorMessage}</span>
		</section>
	{/if}

	<section class="panel">
		<label for="trend">Trend / chủ đề</label>
		<textarea
			id="trend"
			bind:value={trend}
			rows="3"
			placeholder="VD: Gas fee tăng vọt vì NFT drop, trader hoảng loạn..."
		></textarea>

		{#if trend.trim().length >= SUGGEST_MIN_CHARS || loadingSuggestions}
			<div class="suggest-block">
				<div class="suggest-head">
					<span class="label-inline">Meme tương tự trong archive</span>
					{#if loadingSuggestions}
						<span class="suggest-status">Đang tìm…</span>
					{:else if suggestions.length}
						<span class="suggest-status">Chọn tham chiếu cho kịch bản</span>
					{/if}
				</div>
				{#if suggestionWarning}
					<p class="suggest-warn">{suggestionWarning} — đang dùng tìm theo từ khóa.</p>
				{/if}
				{#if suggestionError}
					<p class="suggest-error">{suggestionError}</p>
				{:else if !loadingSuggestions && suggestions.length === 0}
					<p class="suggest-empty">Chưa có kết quả — thử trend bằng tiếng Anh hoặc từ khóa crypto cụ thể hơn.</p>
				{:else if suggestions.length}
					<div class="suggest-grid">
						{#each suggestions as ref}
							<button
								type="button"
								class="suggest-card"
								class:selected={selectedRefIds.includes(ref.id)}
								onclick={() => toggleReference(ref.id)}
							>
								<img src={imageUrl(ref.id)} alt={ref.description || ref.id} loading="lazy" />
								<div class="suggest-meta">
									<strong>{Math.round(scoreFor(ref) * 100)}%</strong>
									<p>{ref.description?.slice(0, 72) || ref.id}{ref.description && ref.description.length > 72 ? '…' : ''}</p>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{:else if trend.trim().length > 0}
			<p class="suggest-hint">Gõ thêm vài ký tự để xem gợi ý từ archive…</p>
		{/if}

		<label for="hint">Gợi ý thêm (tuỳ chọn)</label>
		<input id="hint" bind:value={hint} placeholder="Tone hài, 2 panel, punchline..." />

		<p class="label-inline char-section-label">Nhân vật — chọn có sẵn hoặc thêm mới</p>

		<form
			class="add-char"
			onsubmit={(e) => {
				e.preventDefault();
				addCharacter();
			}}
		>
			<label for="char-name">Tên</label>
			<input id="char-name" bind:value={newChar.name} placeholder="Tên nhân vật" required />
			<label for="char-desc">Mô tả</label>
			<textarea
				id="char-desc"
				bind:value={newChar.description}
				placeholder="Mô tả ngoại hình, vai trò..."
				required
				rows="2"
			></textarea>
			<label for="char-img">URL ảnh tham chiếu</label>
			<input
				id="char-img"
				bind:value={newChar.referenceImageUrl}
				type="url"
				placeholder="https://..."
				required
			/>
			<button type="submit" class="primary">Thêm nhân vật</button>
		</form>

		<div class="char-grid">
			{#each allCharacters as char}
				<button
					type="button"
					class="char-card"
					class:selected={selectedIds.includes(char.id)}
					onclick={() => toggleCharacter(char.id)}
				>
					{#if char.referenceImageUrl}
						<img
							class="char-thumb"
							src={char.referenceImageUrl}
							alt={char.name}
							loading="lazy"
						/>
					{/if}
					<div class="char-body">
						<strong>{char.name}</strong>
						<p>{char.description.slice(0, 100)}{char.description.length > 100 ? '…' : ''}</p>
					</div>
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
			<h2 class="panel-title">Kịch bản</h2>
			<p class="analysis">{scriptResult.script.conceptAnalysis}</p>
			<pre class="blueprint">{scriptResult.blueprintMarkdown}</pre>
			<details>
				<summary>Image prompt (EN)</summary>
				<p class="prompt-text">{scriptResult.script.imagePrompt}</p>
			</details>
			<button type="button" class="primary" disabled={loadingImage} onclick={generateImage}>
				{loadingImage ? 'Đang tạo ảnh…' : 'Tạo ảnh với tham chiếu + kịch bản'}
			</button>
		</section>
	{/if}

	{#if generatedImageUrl}
		<section class="panel">
			<h2 class="panel-title">Kết quả</h2>
			{#if imageModel}
				<p class="meta">Model: {imageModel}</p>
			{/if}
			<img class="output" src={generatedImageUrl} alt="Generated meme" />
			{#if finalPrompt}
				<details>
					<summary>Prompt cuối</summary>
					<p class="prompt-text">{finalPrompt}</p>
				</details>
			{/if}
			<button type="button" class="primary" onclick={downloadImage}>Tải ảnh</button>
		</section>
	{/if}
</main>

<style>
	:global(body) {
		margin: 0;
		min-width: 320px;
		background:
			linear-gradient(135deg, rgba(14, 14, 14, 0.96), rgba(33, 31, 24, 0.94)),
			repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.03) 0 1px, transparent 1px 72px);
		color: #f8f3e6;
		font-family: Avenir Next, Gill Sans, Trebuchet MS, sans-serif;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.shell {
		width: min(920px, 100%);
		margin: 0 auto;
		padding: 28px;
	}

	.hero {
		border-left: 6px solid #e8ff65;
		padding: 24px 24px 14px 30px;
		margin-bottom: 24px;
	}

	.eyebrow {
		margin: 0 0 10px;
		color: #e8ff65;
		font-size: 0.76rem;
		font-weight: 800;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}

	h1 {
		margin: 0 0 12px;
		font-family: Georgia, Charter, serif;
		font-size: clamp(2.2rem, 6vw, 4rem);
		font-weight: 900;
		line-height: 0.95;
	}

	.lede {
		margin: 0;
		color: #cfc6ad;
		line-height: 1.5;
		max-width: 560px;
	}

	.panel,
	.notice {
		border: 1px solid rgba(248, 243, 230, 0.16);
		border-radius: 8px;
		background: rgba(11, 12, 12, 0.7);
		box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32);
		padding: 20px;
		margin-bottom: 20px;
	}

	.panel-title {
		margin: 0 0 16px;
		font-family: Georgia, serif;
		font-size: 1.35rem;
		color: #e8ff65;
	}

	label,
	.label-inline {
		color: #d7cfba;
		font-size: 0.82rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	label {
		display: block;
		margin: 0 0 8px;
	}

	label:not(:first-child) {
		margin-top: 18px;
	}

	input,
	textarea,
	button {
		font: inherit;
	}

	input,
	textarea {
		width: 100%;
		padding: 10px 14px;
		border: 1px solid rgba(248, 243, 230, 0.24);
		border-radius: 6px;
		background: #f8f3e6;
		color: #151515;
		box-sizing: border-box;
	}

	input {
		min-height: 48px;
	}

	textarea {
		resize: vertical;
	}

	button {
		min-height: 42px;
		border: 0;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 900;
	}

	button:disabled {
		opacity: 0.52;
		cursor: not-allowed;
	}

	.primary {
		background: #e8ff65;
		color: #111;
		padding: 12px 20px;
		margin-top: 16px;
	}

	.notice {
		border-color: rgba(255, 111, 82, 0.42);
		color: #ffc6b8;
		display: flex;
		gap: 12px;
	}

	.suggest-block {
		margin: 14px 0 4px;
		padding: 14px;
		border: 1px solid rgba(248, 243, 230, 0.12);
		border-radius: 8px;
		background: rgba(0, 0, 0, 0.35);
	}

	.suggest-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		margin-bottom: 12px;
	}

	.suggest-status {
		font-size: 0.78rem;
		color: #aaa;
		text-transform: none;
		font-weight: 600;
	}

	.suggest-hint,
	.suggest-empty,
	.suggest-warn,
	.suggest-error {
		margin: 10px 0 0;
		font-size: 0.88rem;
	}

	.suggest-empty,
	.suggest-hint {
		color: #9a9588;
	}

	.suggest-warn {
		color: #e8c765;
	}

	.suggest-error {
		color: #ffb4a8;
	}

	.suggest-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 10px;
	}

	.suggest-card {
		display: flex;
		flex-direction: column;
		text-align: left;
		padding: 0;
		overflow: hidden;
		border: 1px solid rgba(248, 243, 230, 0.14);
		background: rgba(248, 243, 230, 0.05);
		color: #f8f3e6;
	}

	.suggest-card.selected {
		border-color: #e8ff65;
		box-shadow: 0 0 0 2px rgba(232, 255, 101, 0.2);
	}

	.suggest-card img {
		width: 100%;
		height: 120px;
		object-fit: cover;
		background: #1a1914;
	}

	.suggest-meta {
		padding: 10px 12px;
	}

	.suggest-meta strong {
		color: #e8ff65;
		font-size: 0.95rem;
	}

	.suggest-meta p {
		margin: 6px 0 0;
		font-size: 0.78rem;
		line-height: 1.4;
		color: #b8b0a0;
		font-weight: 400;
	}

	.char-section-label {
		display: block;
		margin-top: 18px;
		margin-bottom: 10px;
	}

	.char-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
		gap: 10px;
		margin: 12px 0 0;
	}

	.char-card {
		display: flex;
		flex-direction: column;
		text-align: left;
		padding: 0;
		overflow: hidden;
		border: 1px solid rgba(248, 243, 230, 0.14);
		background: rgba(248, 243, 230, 0.06);
		color: #f8f3e6;
	}

	.char-card.selected {
		border-color: #e8ff65;
		box-shadow: 0 0 0 2px rgba(232, 255, 101, 0.16);
	}

	.char-thumb {
		width: 100%;
		height: 88px;
		object-fit: cover;
		background: #1a1914;
	}

	.char-body {
		padding: 10px 12px;
	}

	.char-card strong {
		display: block;
		color: #e8ff65;
	}

	.char-card p {
		margin: 6px 0 0;
		font-size: 0.82rem;
		color: #ccc;
		line-height: 1.35;
	}

	.add-char {
		display: grid;
		gap: 6px;
		margin: 0 0 14px;
		padding: 14px;
		border: 1px solid rgba(232, 255, 101, 0.35);
		border-radius: 8px;
		background: rgba(232, 255, 101, 0.06);
	}

	.add-char label {
		margin: 8px 0 4px;
		font-size: 0.75rem;
	}

	.add-char .primary {
		margin-top: 10px;
	}

	.analysis {
		line-height: 1.6;
		color: #efe8d5;
		margin: 0 0 14px;
	}

	.blueprint {
		white-space: pre-wrap;
		background: rgba(0, 0, 0, 0.45);
		padding: 14px;
		border-radius: 6px;
		font-size: 0.85rem;
		line-height: 1.5;
		overflow-x: auto;
		margin: 0;
	}

	.prompt-text {
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
		margin-bottom: 8px;
	}

	@media (max-width: 620px) {
		.shell {
			padding: 14px;
		}

		.hero {
			padding: 20px 14px 10px 18px;
		}

		.suggest-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
