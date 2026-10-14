<script setup lang="ts">
const model = defineModel<string>({ default: '' })
</script>

<template>
  <input
    v-model="model"
    type="search"
    class="search-bar"
    placeholder="Search records..."
    aria-label="Search records"
  />
</template>

<style scoped>
.search-bar {
  width: 100%;
  max-width: 360px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
  background: var(--color-surface);
}

.search-bar:focus {
  outline: 2px solid var(--color-accent);
  outline-offset: -1px;
}
</style>
