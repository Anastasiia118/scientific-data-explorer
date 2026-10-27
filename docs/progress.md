# Progress

## Current milestone
MVP: CSV upload → Vuetify table → chart

## Completed
- Vue frontend structure
- Dataset/SampleRecord TypeScript types
- Initial API contract
- Vite proxy configuration
- Django 5.2 + DRF skeleton (`backend/config`)
- Settings read from environment variables, loaded from `backend/.env` via python-dotenv
- PostgreSQL 17 in Docker Compose (`db` service); Django connected; initial migrations applied
- `datasets` app: `Dataset` and `SampleRecord` models, initial migration, admin, model tests
- Read-only API: `GET /api/datasets/`, `/api/datasets/{id}/`, `/api/datasets/{id}/records/`; verified end to end through the Vite proxy
- CSV upload API: `POST /api/datasets/upload/` (multipart `name` + `file`); row-numbered validation, all-or-nothing import; verified through the Vite proxy and manually in the browser (valid, invalid and 150-row files)
- Re-uploads of an identical file are rejected (`Dataset.content_hash`, migration `0002`); covered by tests
- Root `README.md` with local setup, checks and the API overview
- Vuetify 4 installed; theme colors match `style.css`; light theme pinned (no dark styles yet)
- Server-side pagination, sorting and search for records: `GET /api/datasets/{id}/records/` with `page`, `page_size` (default 25, max 100), `ordering`, `search`; `v-data-table-server` in the frontend (debounced search, outdated requests cancelled); verified in the browser
- Upload form on Vuetify (`v-text-field`, `v-file-input`, `v-btn`) with persistent "Required" hints; outlined fields restyled to match `style.css` (8px radius, light grey border); verified in the browser

## In progress
- None

## Decisions
- Fixed CSV schema for MVP
- PostgreSQL as primary database
- Records are paginated on the server: an upload can have up to 10,000 rows. Ordering always ends with `id`, so pages are stable when values tie
- Python 3.13 (Homebrew); venv + pip; `requirements.txt` lists direct dependencies only, pinned exactly
- python-dotenv for loading `.env` (django-environ considered, not needed yet)
- `DEBUG` defaults to off; a missing `DJANGO_SECRET_KEY` is an error unless `DEBUG` is on
- PostgreSQL runs in Docker rather than a local install: the target is Docker Compose locally and AWS RDS in production
- `backend/.env` is shared by Compose and Django; Django runs on the host for now and connects to `127.0.0.1:5432`
- Postgres port published on `127.0.0.1` only, not the local network
- Dataset names are unique (case-sensitive) and stripped of surrounding whitespace: duplicate uploads are most likely mistakes and get a clear 400
- `value` is a `FloatField`: measurements are floating-point, and `DecimalField` would serialize as a string; NaN/Infinity are rejected on upload (not valid JSON)
- `category` is free text for now; no predefined choices before we see real data
- Uniqueness rules are enforced by database constraints, not only by validation (safe under concurrent requests)
- `DatasetViewSet` (`ReadOnlyModelViewSet` + `upload` action) for datasets; records have their own `ListAPIView`, because the endpoint has its own pagination and filters (`@action` cannot set `search_fields`/`ordering_fields`). No nested-router package for a single nested URL
- Record search uses DRF's `SearchFilter`; exact field filters (`django-filter`) wait until a UI needs them
- `AllowAny` set explicitly in `REST_FRAMEWORK`: the MVP has no authentication, and changing it must be deliberate
- CSV parsing lives in `datasets/csv_import.py` with no Django imports (testable without HTTP/DB, reusable for other input sources); built-in `csv` module with `strict=True`, no pandas
- Upload limits: file ≤ 1 MB (checked before reading), UTF-8 (`utf-8-sig`, so Excel's BOM is accepted), 1–10,000 data rows
- CSV errors use DRF's field-error format with physical line numbers (header is row 1; blank lines skipped but counted), capped at 10 messages plus "...and N more errors."
- `value` accepts decimal and scientific notation only (`1.5`, `1e3`); underscores, NaN and Infinity are rejected
- Upload is one transaction (`transaction.atomic` + `bulk_create`); only an `IntegrityError` on the dataset insert that is confirmed to be a duplicate name becomes a 400; any other constraint violation is a bug and stays a 500
- Dataset ownership (`owner` FK) is added together with JWT authentication, not before
- A duplicate file means identical bytes (SHA-256), not identical rows: simple and predictable. Rejected with a 400 that names the existing dataset. `content_hash` is nullable (datasets created before hashing have no file to hash); it becomes unique per owner once auth arrives, so one user's uploads are not revealed to another

## Known issues
- Compose `env_file` passes all of `backend/.env` (including `DJANGO_SECRET_KEY`) to the `db` container; scope per service before deployment

## Next
- Chart of record values (last MVP item)

## Planned (after MVP, before AWS deployment)
- JWT authentication with djangorestframework-simplejwt: short-lived access token in memory, refresh token in an httpOnly cookie, rotation + blacklist; add `Dataset.owner` at the same time
- Then Docker setup for Django, then AWS deployment

## Open questions
- Chart data: records are paginated, so the chart cannot use the table's page. Proposed: a small aggregated endpoint (e.g. value statistics per category) over all records; not decided yet
