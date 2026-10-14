<script setup lang="ts">
const menuItems = [{ to: '/', label: 'Datasets' }]
</script>

<template>
  <nav class="app-menu">
    <RouterLink
      v-for="item in menuItems"
      :key="item.to"
      :to="item.to"
      class="app-menu__link"
      active-class="app-menu__link--active"
    >
      {{ item.label }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.app-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 200px;
  padding: 16px 12px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.app-menu__link {
  padding: 8px 12px;
  border-radius: var(--radius);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 14px;
}

.app-menu__link:hover {
  background: var(--color-bg);
  color: var(--color-text);
}

.app-menu__link--active {
  background: var(--color-accent);
  color: #fff;
}
</style>
