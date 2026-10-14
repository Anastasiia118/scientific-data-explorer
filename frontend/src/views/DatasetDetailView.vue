<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import SearchBar from '../components/SearchBar.vue'
import DataTable from '../components/DataTable.vue'
import { fetchDataset, fetchDatasetRecords, getErrorMessage } from '../services/api'
import type { Dataset, SampleRecord } from '../types/dataset'

const props = defineProps<{
  id: number
}>()

// Records belong to the dataset shown by this route, so they are kept in
// the view rather than in a global store.
const dataset = ref<Dataset | null>(null)
const records = ref<SampleRecord[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')

watch(
  () => props.id,
  async (id) => {
    loading.value = true
    error.value = null
    dataset.value = null
    records.value = []
    try {
      const [loadedDataset, loadedRecords] = await Promise.all([
        fetchDataset(id),
        fetchDatasetRecords(id),
      ])
      // Ignore the response if the user navigated to another dataset meanwhile.
      if (id !== props.id) return
      dataset.value = loadedDataset
      records.value = loadedRecords
    } catch (e) {
      if (id === props.id) error.value = getErrorMessage(e, 'Could not load dataset.')
    } finally {
      if (id === props.id) loading.value = false
    }
  },
  { immediate: true },
)

const filteredRecords = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return records.value
  return records.value.filter(
    (record) =>
      record.sample_id.toLowerCase().includes(query) ||
      record.category.toLowerCase().includes(query),
  )
})
</script>

<template>
  <section class="dataset-detail">
    <RouterLink :to="{ name: 'dataset-list' }" class="dataset-detail__back">
      &larr; All datasets
    </RouterLink>

    <h1 class="dataset-detail__title">{{ dataset?.name ?? 'Dataset' }}</h1>

    <p v-if="error" class="dataset-detail__error">{{ error }}</p>

    <div class="dataset-detail__toolbar">
      <SearchBar v-model="searchQuery" />
    </div>

    <DataTable :records="filteredRecords" :loading="loading" />
  </section>
</template>

<style scoped>
.dataset-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dataset-detail__back {
  color: var(--color-accent);
  text-decoration: none;
  font-size: 14px;
}

.dataset-detail__title {
  margin: 0;
  font-size: 20px;
}

.dataset-detail__toolbar {
  display: flex;
}

.dataset-detail__error {
  margin: 0;
  color: var(--color-danger);
  font-size: 14px;
}
</style>
