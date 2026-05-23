<script lang="ts">
	type MemeResult = {
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

	type SearchResponse = {
		query?: string;
		results?: MemeResult[];
		error?: string;
	};

	const examples = [
		'crypto founder explaining tokenomics',
		'market panic with cartoon characters',
		'AI agent trading meme',
		'absurd finance conversation'
	];

	let query = $state(examples[0]);
	let resultCount = $state(8);
	let results = $state<MemeResult[]>([]);
	let selected = $state<MemeResult | null>(null);
	let loading = $state(false);
	let errorMessage = $state('');
	let searchedQuery = $state('');

	const scoreFor = (result: MemeResult) => result.similarity ?? result.score ?? 0;

	const imageUrl = (result: MemeResult) => `/api/image/${encodeURIComponent(result.id)}`;

	const compact = (value: unknown) => {
		if (!value) return 'No metadata';
		if (typeof value === 'string') return value;
		return JSON.stringify(value, null, 2);
	};

	async function searchMemes() {
		const trimmed = query.trim();
		if (!trimmed || loading) return;

		loading = true;
		errorMessage = '';
		searchedQuery = trimmed;

		try {
			const response = await fetch('/api/search', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query: trimmed, k: resultCount })
			});
			const payload = (await response.json()) as SearchResponse;

			if (!response.ok) {
				throw new Error(payload.error || 'Search failed');
			}

			results = payload.results || [];
			selected = results[0] ?? null;
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : String(error);
			results = [];
			selected = null;
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Boldleonidas Meme Search</title>
	<meta
		name="description"
		content="Semantic search interface for the Boldleonidas meme reference archive."
	/>
</svelte:head>

