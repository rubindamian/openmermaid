<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Button, Card, Heading, Spinner } from 'flowbite-svelte';
	import { createDiagram, listDiagrams, type Diagram } from '$lib/api';
	import { editorPath, isSignInRequired, signInPath } from '$lib/studio';

	let diagrams = $state<Diagram[]>([]);
	let loading = $state(true);
	let creating = $state(false);
	let error = $state('');

	onMount(async () => {
		const result = await listDiagrams();
		if (isSignInRequired(result.status)) {
			await goto(signInPath('/'));
			return;
		}
		if (result.status !== 200) {
			error = 'Could not load diagrams.';
		}
		diagrams = result.diagrams;
		loading = false;
	});

	async function onCreate() {
		creating = true;
		const result = await createDiagram('Untitled');
		creating = false;
		if (isSignInRequired(result.status)) {
			await goto(signInPath('/'));
			return;
		}
		if (!result.diagram) {
			error = 'Could not create a diagram.';
			return;
		}
		await goto(editorPath(result.diagram.id));
	}
</script>

<Heading tag="h1" class="mb-2 text-2xl">My diagrams</Heading>
<p class="mb-6 text-gray-600">Open a diagram you own, or start a new one. Save publishes the picture URL.</p>

{#if error}
	<p class="mb-4 text-sm text-red-600">{error}</p>
{/if}

<Button class="mb-6" onclick={onCreate} disabled={creating}>New diagram</Button>

{#if loading}
	<Spinner />
{:else if diagrams.length === 0}
	<p class="text-gray-600">No diagrams yet.</p>
{:else}
	<div class="grid gap-4 md:grid-cols-2">
		{#each diagrams as diagram (diagram.id)}
			<Card href={editorPath(diagram.id)}>
				<h2 class="text-lg font-semibold text-gray-900">{diagram.title}</h2>
				<p class="mt-2 line-clamp-3 font-mono text-xs text-gray-500">
					{diagram.source_draft || 'Empty draft'}
				</p>
			</Card>
		{/each}
	</div>
{/if}
