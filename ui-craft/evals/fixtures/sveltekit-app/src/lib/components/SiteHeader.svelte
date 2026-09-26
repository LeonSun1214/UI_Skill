<script lang="ts">
	import { toggleMode } from 'mode-watcher';
	import Button from '$lib/components/Button.svelte';
</script>

<header class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
	<a href="/" class="font-semibold text-slate-900 dark:text-white">Ledger</a>
	<nav class="flex gap-4 text-sm">
		<a href="/pricing">Pricing</a>
		<a href="/reports">Reports</a>
		<a href="/settings">Settings</a>
	</nav>
	<Button variant="ghost" size="sm">Theme</Button>
	<button onclick={toggleMode} aria-label="Toggle theme">◐</button>
</header>
