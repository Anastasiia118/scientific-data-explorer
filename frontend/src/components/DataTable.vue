<script setup lang="ts">
import type { SampleRecord } from '../types/dataset'

defineProps<{
  records: SampleRecord[]
  loading?: boolean
}>()

// The CSV schema is fixed, so the columns are too.
const columns: { key: keyof SampleRecord; label: string }[] = [
  { key: 'sample_id', label: 'Sample ID' },
  { key: 'category', label: 'Category' },
  { key: 'value', label: 'Value' },
]
</script>

<template>
  <div class="data-table__wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in records" :key="record.id">
          <td v-for="column in columns" :key="column.key">{{ record[column.key] }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="loading" class="data-table__message">Loading records...</p>
    <p v-else-if="records.length === 0" class="data-table__message">No records to display.</p>
  </div>
</template>

<style scoped>
.data-table__wrapper {
  overflow-x: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.data-table th {
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-bg);
}

.data-table tbody tr:hover {
  background: var(--color-bg);
}

.data-table__message {
  margin: 0;
  padding: 24px;
  color: var(--color-text-muted);
  text-align: center;
  font-size: 14px;
}
</style>
