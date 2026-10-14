# Progress

## Current milestone
PostgreSQL setup

## Completed
- Vue frontend structure
- Dataset/SampleRecord TypeScript types
- Initial API contract
- Vite proxy configuration
- Django 5.2 + DRF skeleton (`backend/config`)
- Settings read from environment variables, loaded from `backend/.env` via python-dotenv

## Decisions
- Fixed CSV schema for MVP
- PostgreSQL as primary database
- No pagination in initial MVP: single client and small CSVs; enforce a row limit on upload instead
- Python 3.13 (Homebrew); venv + pip; `requirements.txt` lists direct dependencies only, pinned exactly
- python-dotenv for loading `.env` (django-environ considered, not needed yet)
- `DEBUG` defaults to off; a missing `DJANGO_SECRET_KEY` is an error unless `DEBUG` is on

## Next
- Choose how to run PostgreSQL locally
- Configure Django to use PostgreSQL

## Open questions
- CSV validation error format
- Duplicate dataset names
