<script setup lang="ts">
defineProps<{ title?: string; sticky?: boolean }>()
</script>
<template>
  <UHeader :title="title"><template #right><UColorModeButton /></template></UHeader>
</template>
