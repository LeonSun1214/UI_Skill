<script setup lang="ts">
import AppLayout from '@/layouts/AppLayout.vue'
import StatCard from '@/components/StatCard.vue'
const stats = [{ label: 'Users', value: 12 }, { label: 'Orders', value: 7 }]
</script>
<template>
  <AppLayout>
    <div class="grid gap-4 sm:grid-cols-2">
      <StatCard v-for="s in stats" :key="s.label" :label="s.label" :value="s.value" />
    </div>
  </AppLayout>
</template>
