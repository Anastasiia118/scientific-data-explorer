<script setup lang="ts">
import type { DataTableHeader, DataTableSortItem } from 'vuetify'
import type { SampleRecord } from '../types/dataset'

defineProps<{
  /** The records of the current page only. */
  records: SampleRecord[]
  /** Number of matching records across all pages. */
  total: number
  loading?: boolean
}>()

// The parent owns the table state and fetches a page whenever it changes.
const page = defineModel<number>('page', { required: true })
const itemsPerPage = defineModel<number>('itemsPerPage', { required: true })
const sortBy = defineModel<DataTableSortItem[]>('sortBy', { required: true })

// The CSV schema is fixed, so the columns are too. Numbers are right-aligned
// so their digits line up.
const headers: DataTableHeader<SampleRecord>[] = [
  { key: 'sample_id', title: 'Sample ID' },
  { key: 'category', title: 'Category' },
  { key: 'value', title: 'Value', align: 'end' },
]

// The backend accepts any page size up to 100; these are the ones offered.
const itemsPerPageOptions = [10, 25, 50, 100]
</script>

<template>
  <v-data-table-server
    v-model:page="page"
    v-model:items-per-page="itemsPerPage"
    v-model:sort-by="sortBy"
    class="data-table"
    :headers="headers"
    :items="records"
    :items-length="total"
    item-value="id"
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
