import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchDatasets, getErrorMessage, uploadDataset } from '../services/api'
import type { Dataset } from '../types/dataset'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets = ref<Dataset[]>([])
  const loading = ref(false)
  const uploading = ref(false)
  const error = ref<string | null>(null)

  async function loadDatasets(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      datasets.value = await fetchDatasets()
    } catch (e) {
      error.value = getErrorMessage(e, 'Could not load datasets.')
    } finally {
      loading.value = false
    }
  }

  /** Returns the created dataset, or null if the upload failed. */
  async function upload(name: string, file: File): Promise<Dataset | null> {
    uploading.value = true
    error.value = null
    try {
      const dataset = await uploadDataset(name, file)
      await loadDatasets()
      return dataset
    } catch (e) {
      error.value = getErrorMessage(e, 'Upload failed.')
      return null
    } finally {
      uploading.value = false
    }
  }

  return { datasets, loading, uploading, error, loadDatasets, upload }
})
