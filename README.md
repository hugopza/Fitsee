# Fittsee Demo Backend - MVP (Phase 1)

This is the backend for the Fittsee e-commerce demo.

## Phase 1: Offline 3D Render Workflow

Features:

- **FastAPI** + **PostgreSQL** + **Redis** + **Worker**
- Offline rendering (simulated via file copy in Phase 1)
- Async job queue (RQ)

### User Workflow

1. **Register/Login** to get an auth token.
2. **Complete Profile** (Height, Chest, Shoulders are mandatory).
3. **Request Render**: `POST /api/v1/renders` with product ID and Size.
4. **Poll Status**: `GET /api/v1/renders/{job_id}` until `status=DONE`.
5. **View Video**: Access the `video_url`.

## Tech Stack

- **Python 3.12** + **FastAPI**
- **PostgreSQL** + SQLAlchemy + Alembic
- **Redis** + **RQ** (Job Queue)
- **Docker Compose**

## Setup & Run

### 1. Prerequisites

- Docker Desktop installed and running.
- Create `.env` from example:
  ```bash
  cp .env.example .env
  ```

### 2. Prepare Template (Mock Render)

Place your template MP4 file at:
`./data/static/templates/template.mp4`
_(This file will be copied as the "result" of every render job in Phase 1)_

### 3. Start Services

```bash
docker-compose up --build
```

This starts:

- API: `http://localhost:8000`
- Worker (background rendering)
- Redis: `6379`
- DB: `5432`

Swagger UI: `http://localhost:8000/docs`

### 4. Migrations

To run existing migrations:

```bash
docker-compose run --rm api alembic upgrade head
```

### 5. Testing

Run tests inside the container:

```bash
docker-compose run --rm api pytest
```

## Seed Data

To seed admin and default products:

```bash
docker-compose run --rm api python scripts/seed.py
```

## Default Credentials

- **Admin Email**: `admin@fittsee.com`
- **Password**: `admin123`

## Directory Structure

- `app/main.py`: App entry point.
- `app/modules/renders`: Render Job API & Service.
- `app/worker`: Worker entry point and render logic.
- `app/modules/try_on`: (Renamed from `try`) Virtual Try-On module.
- `data/renders`: Storage for output videos.
