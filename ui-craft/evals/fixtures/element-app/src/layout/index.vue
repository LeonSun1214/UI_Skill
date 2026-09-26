<template>
  <el-container>
    <el-aside width="220px"><el-menu router><el-menu-item index="/dashboard">仪表盘</el-menu-item></el-menu></el-aside>
    <el-container>
      <el-header><el-button text @click="settings.toggleTheme()">切换主题</el-button></el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/store/settings';
const settings = useSettingsStore();
</script>
