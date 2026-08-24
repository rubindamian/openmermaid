<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { csrfToken, publicApiOrigin } from '$lib/api';
	import { googleLoginUrl } from '$lib/studio';

	let csrf = $state('');
	let error = $state('');

	onMount(async () => {
		try {
			csrf = await csrfToken();
		} catch {
			error = 'The API is not reachable. Start the backend, then refresh.';
		}
	});

	const nextPath = $derived(page.url.searchParams.get('next') || '/');
	const next = $derived(
		typeof window !== 'undefined'
			? `${window.location.origin}${nextPath.startsWith('/') ? nextPath : `/${nextPath}`}`
			: nextPath
	);
	const authError = $derived(page.url.searchParams.get('auth_error'));
	const action = $derived(googleLoginUrl(publicApiOrigin()));
</script>

<div class="flex min-h-screen items-center justify-center px-6 py-12">
	<div class="w-full max-w-sm">
		<div class="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
			<div class="flex justify-center">
				<!-- Swap this span for <img src="..." alt="Open Mermaid" class="h-20 w-20 rounded-2xl object-cover" /> -->
				<span
					class="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-blue-600 text-3xl font-bold text-white"
					aria-hidden="true"
				>
					M
				</span>
			</div>
			<h1 class="mt-5 text-center text-lg font-semibold tracking-tight text-gray-900">Sign in</h1>
			<p class="mt-1 text-center text-sm text-gray-500">
				Use your organization Google account. Anyone can view a published picture; editing needs
				this sign-in.
			</p>

			{#if authError}
				<div
					class="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
				>
					That Google account is not allowed, or sign-in was cancelled.
				</div>
			{/if}
			{#if error}
				<div
					class="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
				>
					{error}
				</div>
			{/if}

			<form method="post" action={action} class="mt-6">
				<input type="hidden" name="csrfmiddlewaretoken" value={csrf} />
				<input type="hidden" name="next" value={next} />
				<button
					type="submit"
					disabled={!csrf}
					class="flex w-full items-center justify-center gap-2.5 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-60"
				>
					<svg class="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
						<path
							fill="#4285F4"
							d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 01-2.4 3.62v3h3.86c2.26-2.08 3.6-5.15 3.6-8.81z"
						/>
						<path
							fill="#34A853"
							d="M12 24c3.24 0 5.96-1.08 7.94-2.91l-3.87-3a7.23 7.23 0 01-10.75-3.8H1.32v3.1A11.99 11.99 0 0012 24z"
						/>
						<path
							fill="#FBBC05"
							d="M5.32 14.29a7.19 7.19 0 010-4.58v-3.1H1.32a12 12 0 000 10.78l4-3.1z"
						/>
						<path
							fill="#EA4335"
							d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42A11.96 11.96 0 0012 0 11.99 11.99 0 001.32 6.61l4 3.1A7.15 7.15 0 0112 4.75z"
						/>
					</svg>
					{csrf ? 'Continue with Google' : 'Connecting…'}
				</button>
			</form>
		</div>
		<p class="mt-4 text-center text-xs text-gray-400">Open Mermaid — internal Mermaid studio</p>
	</div>
</div>
