<script setup lang="ts">
const route = useRoute()
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`)
</script>
<template>
  <UContainer><UPageHeader :title="post?.title" /></UContainer>
</template>
