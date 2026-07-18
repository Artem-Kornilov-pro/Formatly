# Formatly
AI-powered formatting linter and auto-fixer for Word documents. Classifies document structure with LLMs, applies academic/GOST formatting rules deterministically, and validates the result.

## Project structure

```
backend/    FastAPI app: parsing, LLM classification, formatting, validation
frontend/   React + TypeScript UI: upload, job status, download
```

## Getting started

Requires Docker and Docker Compose.

```
make up
```

This copies `.env.example` to `.env` on first run, then builds and starts Postgres, Redis, the API, the Celery worker, and the frontend dev server.

- API: http://localhost:8000
- Frontend: http://localhost:5173

Other common commands:

```
make test    # run backend and frontend test suites
make lint    # run backend and frontend linters
make down    # stop the stack
```

## License
Licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE). Free for noncommercial use; commercial use requires a separate agreement with the copyright holder.
