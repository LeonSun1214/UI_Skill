<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from 'mode-watcher';
	import SiteHeader from '$lib/components/SiteHeader.svelte';

	let { children } = $props();
</script>

<ModeWatcher />
<SiteHeader />
<main class="mx-auto max-w-5xl px-6 py-10">{@render children()}</main>