<main class="shell">
	<nav class="site-nav" aria-label="Main">
		<a href="/" class="active">Tìm kiếm</a>
		<a href="/create">Tạo meme</a>
	</nav>

	<section class="hero">
		<div class="hero-copy">
			<p class="eyebrow">Boldleonidas archive</p>
			<h1>Meme reference search for visual recall.</h1>
			<p class="lede">
				Search the indexed image library by scene, punchline, character setup, or visual structure.
			</p>
		</div>

		<form class="search-panel" onsubmit={(event) => { event.preventDefault(); searchMemes(); }}>
			<label for="query">Semantic prompt</label>
			<div class="query-row">
				<input
					id="query"
					bind:value={query}
					placeholder="Describe the meme you want to find..."
					autocomplete="off"
				/>
				<button type="submit" disabled={loading || !query.trim()}>
					{loading ? 'Searching' : 'Search'}
				</button>
			</div>

			<div class="controls">
				<label for="count">Results</label>
				<input id="count" type="range" min="3" max="20" bind:value={resultCount} />
				<strong>{resultCount}</strong>
			</div>

			<div class="examples" aria-label="Example searches">
				{#each examples as example}
					<button type="button" onclick={() => { query = example; searchMemes(); }}>
						{example}
					</button>
				{/each}
			</div>
		</form>
	</section>

	{#if errorMessage}
		<section class="notice" role="alert">
			<strong>Search error</strong>
			<span>{errorMessage}</span>
		</section>
	{/if}

	<section class="workspace" class:empty={!results.length}>
		<div class="results-pane">
			<div class="section-heading">
				<div>
					<p class="eyebrow">Matches</p>
					<h2>{results.length ? searchedQuery : 'Ready when you are'}</h2>
				</div>
				{#if results.length}
					<span>{results.length} results</span>
				{/if}
			</div>

			{#if results.length}
				<div class="result-grid">
					{#each results as result}
						<button
							type="button"
							class:selected={selected?.id === result.id}
							class="result-card"
							onclick={() => (selected = result)}
						>
							<img src={imageUrl(result)} alt={result.description || result.id} loading="lazy" />
							<div>
								<strong>{Math.round(scoreFor(result) * 100)}%</strong>
								<span>{result.id}</span>
							</div>
						</button>
					{/each}
				</div>
			{:else}
				<div class="empty-state">
					<p>Try a scene like “two characters debating crypto risk” or pick one of the presets above.</p>
				</div>
			{/if}
		</div>

		<aside class="detail-pane">
			{#if selected}
				<img class="detail-image" src={imageUrl(selected)} alt={selected.description || selected.id} />
				<div class="detail-copy">
					<div>
						<p class="eyebrow">Selected reference</p>
						<h2>{selected.id}</h2>
					</div>
					<p>{selected.description}</p>
					<dl>
						<div>
							<dt>Similarity</dt>
							<dd>{Math.round(scoreFor(selected) * 1000) / 10}%</dd>
						</div>
						<div>
							<dt>Path</dt>
							<dd>{selected.image_path}</dd>
						</div>
					</dl>
					<div class="metadata">
						<section>
							<h3>Structure</h3>
							<p>{selected.content_structure || 'No structure summary'}</p>
						</section>
						<section>
							<h3>Layout</h3>
							<pre>{compact(selected.layout)}</pre>
						</section>
						<section>
							<h3>Characters</h3>
							<pre>{compact(selected.character_position)}</pre>
						</section>
						<section>
							<h3>Text style</h3>
							<pre>{compact(selected.text_style)}</pre>
						</section>
					</div>
				</div>
			{:else}
				<div class="detail-placeholder">
					<p class="eyebrow">Preview</p>
					<h2>Select a result to inspect its visual recipe.</h2>
				</div>
			{/if}
		</aside>
	</section>
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
		width: min(1480px, 100%);
		margin: 0 auto;
		padding: 28px;
	}

	.site-nav {
		display: flex;
		gap: 10px;
		margin-bottom: 20px;
	}

	.site-nav a {
		color: #f8f3e6;
		text-decoration: none;
		padding: 8px 14px;
		border: 1px solid rgba(248, 243, 230, 0.2);
		border-radius: 6px;
		font-weight: 800;
		font-size: 0.9rem;
	}

	.site-nav a.active {
		background: #e8ff65;
		color: #111;
		border-color: #e8ff65;
	}

	.hero {
		display: grid;
		grid-template-columns: minmax(0, 0.95fr) minmax(380px, 0.78fr);
		gap: 28px;
		align-items: stretch;
		min-height: 360px;
	}

	.hero-copy {
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		border-left: 6px solid #e8ff65;
		padding: 44px 24px 14px 30px;
	}

	.eyebrow {
		margin: 0 0 10px;
		color: #e8ff65;
		font-size: 0.76rem;
		font-weight: 800;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}

	h1,
	h2,
	h3,
	p {
		margin-top: 0;
	}

	h1 {
		max-width: 760px;
		margin-bottom: 18px;
		font-family: Georgia, Charter, serif;
		font-size: clamp(3.2rem, 7vw, 7.6rem);
		font-weight: 900;
		line-height: 0.88;
		letter-spacing: 0;
	}

	.lede {
		max-width: 680px;
		margin-bottom: 0;
		color: #cfc6ad;
		font-size: clamp(1rem, 2vw, 1.35rem);
		line-height: 1.5;
	}

	.search-panel,
	.results-pane,
	.detail-pane,
	.notice {
		border: 1px solid rgba(248, 243, 230, 0.16);
		border-radius: 8px;
		background: rgba(11, 12, 12, 0.7);
		box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32);
	}

	.search-panel {
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 20px;
		padding: 24px;
	}

	label {
		color: #d7cfba;
		font-size: 0.82rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	.query-row {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 128px;
		gap: 10px;
	}

	input,
	button {
		font: inherit;
	}

	input:not([type]) {
		width: 100%;
		min-height: 54px;
		border: 1px solid rgba(248, 243, 230, 0.24);
		border-radius: 6px;
		background: #f8f3e6;
		color: #151515;
		padding: 0 16px;
		font-size: 1rem;
	}

	button {
		min-height: 42px;
		border: 0;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 900;
		transition:
			transform 140ms ease,
			background 140ms ease,
			border-color 140ms ease;
	}

	button:hover:not(:disabled) {
		transform: translateY(-1px);
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.52;
	}

	.query-row button {
		background: #e8ff65;
		color: #111;
	}

	.controls {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) 34px;
		gap: 12px;
		align-items: center;
	}

	input[type='range'] {
		accent-color: #e8ff65;
	}

	.examples {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.examples button {
		min-height: 34px;
		border: 1px solid rgba(248, 243, 230, 0.18);
		background: rgba(248, 243, 230, 0.08);
		color: #f8f3e6;
		padding: 0 12px;
		font-size: 0.82rem;
	}

	.notice {
		display: flex;
		gap: 12px;
		margin-top: 22px;
		padding: 16px 18px;
		border-color: rgba(255, 111, 82, 0.42);
		color: #ffc6b8;
	}

	.workspace {
		display: grid;
		grid-template-columns: minmax(340px, 0.72fr) minmax(0, 1fr);
		gap: 22px;
		margin-top: 24px;
	}

	.workspace.empty {
		grid-template-columns: 1fr minmax(340px, 0.58fr);
	}

	.results-pane,
	.detail-pane {
		min-height: 560px;
		padding: 20px;
	}

	.section-heading {
		display: flex;
		justify-content: space-between;
		gap: 16px;
		align-items: flex-start;
		margin-bottom: 18px;
	}

	.section-heading h2,
	.detail-copy h2,
	.detail-placeholder h2 {
		margin: 0;
		font-family: Georgia, Charter, serif;
		font-size: clamp(1.7rem, 3vw, 3rem);
		line-height: 1;
		overflow-wrap: anywhere;
	}

	.section-heading span {
		flex: 0 0 auto;
		color: #cfc6ad;
		font-weight: 800;
	}

	.result-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 12px;
	}

	.result-card {
		display: grid;
		grid-template-rows: 1fr auto;
		overflow: hidden;
		min-height: 220px;
		border: 1px solid rgba(248, 243, 230, 0.14);
		background: rgba(248, 243, 230, 0.06);
		color: #f8f3e6;
		padding: 0;
		text-align: left;
	}

	.result-card.selected {
		border-color: #e8ff65;
		box-shadow: 0 0 0 2px rgba(232, 255, 101, 0.16);
	}

	.result-card img {
		width: 100%;
		height: 168px;
		object-fit: cover;
		background: #211f18;
	}

	.result-card div {
		display: grid;
		gap: 3px;
		padding: 12px;
	}

	.result-card strong {
		color: #e8ff65;
		font-size: 1.05rem;
	}

	.result-card span {
		color: #cfc6ad;
		font-size: 0.76rem;
		overflow-wrap: anywhere;
	}

	.empty-state,
	.detail-placeholder {
		display: grid;
		min-height: 400px;
		place-items: center;
		color: #cfc6ad;
		text-align: center;
	}

	.empty-state p {
		max-width: 380px;
		margin: 0;
		line-height: 1.6;
	}

	.detail-pane {
		display: grid;
		gap: 18px;
		align-content: start;
	}

	.detail-image {
		width: 100%;
		max-height: 640px;
		border-radius: 6px;
		object-fit: contain;
		background: #0b0c0c;
	}

	.detail-copy {
		display: grid;
		gap: 16px;
	}

	.detail-copy > p {
		margin: 0;
		color: #efe8d5;
		font-size: 1.05rem;
		line-height: 1.65;
	}

	dl {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 10px;
		margin: 0;
	}

	dl div {
		border: 1px solid rgba(248, 243, 230, 0.14);
		border-radius: 6px;
		padding: 12px;
	}

	dt {
		color: #cfc6ad;
		font-size: 0.74rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	dd {
		margin: 4px 0 0;
		overflow-wrap: anywhere;
	}

	.metadata {
		display: grid;
		gap: 10px;
	}

	.metadata section {
		border-top: 1px solid rgba(248, 243, 230, 0.13);
		padding-top: 12px;
	}

	.metadata h3 {
		margin-bottom: 8px;
		color: #e8ff65;
		font-size: 0.84rem;
		text-transform: uppercase;
	}

	.metadata p,
	pre {
		margin: 0;
		color: #d7cfba;
		line-height: 1.55;
		white-space: pre-wrap;
	}

	pre {
		font-family: Menlo, Consolas, monospace;
		font-size: 0.84rem;
	}

	@media (max-width: 980px) {
		.shell {
			padding: 18px;
		}

		.hero,
		.workspace,
		.workspace.empty {
			grid-template-columns: 1fr;
		}

		.hero {
			min-height: auto;
		}
	}

	@media (max-width: 620px) {
		.shell {
			padding: 12px;
		}

		.hero-copy {
			padding: 34px 14px 10px 18px;
		}

		h1 {
			font-size: clamp(2.7rem, 16vw, 4.5rem);
		}

		.search-panel,
		.results-pane,
		.detail-pane {
			padding: 14px;
		}

		.query-row,
		dl {
			grid-template-columns: 1fr;
		}

		.result-grid {
			grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
		}
	}
</style>
