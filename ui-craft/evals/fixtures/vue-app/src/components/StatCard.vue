<script setup lang="ts">
defineProps<{ label: string; value: number }>()
</script>
<template>
  <div class="card"><p class="text-sm text-gray-600 dark:text-gray-400">{{ label }}</p><p class="text-2xl font-semibold">{{ value }}</p></div>
</template>
