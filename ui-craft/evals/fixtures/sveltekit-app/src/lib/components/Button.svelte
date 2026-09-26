<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'primary' | 'ghost';
		size?: 'sm' | 'md';
		href?: string;
		children: Snippet;
	}

	let { variant = 'primary', size = 'md', href, children }: Props = $props();
</script>

{#if href}
	<a {href} class="btn btn-{variant} btn-{size}">{@render children()}</a>
{:else}
	<button class="btn btn-{variant} btn-{size}">{@render children()}</button>
{/if}
