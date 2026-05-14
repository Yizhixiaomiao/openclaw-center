<template>
  <el-container style="height: 100vh">
    <el-aside width="280px" class="app-sidebar">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header class="app-topbar">
        <Header />
      </el-header>
      <el-main class="app-main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>
