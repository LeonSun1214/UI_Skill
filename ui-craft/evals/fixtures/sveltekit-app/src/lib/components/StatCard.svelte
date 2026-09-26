<script lang="ts">
	export let label: string;
	export let value: string | number;
	export let delta: number | undefined = undefined;
</script>

<div class="card">
	<p class="text-sm text-slate-500 dark:text-slate-400">{label}</p>
	<p class="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{value}</p>
	{#if delta !== undefined}<p class="text-xs text-emerald-600">{delta}%</p>{/if}
</div>
