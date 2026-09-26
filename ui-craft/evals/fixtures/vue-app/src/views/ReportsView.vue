<script setup lang="ts">
import AppLayout from '@/layouts/AppLayout.vue'
import StatCard from '@/components/StatCard.vue'
import BaseButton from '@/components/BaseButton.vue'
</script>
<template>
  <AppLayout>
    <StatCard label="Revenue" :value="120" />
    <BaseButton size="sm">Export</BaseButton>
  </AppLayout>
</template>
