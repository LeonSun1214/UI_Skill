<script setup lang="ts">
definePageMeta({ layout: 'dashboard', middleware: 'auth' })
const state = reactive({ name: '', email: '' })
</script>
<template>
  <UForm :state="state" class="space-y-4">
    <UFormField label="Name"><UInput v-model="state.name" /></UFormField>
    <UFormField label="Email"><UInput v-model="state.email" type="email" /></UFormField>
    <UButton type="submit">Save</UButton>
  </UForm>
</template>
