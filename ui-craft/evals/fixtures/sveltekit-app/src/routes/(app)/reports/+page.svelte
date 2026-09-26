<script lang="ts">
	import StatCard from '$lib/components/StatCard.svelte';

	let { data } = $props();
</script>

<h1 class="text-2xl font-semibold">Reports</h1>
<div class="grid grid-cols-3 gap-4">
	{#each data.stats as stat (stat.label)}
		<StatCard label={stat.label} value={stat.value} delta={stat.delta} />
	{/each}
</div>
