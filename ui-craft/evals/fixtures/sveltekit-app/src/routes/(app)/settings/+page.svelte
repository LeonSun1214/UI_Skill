<script lang="ts">
	import Button from '$lib/components/Button.svelte';

	let { data, form } = $props();
</script>

<h1 class="text-2xl font-semibold">Settings</h1>
<form method="POST" class="card space-y-4">
	<label class="block">Name <input name="name" value={data.user?.name} /></label>
	<label class="block">Email <input name="email" type="email" /></label>
	{#if form?.error}<p role="alert">{form.error}</p>{/if}
	<Button>Save</Button>
</form>
