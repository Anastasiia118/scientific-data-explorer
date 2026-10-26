<script setup lang="ts">
import type { SampleRecord } from '../types/dataset'

defineProps<{
  records: SampleRecord[]
  loading?: boolean
}>()

// The CSV schema is fixed, so the columns are too. Numbers are right-aligned
// so their digits line up.
const headers: { key: keyof SampleRecord; title: string; align?: 'end' }[] = [
  { key: 'sample_id', title: 'Sample ID' },
  { key: 'category', title: 'Category' },
  { key: 'value', title: 'Value', align: 'end' },
]

// All records are already loaded, so sorting and paging happen in the
// browser; the API is not paginated.
const itemsPerPageOptions = [10, 25, 50, 100]
</script>

<template>
  <v-data-table
    class="data-table"
    :headers="headers"
    :items="records"
    item-value="id"
    :items-per-page="25"
    :items-per-page-options="itemsPerPageOptions"
    :loading="loading"
    loading-text="Loading records..."
    no-data-text="No records to display."
    density="compact"
  />
</template>

<style scoped>
.data-table {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}
</style>
