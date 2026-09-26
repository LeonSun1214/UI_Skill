<script setup lang="ts">
import AppLayout from '@/layouts/AppLayout.vue'
import BaseButton from '@/components/BaseButton.vue'
</script>
<template>
  <AppLayout>
    <form class="card space-y-4">
      <label class="block">Name <input class="mt-1 w-full rounded-md border border-gray-400 px-3 py-2" /></label>
      <label class="block">Email <input type="email" class="mt-1 w-full rounded-md border border-gray-400 px-3 py-2" /></label>
      <BaseButton variant="primary">Save</BaseButton>
    </form>
  </AppLayout>
</template>
