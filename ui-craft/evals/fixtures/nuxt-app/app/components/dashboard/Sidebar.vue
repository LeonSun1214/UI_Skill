<script setup lang="ts">
const props = defineProps({ collapsed: { type: Boolean, default: false }, items: Array })
</script>
<template>
  <aside class="w-64 border-r border-default"><UNavigationMenu orientation="vertical" :items="items" /></aside>
</template>
