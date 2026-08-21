<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { Alert, Button, Heading } from 'flowbite-svelte';
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
		typeof window !== 'undefined' ? `${window.location.origin}${nextPath.startsWith('/') ? nextPath : `/${nextPath}`}` : nextPath
	);
	const authError = $derived(page.url.searchParams.get('auth_error'));
	const action = $derived(googleLoginUrl(publicApiOrigin()));
</script>

<Heading tag="h1" class="mb-2 text-2xl">Sign in</Heading>
<p class="mb-6 text-gray-600">
	Use your organization Google account. The picture URL stays public; editing requires this sign-in.
</p>

{#if authError}
	<Alert color="red" class="mb-4">That Google account is not allowed, or sign-in was cancelled.</Alert>
{/if}
{#if error}
	<Alert color="yellow" class="mb-4">{error}</Alert>
{/if}

<form method="post" action={action}>
	<input type="hidden" name="csrfmiddlewaretoken" value={csrf} />
	<input type="hidden" name="next" value={next} />
	<Button type="submit" disabled={!csrf}>Continue with Google</Button>
</form>
