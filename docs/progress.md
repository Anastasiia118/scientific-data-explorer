# Progress

## Current milestone
`datasets` app and data model

## Completed
- Vue frontend structure
- Dataset/SampleRecord TypeScript types
- Initial API contract
- Vite proxy configuration
- Django 5.2 + DRF skeleton (`backend/config`)
- Settings read from environment variables, loaded from `backend/.env` via python-dotenv
- PostgreSQL 17 in Docker Compose (`db` service); Django connected; initial migrations applied

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

## Known issues
- Compose `env_file` passes all of `backend/.env` (including `DJANGO_SECRET_KEY`) to the `db` container; scope per service before deployment

## Next
- Create the `datasets` app with `Dataset` and `SampleRecord` models

## Open questions
- CSV validation error format
- Duplicate dataset names
