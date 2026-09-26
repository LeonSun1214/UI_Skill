<template>
  <div class="login">
    <el-form :model="form" label-position="top">
      <h1>登录</h1>
      <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
      <el-button type="primary" native-type="submit">登录</el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
const form = reactive({ username: '', password: '' });
</script>
