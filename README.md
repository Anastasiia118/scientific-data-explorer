# Scientific Data Explorer

A full-stack project for uploading, validating and browsing structured
research datasets. All data is synthetic.

**Status:** MVP complete: CSV upload, a server-side paginated, sortable and
searchable records table, and a chart of value statistics per category. Next:
authentication. See [`docs/progress.md`](docs/progress.md).

## Stack

- **Backend:** Python 3.13, Django 5.2, Django REST Framework
- **Database:** PostgreSQL 17, run with Docker Compose
- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Vue Router, Vuetify 4 (some components still use plain CSS), Chart.js (via vue-chartjs)

## Project layout

```
backend/            Django project (config/) and the datasets app
frontend/           Vue SPA (see frontend/README.md)
docs/progress.md    Progress tracker and technical decisions
docker-compose.yml  PostgreSQL service
```

## Local setup

Prerequisites: Python 3.13, Node.js, Docker.

**1. Environment and database**

```bash
cp backend/.env.example backend/.env   # then set real passwords
docker compose up -d --wait            # starts PostgreSQL on 127.0.0.1:5432
```

**2. Backend** (http://127.0.0.1:8000)

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser       # optional, for /admin/
python manage.py runserver
```

**3. Frontend** (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the Django server, so open the app on port 5173.

## Checks

```bash
cd backend
python manage.py test datasets
python manage.py check
python manage.py makemigrations --check --dry-run

cd ../frontend
npm run build                          # type-check and build
```

## API

There is no authentication yet; every endpoint is public.

| Method | Path                          | Description                                          |
| ------ | ----------------------------- | ---------------------------------------------------- |
| GET    | `/api/datasets/`              | List datasets, newest first                          |
| GET    | `/api/datasets/{id}/`         | Retrieve one dataset                                 |
| GET    | `/api/datasets/{id}/records/` | List a dataset's records, paginated (see below)      |
| GET    | `/api/datasets/{id}/stats/`   | Value statistics per category (see below)            |
| POST   | `/api/datasets/upload/`       | Multipart `name` + `file`; returns the new dataset (201) |

### Records: pagination, sorting and search

`GET /api/datasets/{id}/records/` accepts these query parameters:

- `page`: page number, starting at 1; a page past the end is a 404
- `page_size`: 1–100, default 25
- `ordering`: `sample_id`, `category` or `value`, prefixed with `-` for descending (for example `-value`). Default: CSV row order. Unknown fields are ignored
- `search`: case-insensitive substring match on `sample_id` or `category`

Search and sorting apply to all records before paginating. The response:

```json
{"count": 150, "next": "...", "previous": null, "results": [{"id": 1, "sample_id": "S-001", "category": "control", "value": 1.5}]}
```

### Statistics per category

`GET /api/datasets/{id}/stats/` returns one entry per category over all records,
sorted by category (not paginated; search does not apply):

```json
[{"category": "control", "count": 64, "min": 5.691, "avg": 10.08, "max": 12.875}]
```

A dataset without records returns `[]`.

### CSV format

```csv
sample_id,category,value
S-001,control,1.5
S-002,treated,2e3
```

- UTF-8 (a byte-order mark is accepted), at most 1 MB and 10,000 data rows
- `sample_id` and `category`: required, at most 100 characters; `sample_id` unique within the file
- `value`: a decimal or scientific-notation number; NaN and Infinity are rejected
- Dataset names must be unique, and the same file cannot be uploaded twice
- The import is all or nothing. Errors use row numbers (the header is row 1), for example:

```json
{"file": ["Row 3: 'value' must be a number, got 'abc'."]}
```
