<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { Navbar, NavBrand, NavLi, NavUl, Button } from 'flowbite-svelte';
	import { fetchMe, type Me } from '$lib/api';
	import { signInPath } from '$lib/studio';

	let { children } = $props();
	let me = $state<Me | null>(null);
	let loaded = $state(false);

	onMount(async () => {
		const result = await fetchMe();
		me = result.me;
		loaded = true;
	});

	const next = $derived(page.url.pathname + page.url.search);
</script>

<svelte:head>
	<title>Open Mermaid</title>
</svelte:head>

<Navbar class="border-b border-gray-200 bg-white">
	<NavBrand href="/">
		<span class="self-center whitespace-nowrap text-xl font-semibold text-gray-900">Open Mermaid</span>
	</NavBrand>
	<NavUl>
		{#if loaded && me}
			<NavLi>
				<span class="text-sm text-gray-600">{me.email}</span>
			</NavLi>
		{:else if loaded}
			<NavLi>
				<Button href={signInPath(next)} size="sm">Sign in with Google</Button>
			</NavLi>
		{/if}
	</NavUl>
</Navbar>

<main class="mx-auto max-w-6xl px-4 py-6">
	{@render children?.()}
</main>
