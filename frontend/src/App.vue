 <script setup lang="ts">
import AppHeader from './components/AppHeader.vue'
import AppMenu from './components/AppMenu.vue'
</script>

<template>
  <v-app>
    <div class="app-layout">
      <AppHeader />
      <div class="app-body">
        <AppMenu />
        <main class="app-content">
          <RouterView />
        </main>
      </div>
    </div>
  </v-app>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-body {
  display: flex;
  flex: 1;
}

.app-content {
  flex: 1;
  padding: 24px;
  max-width: 1100px;
}
</style>
