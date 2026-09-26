<template>
  <v-app>
    <v-app-bar title="Harbor">
      <v-btn icon="mdi-theme-light-dark" aria-label="Toggle theme" @click="toggle" />
    </v-app-bar>
    <v-main><router-view /></v-main>
  </v-app>
</template>

<script setup lang="ts">
import { useTheme } from 'vuetify';
const theme = useTheme();
theme.global.name.value = localStorage.getItem('app-theme') || 'light';
function toggle() {
  theme.global.name.value = theme.global.name.value === 'dark' ? 'light' : 'dark';
  localStorage.setItem('app-theme', theme.global.name.value);
}
</script>
