<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getDiagram, patchDraft, patchTitle, saveDiagram, type Diagram } from '$lib/api';
	import {
		DEFAULT_SPLIT_PERCENT,
		MAX_SPLIT_PERCENT,
		MIN_SPLIT_PERCENT,
		splitPercentFromKey,
		splitPercentFromPointer
	} from '$lib/editorLayout';
	import {
		DRAFT_DEBOUNCE_MS,
		draftErrorMessage,
		draftIndicator,
		type DraftStatus
	} from '$lib/draftStatus';
	import MermaidEditor from '$lib/MermaidEditor.svelte';
	import { renderMermaidPreview } from '$lib/mermaidPreview';
	import {
		clipboardTextFromSource,
		formatRelativeTime,
		isApiUnreachable,
		isForbidden,
		isSignInRequired,
		keepShareOnSaveError,
		normalizeTitle,
		shareStateFromSave,
		signInPath,
		tokenAfterSave,
		type ShareState
	} from '$lib/studio';

	type WorkspaceMode = 'editor' | 'split' | 'preview';

	let diagram = $state<Diagram | null>(null);
	let source = $state('');
	let previewSvg = $state('');
	let previewError = $state<string | null>(null);
	let message = $state('');
	let error = $state('');
	let saving = $state(false);
	let share = $state<ShareState>({ pictureUrl: null, editorUrl: null, publicToken: null });
	let draftTimer: ReturnType<typeof setTimeout> | undefined;
	// Plain (non-reactive) so the unload listeners can read it without
	// re-subscribing every keystroke.
	let pendingDraft: string | null = null;
	let draftStatus = $state<DraftStatus>('saved');
	let draftDetail = $state('');
	let saveInFlight = $state(false);
	let urlCopied = $state('');
	let workspaceMode = $state<WorkspaceMode>('split');
	let title = $state('');
	let committedTitle = $state('');
	let titleTimer: ReturnType<typeof setTimeout> | undefined;
	let titleInput = $state<HTMLInputElement | null>(null);
	let splitWidth = $state(DEFAULT_SPLIT_PERCENT);
	let workspaceElement = $state<HTMLDivElement | null>(null);

	const WORKSPACE_MODE_KEY = 'openmermaid:workspace-mode';
	const SPLIT_WIDTH_KEY = 'openmermaid:split-width';

	const diagramId = $derived(page.params.id ?? '');
	const editorUrl = $derived(
		typeof window !== 'undefined' && share.editorUrl
			? `${window.location.origin}${share.editorUrl}`
			: ''
	);

	async function refreshPreview(value: string) {
		const result = await renderMermaidPreview(value);
		previewSvg = result.svg;
		previewError = result.error;
	}

	onMount(async () => {
		try {
			const stored = localStorage.getItem(WORKSPACE_MODE_KEY);
			if (stored === 'editor' || stored === 'split' || stored === 'preview') {
				workspaceMode = stored;
			}
			const storedWidth = Number(localStorage.getItem(SPLIT_WIDTH_KEY));
			if (storedWidth >= MIN_SPLIT_PERCENT && storedWidth <= MAX_SPLIT_PERCENT) {
				splitWidth = storedWidth;
			}
		} catch {
			// Private browsing can reject storage; keep the split default.
		}

		const result = await getDiagram(diagramId);
		if (isSignInRequired(result.status)) {
			await goto(signInPath(`/d/${diagramId}`));
			return;
		}
		if (isForbidden(result.status)) {
			error = 'You cannot edit this diagram. You can still open the public picture if you have the URL.';
			return;
		}
		if (isApiUnreachable(result.status)) {
			error = 'The API is not reachable. Start the backend, then refresh.';
			return;
		}
		if (!result.diagram) {
			error = 'Diagram not found.';
			return;
		}
		diagram = result.diagram;
		source = result.diagram.source_draft;
		title = result.diagram.title;
		committedTitle = result.diagram.title;
		share = shareStateFromSave(result.diagram);
		await refreshPreview(source);
	});

	// Closing the tab or leaving the page mid-debounce would otherwise drop the
	// last keystrokes; `keepalive` lets the write outlive the document.
	$effect(() => {
		// Captured because the teardown path runs after the route state is gone.
		const id = diagramId;
		const flushPending = () => {
			if (pendingDraft !== null) void flushDraft({ keepalive: true, id });
		};
		const onVisibilityChange = () => {
			if (document.visibilityState === 'hidden') flushPending();
		};
		window.addEventListener('pagehide', flushPending);
		document.addEventListener('visibilitychange', onVisibilityChange);
		return () => {
			window.removeEventListener('pagehide', flushPending);
			document.removeEventListener('visibilitychange', onVisibilityChange);
			// Client-side navigation destroys the page without firing `pagehide`.
			flushPending();
		};
	});

	const draftLabel = $derived(draftIndicator(draftStatus, draftDetail));

	// Renames get their own PATCH so a title edit never races the draft debounce.
	function commitTitle() {
		if (titleTimer) clearTimeout(titleTimer);
		const next = normalizeTitle(title);
		title = next;
		if (next === committedTitle) return;
		committedTitle = next;
		void patchTitle(diagramId, next).then((result) => {
			if (result.diagram) diagram = result.diagram;
		});
	}

	function onTitleInput(value: string) {
		title = value;
		if (titleTimer) clearTimeout(titleTimer);
		titleTimer = setTimeout(commitTitle, 600);
	}

	function onTitleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			titleInput?.blur();
			return;
		}
		if (event.key === 'Escape') {
			event.preventDefault();
			title = committedTitle;
			titleInput?.blur();
		}
	}

	function setWorkspaceMode(mode: WorkspaceMode) {
		workspaceMode = mode;
		try {
			localStorage.setItem(WORKSPACE_MODE_KEY, mode);
		} catch {
			// The current session can still switch modes without persistence.
		}
	}

	function persistSplitWidth() {
		try {
			localStorage.setItem(SPLIT_WIDTH_KEY, String(splitWidth));
		} catch {
			// Resizing still works for this session if storage is unavailable.
		}
	}

	function resizeSplitFromPointer(event: PointerEvent) {
		if (!workspaceElement) return;
		const bounds = workspaceElement.getBoundingClientRect();
		splitWidth = splitPercentFromPointer(event.clientX, bounds.left, bounds.width);
	}

	function startSplitResize(event: PointerEvent) {
		event.preventDefault();
		const handle = event.currentTarget as HTMLInputElement;
		handle.focus();
		handle.setPointerCapture(event.pointerId);
		resizeSplitFromPointer(event);
	}

	function finishSplitResize(event: PointerEvent) {
		const handle = event.currentTarget as HTMLElement;
		if (handle.hasPointerCapture(event.pointerId)) {
			handle.releasePointerCapture(event.pointerId);
		}
		persistSplitWidth();
	}

	function resizeSplitFromKeyboard(event: KeyboardEvent) {
		const next = splitPercentFromKey(splitWidth, event.key);
		if (next === null) return;
		event.preventDefault();
		splitWidth = next;
		persistSplitWidth();
	}

	function onSourceInput(value: string) {
		source = value;
		error = '';
		void refreshPreview(value);
		pendingDraft = value;
		draftStatus = 'pending';
		if (draftTimer) clearTimeout(draftTimer);
		draftTimer = setTimeout(() => void flushDraft(), DRAFT_DEBOUNCE_MS);
	}

	// Writes the pending draft immediately and reports whether the server has it.
	async function flushDraft(
		options: { keepalive?: boolean; id?: string } = {}
	): Promise<boolean> {
		if (draftTimer) {
			clearTimeout(draftTimer);
			draftTimer = undefined;
		}
		const inFlight = pendingDraft;
		if (inFlight === null) return draftStatus !== 'error';
		pendingDraft = null;
		draftStatus = 'saving';

		const result = await patchDraft(options.id ?? diagramId, inFlight, {
			keepalive: options.keepalive
		});
		if (result.diagram) {
			diagram = result.diagram;
			// A keystroke can land mid-flight; leave that newer draft pending.
			if (pendingDraft === null) {
				draftStatus = 'saved';
				draftDetail = '';
			}
			return true;
		}

		draftStatus = 'error';
		draftDetail = draftErrorMessage(result.status);
		if (pendingDraft === null) pendingDraft = inFlight;
		return false;
	}

	async function onSave() {
		if (saveInFlight) return;
		saveInFlight = true;
		saving = true;
		message = '';
		error = '';

		// The server publishes the stored draft, so a pending edit has to land
		// first or Save would render the previous version of the diagram.
		const flushed = await flushDraft();
		if (!flushed) {
			saving = false;
			saveInFlight = false;
			error = draftDetail || 'Your latest edit was not saved, so nothing was published.';
			return;
		}

		const previous = share;
		const result = await saveDiagram(diagramId);
		saving = false;
		saveInFlight = false;
		if (isSignInRequired(result.status)) {
			error = 'Your session expired. Sign in again to publish. The public picture was not changed.';
			share = keepShareOnSaveError(previous, false);
			return;
		}
		if (!result.diagram) {
			error = result.detail || 'Save failed.';
			share = keepShareOnSaveError(previous, false);
			return;
		}
		diagram = result.diagram;
		share = keepShareOnSaveError(previous, true, shareStateFromSave(result.diagram));
		share.publicToken = tokenAfterSave(previous.publicToken, result.diagram.public_token);
		message = 'Published. The picture URL now shows this Save.';
	}

	async function copyUrl(label: string, value: string) {
		if (!value) return;
		await navigator.clipboard.writeText(value);
		urlCopied = label;
		setTimeout(() => {
			urlCopied = '';
		}, 1500);
	}
