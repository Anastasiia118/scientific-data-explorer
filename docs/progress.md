# Progress

## Current milestone
Read-only REST API for datasets and records

## Completed
- Vue frontend structure
- Dataset/SampleRecord TypeScript types
- Initial API contract
- Vite proxy configuration
- Django 5.2 + DRF skeleton (`backend/config`)
- Settings read from environment variables, loaded from `backend/.env` via python-dotenv
- PostgreSQL 17 in Docker Compose (`db` service); Django connected; initial migrations applied
- `datasets` app: `Dataset` and `SampleRecord` models, initial migration, admin, model tests

## Decisions
- Fixed CSV schema for MVP
- PostgreSQL as primary database
- No pagination in initial MVP: single client and small CSVs; enforce a row limit on upload instead
- Python 3.13 (Homebrew); venv + pip; `requirements.txt` lists direct dependencies only, pinned exactly
- python-dotenv for loading `.env` (django-environ considered, not needed yet)
- `DEBUG` defaults to off; a missing `DJANGO_SECRET_KEY` is an error unless `DEBUG` is on
- PostgreSQL runs in Docker rather than a local install: the target is Docker Compose locally and AWS RDS in production
- `backend/.env` is shared by Compose and Django; Django runs on the host for now and connects to `127.0.0.1:5432`
- Postgres port published on `127.0.0.1` only, not the local network
- Dataset names are unique (case-sensitive): duplicate uploads are most likely mistakes and should get a clear 400
- `value` is a `FloatField`: measurements are floating-point, and `DecimalField` would serialize as a string; NaN/Infinity must be rejected on upload (not valid JSON)
- `category` is free text for now; no predefined choices before we see real data
- Uniqueness rules are enforced by database constraints, not only by validation (safe under concurrent requests)

## Known issues
- Compose `env_file` passes all of `backend/.env` (including `DJANGO_SECRET_KEY`) to the `db` container; scope per service before deployment
- Constraint violations raise `IntegrityError` (500); the upload endpoint must validate duplicates and return 400
- Dataset name uniqueness is case- and whitespace-sensitive; the upload serializer should strip whitespace

## Next
- Read-only API: `GET /api/datasets/`, `/api/datasets/{id}/`, `/api/datasets/{id}/records/`
- Then CSV upload (`POST /api/datasets/upload/`) as a separate iteration

## Open questions
- CSV validation error format
