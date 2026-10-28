<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import type { DataTableSortItem } from 'vuetify'
import SearchBar from '../components/SearchBar.vue'
import DataTable from '../components/DataTable.vue'
import CategoryChart from '../components/CategoryChart.vue'
import {
  fetchDataset,
  fetchDatasetRecords,
  fetchDatasetStats,
  getErrorMessage,
} from '../services/api'
import type { CategoryStats, Dataset, SampleRecord } from '../types/dataset'

const props = defineProps<{
  id: number
}>()

// Records belong to the dataset shown by this route, so they are kept in
// the view rather than in a global store.
const dataset = ref<Dataset | null>(null)
const error = ref<string | null>(null)

// Chart data covers all records, so it does not follow the table's search.
// null while loading.
const stats = ref<CategoryStats[] | null>(null)
const statsError = ref<string | null>(null)

const records = ref<SampleRecord[]>([])
const total = ref(0)
const loading = ref(false)
const recordsError = ref<string | null>(null)

// Table state; the backend searches, sorts and paginates.
const page = ref(1)
const itemsPerPage = ref(25)
const sortBy = ref<DataTableSortItem[]>([])
const searchQuery = ref('')
// searchQuery follows every keystroke; search is updated once typing pauses,
// so a fast typist causes one request instead of one per letter.
const search = ref('')
const SEARCH_DELAY_MS = 300
let searchTimer: ReturnType<typeof setTimeout> | undefined

watch(searchQuery, (query) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    search.value = query.trim()
  }, SEARCH_DELAY_MS)
})

watch(
  () => props.id,
  async (id) => {
    error.value = null
    dataset.value = null
    records.value = []
    total.value = 0
    try {
      const loadedDataset = await fetchDataset(id)
      // Ignore the response if the user navigated to another dataset meanwhile.
      if (id === props.id) dataset.value = loadedDataset
    } catch (e) {
      if (id === props.id) error.value = getErrorMessage(e, 'Could not load dataset.')
    }
  },
  { immediate: true },
)

watch(
  () => props.id,
  async (id) => {
    stats.value = null
    statsError.value = null
    try {
      const loadedStats = await fetchDatasetStats(id)
      if (id === props.id) stats.value = loadedStats
    } catch (e) {
      if (id === props.id) statsError.value = getErrorMessage(e, 'Could not load chart data.')
    }
  },
  { immediate: true },
)

// A different result set starts at page 1: the current page may not exist
// in it. Declared before the fetch watcher so that both changes land in one
// request: Vue runs the queued watchers in order, after this one has reset
// the page.
watch([() => props.id, search, sortBy, itemsPerPage], () => {
  page.value = 1
})

// Only the latest request matters. Starting a new one cancels the previous,
// so a slow, outdated response can never overwrite a newer one.
let controller: AbortController | null = null

async function loadRecords(): Promise<void> {
  controller?.abort()
  const current = new AbortController()
  controller = current

  loading.value = true
  recordsError.value = null
  try {
    const result = await fetchDatasetRecords(
      props.id,
      {
        page: page.value,
        pageSize: itemsPerPage.value,
        ordering: sortBy.value
          .map(({ key, order }) => (order === 'desc' ? '-' : '') + key)
          .join(','),
        search: search.value,
      },
      current.signal,
    )
    if (current.signal.aborted) return
    records.value = result.results
    total.value = result.count
  } catch (e) {
    if (current.signal.aborted) return
    records.value = []
    total.value = 0
    recordsError.value = getErrorMessage(e, 'Could not load records.')
  } finally {
    if (controller === current) loading.value = false
  }
}

watch([() => props.id, page, itemsPerPage, sortBy, search], loadRecords, { immediate: true })

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  controller?.abort()
})
</script>

<template>
  <section class="dataset-detail">
    <RouterLink :to="{ name: 'dataset-list' }" class="dataset-detail__back">
      &larr; All datasets
    </RouterLink>

    <h1 class="dataset-detail__title">{{ dataset?.name ?? 'Dataset' }}</h1>

    <p v-if="error" class="dataset-detail__error">{{ error }}</p>

    <p v-if="statsError" class="dataset-detail__error">{{ statsError }}</p>
    <template v-else-if="stats">
      <CategoryChart v-if="stats.length > 0" :stats="stats" />
      <p v-else class="dataset-detail__muted">No records to chart.</p>
    </template>

    <p v-if="recordsError" class="dataset-detail__error">{{ recordsError }}</p>

    <div class="dataset-detail__toolbar">
      <SearchBar v-model="searchQuery" />
    </div>

    <DataTable
      v-model:page="page"
      v-model:items-per-page="itemsPerPage"
      v-model:sort-by="sortBy"
      :records="records"
      :total="total"
      :loading="loading"
    />
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

.dataset-detail__muted {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.dataset-detail__error {
  margin: 0;
  color: var(--color-danger);
  font-size: 14px;
}
</style>
