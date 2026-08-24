<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { fetchMe, type Me } from '$lib/api';
	import { signInPath } from '$lib/studio';

	let { children } = $props();
	let me = $state<Me | null>(null);
	let loaded = $state(false);
	let sidebarCollapsed = $state(false);

	const SIDEBAR_KEY = 'openmermaid:sidebar-collapsed';

	onMount(async () => {
		try {
			sidebarCollapsed = localStorage.getItem(SIDEBAR_KEY) === 'true';
		} catch {
			// Private browsing can reject storage; keep the sidebar expanded.
		}
		const result = await fetchMe();
		me = result.me;
		loaded = true;
	});

	function toggleSidebar() {
		sidebarCollapsed = !sidebarCollapsed;
		try {
			localStorage.setItem(SIDEBAR_KEY, String(sidebarCollapsed));
		} catch {
			// The current session can still collapse it even if storage is unavailable.
		}
	}

	const next = $derived(page.url.pathname + page.url.search);
	const onDashboard = $derived(page.url.pathname === '/');
	const initial = $derived((me?.email ?? '?').charAt(0).toUpperCase());
	// Sign-in owns the whole viewport: the nav is useless without a session.
	const chromeless = $derived(page.url.pathname === '/signin');
</script>

<svelte:head>
	<title>Open Mermaid</title>
</svelte:head>

{#if chromeless}
	<div class="min-h-screen bg-gray-50 text-gray-900">
		{@render children?.()}
	</div>
{:else}
	<div class="flex min-h-screen bg-gray-50 text-gray-900">
	<aside
		class="relative hidden shrink-0 flex-col border-r border-gray-200 bg-white transition-[width] duration-200 md:flex {sidebarCollapsed
			? 'w-16'
			: 'w-60'}"
	>
		<a
			href="/"
			title="Open Mermaid"
			class="flex items-center gap-2.5 py-5 {sidebarCollapsed ? 'justify-center px-2' : 'px-5'}"
		>
			<span
				class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-teal-400 to-blue-600 text-sm font-bold text-white"
			>
				M
			</span>
			{#if !sidebarCollapsed}
				<span class="whitespace-nowrap text-[15px] font-semibold tracking-tight">Open Mermaid</span>
			{/if}
		</a>

		<button
			type="button"
			onclick={toggleSidebar}
			title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
			aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
			class="absolute -right-3 top-6 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-400 shadow-sm transition hover:text-gray-900"
		>
			<svg
				class="h-3.5 w-3.5 transition-transform {sidebarCollapsed ? 'rotate-180' : ''}"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				viewBox="0 0 24 24"
				aria-hidden="true"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
			</svg>
		</button>

		<nav class={sidebarCollapsed ? 'px-2' : 'px-3'}>
			{#if !sidebarCollapsed}
				<p class="px-2 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
					Your space
				</p>
			{/if}
			<a
				href="/"
				title="My diagrams"
				class="flex items-center rounded-lg py-2 text-sm font-medium transition {sidebarCollapsed
					? 'justify-center px-2'
					: 'gap-2.5 px-2.5'} {onDashboard
					? 'bg-gray-100 text-gray-900'
					: 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}"
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
				{#if !sidebarCollapsed}
					<span class="whitespace-nowrap">My diagrams</span>
				{/if}
			</a>
		</nav>

		<div class="mt-auto border-t border-gray-100 p-3">
			{#if loaded && me}
				<div
					class="flex items-center rounded-lg py-2 {sidebarCollapsed
						? 'justify-center'
						: 'gap-2.5 px-2'}"
					title={me.email}
				>
					<span
						class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white"
					>
						{initial}
					</span>
					{#if !sidebarCollapsed}
						<span class="truncate text-xs text-gray-600">{me.email}</span>
					{/if}
				</div>
			{:else if loaded}
				<a
					href={signInPath(next)}
					title="Sign in"
					class="block rounded-lg bg-gray-900 py-2 text-center text-sm font-medium text-white transition hover:bg-gray-800 {sidebarCollapsed
						? 'px-2'
						: 'px-3'}"
				>
					{sidebarCollapsed ? '→' : 'Sign in'}
				</a>
			{/if}
		</div>
	</aside>

		<main class="min-w-0 flex-1">
			{@render children?.()}
		</main>
	</div>
{/if}
