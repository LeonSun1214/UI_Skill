<script setup lang="ts">
defineProps({ variant: { type: String, default: 'primary' }, size: String })
</script>
<template>
  <button class="rounded-md bg-emerald-700 px-4 py-2 text-white hover:bg-emerald-800"><slot /></button>
</template>
