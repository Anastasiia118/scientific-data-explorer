/**
 * Types mirroring the Django REST Framework API. Field names are kept in
 * snake_case exactly as the backend returns them.
 */

export interface Dataset {
  id: number
  name: string
  /** ISO 8601 timestamp, e.g. "2026-10-14T09:30:00Z". */
  created_at: string
}

/**
 * A single row of an uploaded CSV file. Records are always fetched through
 * their dataset (`/datasets/{id}/records/`), so the dataset id is omitted.
 */
export interface SampleRecord {
  id: number
  sample_id: string
  category: string
  value: number
}
