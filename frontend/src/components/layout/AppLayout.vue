<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #304156">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header style="background: #fff; border-bottom: 1px solid #e6e6e6; padding: 0 20px; display: flex; align-items: center; justify-content: space-between;">
        <Header />
      </el-header>
      <el-main style="background: #f0f2f5; padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>
