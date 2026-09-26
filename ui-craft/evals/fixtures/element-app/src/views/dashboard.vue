<template>
  <el-row :gutter="16">
    <el-col :span="8"><el-card shadow="hover">待发货 42</el-card></el-col>
    <el-col :span="8"><el-card shadow="hover">延迟 3</el-card></el-col>
    <el-col :span="8"><el-card shadow="hover">今日已发 17</el-card></el-col>
  </el-row>
  <el-table :data="[]"><el-table-column prop="name" label="订单" /></el-table>
</template>
