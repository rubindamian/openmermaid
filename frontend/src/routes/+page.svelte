<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import DiagramThumbnail from '$lib/DiagramThumbnail.svelte';
	import { createDiagram, listDiagrams, type Diagram } from '$lib/api';
	import {
		diagramSummary,
		editorPath,
		formatRelativeTime,
		isApiUnreachable,
		isSignInRequired,
		signInPath
	} from '$lib/studio';

	type View = 'grid' | 'list';
	const VIEW_KEY = 'openmermaid:view';

	let diagrams = $state<Diagram[]>([]);
	let loading = $state(true);
	let creating = $state(false);
	let error = $state('');
	let view = $state<View>('grid');

	function setView(next: View) {
		view = next;
		try {
			localStorage.setItem(VIEW_KEY, next);
		} catch {
			// Private browsing can reject writes; the choice just will not persist.
		}
	}

	onMount(async () => {
		try {
			const stored = localStorage.getItem(VIEW_KEY);
			if (stored === 'grid' || stored === 'list') view = stored;
		} catch {
			// Ignore and keep the default grid.
		}

		const result = await listDiagrams();
		if (isSignInRequired(result.status)) {
			await goto(signInPath('/'));
			return;
		}
		loading = false;
		if (isApiUnreachable(result.status)) {
			error = 'The API is not reachable. Start the backend, then refresh.';
			return;
		}
		if (result.status !== 200) {
			error = 'Could not load diagrams.';
			return;
		}
		diagrams = result.diagrams;
	});

	async function onCreate() {
		creating = true;
		error = '';
		const result = await createDiagram('Untitled');
		creating = false;
		if (isSignInRequired(result.status)) {
			await goto(signInPath('/'));
			return;
		}
		if (isApiUnreachable(result.status)) {
			error = 'The API is not reachable. Start the backend, then refresh.';
			return;
		}
		if (!result.diagram) {
			error = 'Could not create a diagram.';
			return;
		}
		await goto(editorPath(result.diagram.id));
	}
</script>

<!-- Owner-only content stays hidden until the session is known, so a signed-out
     visitor is never shown a diagram list on the way to /signin. -->
{#if loading}
	<div class="flex h-64 items-center justify-center">
		<div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-gray-900"></div>
	</div>
{:else}
	<div class="mx-auto max-w-6xl px-6 py-6">
		<header class="mb-6 flex flex-wrap items-center justify-between gap-3">
			<div>
				<h1 class="text-xl font-semibold tracking-tight">My diagrams</h1>
				<p class="mt-0.5 text-sm text-gray-500">
					Drafts stay private. Save publishes the picture URL.
				</p>
			</div>
			<button
				type="button"
				onclick={onCreate}
				disabled={creating}
				class="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
			>
				<svg
					class="h-4 w-4"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					aria-hidden="true"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
				</svg>
				{creating ? 'Creating…' : 'New diagram'}
			</button>
		</header>

		{#if error}
			<div class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
				{error}
			</div>
		{/if}

		<div class="mb-3 flex items-center justify-between">
			<p class="text-xs font-semibold uppercase tracking-wider text-gray-400">
				Files{diagrams.length ? ` · ${diagrams.length}` : ''}
			</p>
			<div class="flex items-center gap-1 rounded-lg border border-gray-200 bg-white p-0.5">
				<button
					type="button"
					onclick={() => setView('grid')}
					aria-label="Grid view"
					aria-pressed={view === 'grid'}
					class="rounded-md p-1.5 transition {view === 'grid'
						? 'bg-gray-100 text-gray-900'
						: 'text-gray-400 hover:text-gray-600'}"
				>
					<svg
						class="h-4 w-4"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						viewBox="0 0 24 24"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 8.25V6zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25A2.25 2.25 0 0113.5 8.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 018.25 20.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
						/>
					</svg>
				</button>
				<button
					type="button"
					onclick={() => setView('list')}
					aria-label="List view"
					aria-pressed={view === 'list'}
					class="rounded-md p-1.5 transition {view === 'list'
						? 'bg-gray-100 text-gray-900'
						: 'text-gray-400 hover:text-gray-600'}"
				>
					<svg
						class="h-4 w-4"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						viewBox="0 0 24 24"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"
						/>
					</svg>
				</button>
			</div>
		</div>

		{#if diagrams.length === 0}
			<div
				class="rounded-xl border border-dashed border-gray-300 bg-white px-6 py-16 text-center"
			>
				<h2 class="text-sm font-semibold text-gray-900">No diagrams yet</h2>
				<p class="mx-auto mt-1 max-w-sm text-sm text-gray-500">
					Create your first diagram, then Save to publish a picture URL you can paste anywhere.
				</p>
				<button
					type="button"
					onclick={onCreate}
					disabled={creating}
					class="mt-4 inline-flex items-center gap-2 rounded-lg bg-gray-900 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-60"
				>
					New diagram
				</button>
			</div>
		{:else if view === 'grid'}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#each diagrams as diagram (diagram.id)}
					<a
						href={editorPath(diagram.id)}
						class="group overflow-hidden rounded-xl border border-gray-200 bg-white transition hover:border-gray-300 hover:shadow-md"
					>
						<DiagramThumbnail source={diagram.source_draft} />
						<div class="px-4 py-3">
							<h2 class="truncate text-sm font-medium text-gray-900">{diagram.title}</h2>
							<p class="mt-0.5 text-xs text-gray-500">
								Edited {formatRelativeTime(diagram.updated_at)}
							</p>
						</div>
					</a>
				{/each}
			</div>
		{:else}
			<div class="overflow-hidden rounded-xl border border-gray-200 bg-white">
				{#each diagrams as diagram, index (diagram.id)}
					<a
						href={editorPath(diagram.id)}
						class="flex items-center gap-4 px-4 py-3 transition hover:bg-gray-50 {index > 0
							? 'border-t border-gray-100'
							: ''}"
					>
						<DiagramThumbnail source={diagram.source_draft} compact />
						<div class="min-w-0 flex-1">
							<h2 class="truncate text-sm font-medium text-gray-900">{diagram.title}</h2>
							<p class="truncate font-mono text-xs text-gray-400">
								{diagramSummary(diagram.source_draft)}
							</p>
						</div>
						<p class="hidden shrink-0 text-xs text-gray-500 sm:block">
							Edited {formatRelativeTime(diagram.updated_at)}
						</p>
					</a>
				{/each}
			</div>
		{/if}
	</div>
{/if}