</script>

{#if error && !diagram}
	<div class="mx-auto max-w-2xl px-6 py-16">
		<div class="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
			{error}
		</div>
		<a href="/" class="mt-4 inline-block text-sm text-gray-500 underline hover:text-gray-900">
			Back to my diagrams
		</a>
	</div>
{:else if diagram}
	<div class="flex h-screen flex-col">
		<header
			class="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-gray-200 bg-white px-6 py-3"
		>
			<div class="min-w-0">
				<div class="flex items-center gap-2 text-sm">
					<a href="/" class="text-gray-400 transition hover:text-gray-900">My diagrams</a>
					<span class="text-gray-300">/</span>
					<h1 class="min-w-0">
						<!-- The invisible sizer keeps the input exactly as wide as its text, so a
						     click lands the caret on the title rather than inside a wide empty box. -->
						<span class="inline-grid max-w-full align-bottom">
							<span
								class="invisible col-start-1 row-start-1 whitespace-pre px-1.5 py-0.5 font-medium"
								aria-hidden="true">{title || ' '}</span
							>
							<input
								bind:this={titleInput}
								value={title}
								oninput={(event) => onTitleInput((event.currentTarget as HTMLInputElement).value)}
								onblur={commitTitle}
								onkeydown={onTitleKeydown}
								aria-label="Diagram title"
								spellcheck="false"
								maxlength="255"
								class="col-start-1 row-start-1 min-w-0 rounded border border-transparent bg-transparent px-1.5 py-0.5 font-medium text-gray-900 outline-none transition hover:border-gray-200 hover:bg-gray-50 focus:border-gray-300 focus:bg-white focus:ring-2 focus:ring-gray-900/10"
							/>
						</span>
					</h1>
				</div>
				<p class="mt-0.5 text-xs text-gray-400">
					{diagram.saved_at
						? `Published ${formatRelativeTime(diagram.saved_at)}`
						: 'Draft — not published yet'}
				</p>
			</div>
			<div class="flex items-center gap-2">
				<div
					class="hidden items-center rounded-lg border border-gray-200 bg-gray-100 p-0.5 sm:flex"
					aria-label="Workspace view"
				>
					<button
						type="button"
						onclick={() => setWorkspaceMode('editor')}
						aria-label="Editor only"
						aria-pressed={workspaceMode === 'editor'}
						title="Editor only"
						class="rounded-md px-2.5 py-1 text-xs font-medium transition {workspaceMode ===
						'editor'
							? 'bg-gray-900 text-white shadow-sm'
							: 'text-gray-500 hover:text-gray-900'}"
					>
						Editor
					</button>
					<button
						type="button"
						onclick={() => setWorkspaceMode('split')}
						aria-label="Split editor and preview"
						aria-pressed={workspaceMode === 'split'}
						title="Split editor and preview"
						class="rounded-md px-2.5 py-1 text-xs font-medium transition {workspaceMode ===
						'split'
							? 'bg-gray-900 text-white shadow-sm'
							: 'text-gray-500 hover:text-gray-900'}"
					>
						Split
					</button>
					<button
						type="button"
						onclick={() => setWorkspaceMode('preview')}
						aria-label="Preview only"
						aria-pressed={workspaceMode === 'preview'}
						title="Preview only"
						class="rounded-md px-2.5 py-1 text-xs font-medium transition {workspaceMode ===
						'preview'
							? 'bg-gray-900 text-white shadow-sm'
							: 'text-gray-500 hover:text-gray-900'}"
					>
						Preview
					</button>
				</div>
				<select
					aria-label="Workspace view"
					value={workspaceMode}
					onchange={(event) =>
						setWorkspaceMode((event.currentTarget as HTMLSelectElement).value as WorkspaceMode)}
					class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700 sm:hidden"
				>
					<option value="editor">Editor</option>
					<option value="split">Split</option>
					<option value="preview">Preview</option>
				</select>
				<div class="flex items-center gap-1" aria-label="Copy links">
					<button
						type="button"
						onclick={() => copyUrl('picture', share.pictureUrl ?? '')}
						disabled={!share.pictureUrl}
						title={share.pictureUrl
							? urlCopied === 'picture'
								? 'Copied picture URL'
								: 'Copy picture URL. Google Docs stores a snapshot; re-insert after a later Save to refresh a Doc.'
							: 'Save to copy the picture URL'}
						aria-label={share.pictureUrl ? 'Copy picture URL' : 'Picture URL unavailable until Save'}
						class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-50 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
					>
						{#if urlCopied === 'picture'}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						{:else}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true">
								<rect x="4" y="5" width="16" height="14" rx="2" />
								<circle cx="9" cy="10" r="1.4" fill="currentColor" stroke="none" />
								<path stroke-linecap="round" stroke-linejoin="round" d="M7 16l3.5-3.5 2.5 2.5L17 11l3 3" />
							</svg>
						{/if}
					</button>
					<button
						type="button"
						onclick={() => copyUrl('editor', editorUrl)}
						disabled={!editorUrl}
						title={urlCopied === 'editor' ? 'Copied editor URL' : 'Copy editor URL'}
						aria-label="Copy editor URL"
						class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-50 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
					>
						{#if urlCopied === 'editor'}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						{:else}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M13.5 6H16a4 4 0 010 8h-2.5M10.5 18H8a4 4 0 010-8h2.5M9 12h6"
								/>
							</svg>
						{/if}
					</button>
					<button
						type="button"
						onclick={() => copyUrl('source', clipboardTextFromSource(source))}
						disabled={!source.trim()}
						title={urlCopied === 'source' ? 'Copied source' : 'Copy source'}
						aria-label="Copy source"
						class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition hover:bg-gray-50 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
					>
						{#if urlCopied === 'source'}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						{:else}
							<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M8 7.5 4.5 12 8 16.5M16 7.5 19.5 12 16 16.5"
								/>
							</svg>
						{/if}
					</button>
					{#if urlCopied}
						<span class="hidden text-xs text-gray-500 sm:inline" aria-live="polite">
							{urlCopied === 'picture'
								? 'Copied picture URL'
								: urlCopied === 'editor'
									? 'Copied editor URL'
									: 'Copied source'}
						</span>
					{/if}
				</div>
				<button
					type="button"
					onclick={onSave}
					disabled={saving}
					class="rounded-lg bg-gray-900 px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
				>
					{saving ? 'Saving…' : 'Save'}
				</button>
			</div>
		</header>

		{#if message || error}
			<div class="shrink-0 border-b border-gray-200 bg-white px-6 py-2">
				{#if message}
					<p class="text-sm text-emerald-700">{message}</p>
				{/if}
				{#if error}
					<p class="text-sm text-red-600">{error}</p>
				{/if}
			</div>
		{/if}

		<div
			bind:this={workspaceElement}
			class="workspace grid min-h-0 flex-1 grid-cols-1 {workspaceMode === 'split'
				? 'workspace-split'
				: ''}"
			style={`--editor-width: ${splitWidth}%`}
		>
			{#if workspaceMode !== 'preview'}
			<section
				class="flex min-h-0 flex-col border-gray-200"
			>
				<div
					class="flex shrink-0 items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2"
				>
					<span class="text-xs font-semibold uppercase tracking-wider text-gray-400">Source</span>
					<span
						class="text-xs {draftLabel.tone === 'error' ? 'text-red-600' : 'text-gray-400'}"
						aria-live="polite"
						data-testid="draft-status"
					>
						{draftLabel.text}
					</span>
				</div>
				<div class="min-h-0 flex-1">
					<MermaidEditor value={source} onchange={onSourceInput} />
				</div>
			</section>
			{/if}

			{#if workspaceMode === 'split'}
				<input
					type="range"
					min={MIN_SPLIT_PERCENT}
					max={MAX_SPLIT_PERCENT}
					step="0.1"
					value={splitWidth}
					aria-label="Resize editor and preview"
					title="Drag to resize editor and preview"
					class="split-handle hidden cursor-col-resize touch-none bg-gray-100 outline-none transition-colors hover:bg-blue-100 focus:bg-blue-100 md:block"
					onpointerdown={startSplitResize}
					onpointermove={(event) => {
						if ((event.currentTarget as HTMLElement).hasPointerCapture(event.pointerId)) {
							resizeSplitFromPointer(event);
						}
					}}
					onpointerup={finishSplitResize}
					onpointercancel={finishSplitResize}
					onkeydown={resizeSplitFromKeyboard}
				/>
			{/if}

			{#if workspaceMode !== 'editor'}
			<section class="flex min-h-0 flex-col">
				<div
					class="flex shrink-0 items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2"
				>
					<span class="text-xs font-semibold uppercase tracking-wider text-gray-400">Preview</span>
					{#if previewError}
						<span class="text-xs font-medium text-amber-600">Invalid syntax</span>
					{/if}
				</div>
				<div
					class="preview min-h-0 flex-1 overflow-auto bg-white p-6 {workspaceMode === 'preview'
						? 'preview-full'
						: ''}"
				>
					{#if previewError}
						<pre
							class="whitespace-pre-wrap rounded-lg bg-amber-50 p-3 font-mono text-xs text-amber-800">{previewError}</pre>
					{:else if previewSvg}
						{@html previewSvg}
					{:else}
						<p class="text-sm text-gray-400">Start typing Mermaid on the left.</p>
					{/if}
				</div>
			</section>
			{/if}
		</div>
	</div>
{/if}

<style>
	@media (min-width: 768px) {
		.workspace-split {
			grid-template-columns: minmax(0, var(--editor-width)) 6px minmax(0, 1fr);
		}
	}

	.split-handle {
		width: 6px;
		height: 100%;
		appearance: none;
	}

	.split-handle::-webkit-slider-runnable-track {
		width: 6px;
		height: 100%;
		background: transparent;
	}

	.split-handle::-webkit-slider-thumb {
		width: 2px;
		height: 32px;
		margin-left: 2px;
		border: 0;
		border-radius: 9999px;
		appearance: none;
		background: #d1d5db;
	}

	.split-handle:hover::-webkit-slider-thumb,
	.split-handle:focus::-webkit-slider-thumb {
		background: #3b82f6;
	}

	.split-handle::-moz-range-track {
		width: 6px;
		height: 100%;
		background: transparent;
	}

	.split-handle::-moz-range-thumb {
		width: 2px;
		height: 32px;
		border: 0;
		border-radius: 9999px;
		background: #d1d5db;
	}

	.split-handle:hover::-moz-range-thumb,
	.split-handle:focus::-moz-range-thumb {
		background: #3b82f6;
	}

	.preview :global(svg) {
		max-width: 100%;
		height: auto;
	}

	.preview-full :global(svg) {
		display: block;
		width: 100%;
		height: 100%;
		max-height: 100%;
		margin: auto;
	}
</style>
