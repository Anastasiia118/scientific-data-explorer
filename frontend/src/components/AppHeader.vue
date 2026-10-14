<script setup lang="ts">
const title = 'Scientific Data Explorer'
</script>

<template>
  <header class="app-header">
    <span class="app-header__title">{{ title }}</span>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-header__title {
  font-size: 16px;
  font-weight: 600;
}
</style>
