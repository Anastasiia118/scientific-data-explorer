# Scientific Data Explorer — Frontend

A minimalistic Vue 3 SPA for uploading CSV datasets and browsing their
records. Built with Vue 3 (Composition API, `<script setup>`), TypeScript,
Pinia, Vue Router and Vite.

The UI is plain HTML/CSS for now, structured so components can later be
swapped for Vuetify equivalents (`DataTable` → `v-data-table`,
`SearchBar` → `v-text-field`, etc.).

## Stack

- Vue 3 + TypeScript + `<script setup>`
- Pinia (state: dataset list, upload/loading status)
- Axios (API calls, base URL `/api`)
- Vue Router (routes: `/` dataset list, `/datasets/:id` dataset records)
- Vite (dev server proxies `/api` → `http://127.0.0.1:8000`, the Django
  REST Framework backend)

## Getting started

```bash
npm install
npm run dev
```

## API contract

All API calls live in `src/services/api.ts`; the matching types are in
`src/types/dataset.ts`.

| Method | Path                            | Description                                      |
| ------ | ------------------------------- | ------------------------------------------------ |
| GET    | `/api/datasets/`                | List datasets                                    |
| GET    | `/api/datasets/{id}/`           | Retrieve one dataset                             |
| GET    | `/api/datasets/{id}/records/`   | List the records of a dataset                    |
| POST   | `/api/datasets/upload/`         | Multipart `name` + `file`; returns the dataset   |

The CSV schema is fixed: `sample_id`, `category`, `value`.

## Scripts

- `npm run dev` — start the dev server
- `npm run build` — type-check and build for production
- `npm run preview` — preview the production build
