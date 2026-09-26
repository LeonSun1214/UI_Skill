<script setup lang="ts">
import { Moon } from 'lucide-vue-next'
</script>
<template>
  <div class="min-h-screen bg-white dark:bg-gray-950">
    <header class="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-800">
      <span class="font-semibold">Fixture</span><Moon class="size-5" />
    </header>
    <main class="mx-auto max-w-5xl p-6"><slot /></main>
  </div>
</template>
