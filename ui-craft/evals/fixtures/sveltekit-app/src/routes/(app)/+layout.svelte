<script lang="ts">
	let { children, data } = $props();
</script>

<div class="grid grid-cols-[14rem_1fr] gap-8">
	<aside class="text-sm">Signed in as {data.user?.name}</aside>
	<section>{@render children()}</section>
</div>
