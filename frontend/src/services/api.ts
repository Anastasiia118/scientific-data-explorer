import axios from 'axios'
import type { Dataset, Page, SampleRecord } from '../types/dataset'

// All requests go to the Django REST Framework backend. In development,
// Vite proxies "/api" to http://127.0.0.1:8000 (see vite.config.ts).
const http = axios.create({
  baseURL: '/api',
})

export async function fetchDatasets(): Promise<Dataset[]> {
  const response = await http.get<Dataset[]>('/datasets/')
  return response.data
}

export async function fetchDataset(id: number): Promise<Dataset> {
  const response = await http.get<Dataset>(`/datasets/${id}/`)
  return response.data
}

export interface RecordQuery {
  page: number
  pageSize: number
  /** Comma-separated fields, "-" prefix for descending, e.g. "-value". */
  ordering?: string
  search?: string
}

/**
 * Fetches one page of a dataset's records. Search and ordering are applied
 * by the backend to all records, before paginating. Pass `signal` to cancel
 * the request when its result is no longer needed.
 */
export async function fetchDatasetRecords(
  id: number,
  query: RecordQuery,
  signal?: AbortSignal,
): Promise<Page<SampleRecord>> {
  const response = await http.get<Page<SampleRecord>>(`/datasets/${id}/records/`, {
    // Empty values are left out of the URL (axios skips undefined params).
    params: {
      page: query.page,
      page_size: query.pageSize,
      ordering: query.ordering || undefined,
      search: query.search || undefined,
    },
    signal,
  })
  return response.data
}

/**
 * Uploads a CSV file (columns: sample_id, category, value) and creates a
 * dataset from it. The backend responds with the created dataset.
 */
export async function uploadDataset(name: string, file: File): Promise<Dataset> {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('file', file)
  const response = await http.post<Dataset>('/datasets/upload/', formData)
  return response.data
}

/**
 * Turns a failed request into a message for the user. Distinguishes an
 * unreachable server from errors reported by the backend, which DRF returns
 * as `{"detail": "..."}` or `{"field": ["...", ...]}`.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback
  if (!error.response) return 'Could not reach the server. Is the backend running?'

  const data: unknown = error.response.data
  if (data && typeof data === 'object') {
    if ('detail' in data && typeof data.detail === 'string') return data.detail
    const messages = Object.values(data).flat().filter((m) => typeof m === 'string')
    if (messages.length > 0) return messages.join(' ')
  }
  return fallback
}
