<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Alert, Button, Heading, Label, Textarea } from 'flowbite-svelte';
	import { getDiagram, patchDraft, saveDiagram, type Diagram } from '$lib/api';
	import { renderMermaidPreview } from '$lib/mermaidPreview';
	import {
		clipboardTextFromSource,
		isForbidden,
		isSignInRequired,
		keepShareOnSaveError,
		shareStateFromSave,
		signInPath,
		tokenAfterSave,
		type ShareState
	} from '$lib/studio';

	let diagram = $state<Diagram | null>(null);
	let source = $state('');
	let previewSvg = $state('');
	let previewError = $state<string | null>(null);
	let message = $state('');
	let error = $state('');
	let saving = $state(false);
	let copied = $state(false);
	let share = $state<ShareState>({ pictureUrl: null, editorUrl: null, publicToken: null });
	let draftTimer: ReturnType<typeof setTimeout> | undefined;
	let saveInFlight = $state(false);

	const diagramId = $derived(page.params.id ?? '');

	async function refreshPreview(value: string) {
		const result = await renderMermaidPreview(value);
		previewSvg = result.svg;
		previewError = result.error;
	}

	onMount(async () => {
		const result = await getDiagram(diagramId);
		if (isSignInRequired(result.status)) {
			await goto(signInPath(`/d/${diagramId}`));
			return;
		}
		if (isForbidden(result.status)) {
			error = 'You cannot edit this diagram. You can still open the public picture if you have the URL.';
			return;
		}
		if (!result.diagram) {
			error = 'Diagram not found.';
			return;
		}
		diagram = result.diagram;
		source = result.diagram.source_draft;
		share = shareStateFromSave(result.diagram);
		await refreshPreview(source);
	});

	function onSourceInput(value: string) {
		source = value;
		error = '';
		void refreshPreview(value);
		if (draftTimer) clearTimeout(draftTimer);
		draftTimer = setTimeout(() => {
			void patchDraft(diagramId, value);
		}, 400);
	}

	async function onSave() {
		if (saveInFlight) return;
		saveInFlight = true;
		saving = true;
		message = '';
		error = '';
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

	async function onCopy() {
		const text = clipboardTextFromSource(source);
		await navigator.clipboard.writeText(text);
		copied = true;
		setTimeout(() => {
			copied = false;
		}, 1500);
	}
</script>

{#if error && !diagram}
	<Alert color="red">{error}</Alert>
{:else if diagram}
	<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
		<Heading tag="h1" class="text-2xl">{diagram.title}</Heading>
		<div class="flex gap-2">
			<Button color="alternative" onclick={onCopy}>Copy source</Button>
			<Button onclick={onSave} disabled={saving}>Save</Button>
		</div>
	</div>

	{#if message}
		<Alert color="green" class="mb-4">{message}</Alert>
	{/if}
	{#if error}
		<Alert color="red" class="mb-4">{error}</Alert>
	{/if}
	{#if copied}
		<p class="mb-2 text-sm text-gray-600">Source copied for a pull request.</p>
	{/if}

	<div class="grid gap-4 md:grid-cols-2">
		<div>
			<Label for="source" class="mb-2">Mermaid source</Label>
			<Textarea
				id="source"
				rows={22}
				class="font-mono text-sm"
				value={source}
				oninput={(event) => onSourceInput((event.currentTarget as HTMLTextAreaElement).value)}
			/>
		</div>
		<div>
			<Label class="mb-2">Live preview</Label>
			<div class="min-h-80 overflow-auto rounded-lg border border-gray-200 bg-white p-4">
				{#if previewError}
					<p class="text-sm text-red-600">{previewError}</p>
				{:else if previewSvg}
					{@html previewSvg}
				{:else}
					<p class="text-sm text-gray-500">Start typing Mermaid on the left.</p>
				{/if}
			</div>
		</div>
	</div>

	{#if share.pictureUrl}
		<div class="mt-6 space-y-2 text-sm">
			<p>
				<strong>Picture URL</strong>
				<a class="text-blue-700 underline" href={share.pictureUrl}>{share.pictureUrl}</a>
			</p>
			<p>
				<strong>Editor link</strong>
				<span>{typeof window !== 'undefined' ? window.location.origin : ''}{share.editorUrl}</span>
			</p>
			<p class="text-gray-500">
				Google Docs stores a copy at insert time. Re-insert the image after a later Save to refresh the Doc.
			</p>
		</div>
	{/if}
{/if}
