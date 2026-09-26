<script setup lang="ts">
const features = [{ title: 'Fast' }, { title: 'Typed' }, { title: 'Themed' }]
</script>
<template>
  <div>
    <UPageHero title="Fixture" description="A Nuxt UI landing page." />
    <UPageSection title="Features">
      <UPageCard v-for="f in features" :key="f.title" :title="f.title" />
    </UPageSection>
  </div>
</template>
