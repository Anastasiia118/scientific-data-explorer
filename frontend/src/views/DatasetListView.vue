<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CsvUploadForm from '../components/CsvUploadForm.vue'
import { useDatasetStore } from '../stores/datasetStore'

const store = useDatasetStore()
const router = useRouter()

onMounted(() => {
  void store.loadDatasets()
})

async function onUpload(payload: { name: string; file: File }): Promise<void> {
  const dataset = await store.upload(payload.name, payload.file)
  if (dataset) {
    await router.push({ name: 'dataset-detail', params: { id: dataset.id } })
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}
</script>

<template>
  <section class="dataset-list">
    <h1 class="dataset-list__title">Datasets</h1>

    <CsvUploadForm :uploading="store.uploading" @upload="onUpload" />

    <p v-if="store.error" class="dataset-list__error">{{ store.error }}</p>

    <p v-if="store.loading" class="dataset-list__message">Loading datasets...</p>
    <p v-else-if="store.datasets.length === 0" class="dataset-list__message">
      No datasets yet. Upload a CSV file to get started.
    </p>
    <ul v-else class="dataset-list__items">
      <li v-for="dataset in store.datasets" :key="dataset.id" class="dataset-list__item">
        <RouterLink :to="{ name: 'dataset-detail', params: { id: dataset.id } }">
          {{ dataset.name }}
        </RouterLink>
        <span class="dataset-list__date">{{ formatDate(dataset.created_at) }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dataset-list__title {
  margin: 0;
  font-size: 20px;
}

.dataset-list__error {
  margin: 0;
  color: var(--color-danger);
  font-size: 14px;
}

.dataset-list__message {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.dataset-list__items {
  margin: 0;
  padding: 0;
  list-style: none;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.dataset-list__item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 12px;
  font-size: 14px;
}

.dataset-list__item + .dataset-list__item {
  border-top: 1px solid var(--color-border);
}

.dataset-list__item a {
  color: var(--color-accent);
  text-decoration: none;
}

.dataset-list__date {
  color: var(--color-text-muted);
}
</style>
