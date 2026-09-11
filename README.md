# Complaint & Feedback Portal

A complaint management portal where users submit complaints, track their status, and communicate with administrators. Admins manage complaints through a dashboard — assign priority, respond, and resolve issues.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 + Django REST Framework |
| Database | PostgreSQL 15 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Frontend | Plain HTML/CSS/JS served by Nginx |
| Containerization | Docker + Docker Compose |

## Architecture

```
Browser
   │
   ├── Frontend (Nginx) → http://localhost:3000
   │        │
   │        │ HTTP/JSON + JWT Bearer token
   │        ▼
   └── Django REST API → http://localhost:8000
            │
            ├── accounts/    → Auth, User management
            ├── complaints/  → Complaint CRUD, workflow, responses
            └── dashboard/   → Stats and reporting
                    │
                    ▼
             PostgreSQL :5434
```

**Request flow:**
```
HTTP Request
    ↓
URLs (config/urls.py)
    ↓
Views (permission check)
    ↓
Serializers (validation)
    ↓
Services (business logic)
    ↓
Models / ORM
    ↓
PostgreSQL
```

## Project Structure

```
complaint-portal/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── conftest.py          # Shared test fixtures
│   ├── manage.py
│   ├── config/              # Django settings, URLs, exception handler
│   ├── accounts/            # Custom User model, auth views, serializers
│   ├── complaints/          # Complaint, Category, Response, ActivityLog
│   └── dashboard/           # Stats and reporting
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── public/              # HTML pages, CSS, JS
```

## User Roles

| Role | Capabilities |
|---|---|
| User | Register, login, submit complaints, view own complaints, reply to responses |
| Admin | View all complaints, assign priority, change status, respond, view dashboard, manage categories |

## Status Workflow

```
open → in_progress → resolved → closed

Reopening allowed:
in_progress → open
resolved → in_progress
```

Invalid transitions return `400 Bad Request`.

---

## Getting Started

### Prerequisites

- Docker Desktop installed and running
- Git

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=complaint_portal
DB_USER=complaint_user
DB_PASSWORD=complaint_pass
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Start the Application

```bash
git clone <repo-url>
cd complaint-portal
docker compose up --build
```

This starts three services:
- **db** — PostgreSQL on port 5434
- **app** — Django API on port 8000
- **frontend** — Nginx serving HTML/JS on port 3000

### Access the Application

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Django API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin |

### Run Migrations

```bash
docker compose exec app python manage.py migrate
```

### Collect Static Files (Django Admin CSS)

```bash
docker compose exec app python manage.py collectstatic --noinput
```

### Create Admin User

```bash
docker compose exec app python manage.py createadmin --email admin@example.com --password YourPassword123!
```

### Database Reset

If you get `InconsistentMigrationHistory` after pulling a new branch:

```bash
docker compose down -v
docker compose up --build
```

The `-v` flag removes volumes including PostgreSQL data. Recreate admin user after this.

---

## Running Tests

```bash
docker compose run --rm app python -m pytest
```

Verbose output:

```bash
docker compose run --rm app python -m pytest -v
```

Run specific test file:

```bash
docker compose run --rm app python -m pytest accounts/tests.py -v
```

### Test Coverage

| File | Tests |
|---|---|
| `accounts/tests.py` | Registration, login, JWT claims, negative cases |
| `complaints/tests.py` | Creation, status workflow, invalid transitions, permissions |
| `dashboard/tests.py` | Stats accuracy, access control, soft delete filtering |

---

## API Documentation

All endpoints require `Authorization: Bearer <access_token>` unless marked Public.

### Authentication

#### Register
```
POST /api/auth/register/
```
Request:
```json
{
    "email": "user@example.com",
    "full_name": "Ali Faraz",
    "phone": "+92 300 1234567",
    "password": "StrongPassword123!"
}
```
Response `201`:
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "Ali Faraz",
    "role": "user"
}
```

#### Login
```
POST /api/auth/login/
```
Request:
```json
{
    "email": "user@example.com",
    "password": "StrongPassword123!"
}
```
Response `200`:
```json
{
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>"
}
```

#### Refresh Token
```
POST /api/auth/refresh/
```
Request:
```json
{
    "refresh": "<jwt_refresh_token>"
}
```

#### Get/Update Profile
```
GET  /api/auth/profile/
PUT  /api/auth/profile/
```

---

### Categories

| Method | Endpoint | Access |
|---|---|---|
| GET | `/api/complaints/categories/` | Authenticated |
| POST | `/api/complaints/categories/create/` | Admin only |
| PUT/DELETE | `/api/complaints/categories/<id>/` | Admin only |

---

### Complaints

#### Submit Complaint
```
POST /api/complaints/complaints/
```
Request:
```json
{
    "category": 1,
    "subject": "Internet connection issue",
    "description": "My internet has been unstable for 3 days."
}
```
Response `201`:
```json
{
    "id": 83,
    "complaint_number": "CMP-00083",
    "status": "open",
    "priority": null,
    "subject": "Internet connection issue",
    "created_at": "2026-09-08T14:24:40Z"
}
```

#### List Complaints
```
GET /api/complaints/complaints/
```
Query parameters:
- `status` — filter by status (open, in_progress, resolved, closed)
- `priority` — filter by priority (low, medium, high, urgent)
- `category` — filter by category ID
- `search` — search in subject and description
- `page`, `page_size` — pagination

#### Update Complaint (Admin)
```
PATCH /api/complaints/complaints/<id>/update/
```
Request:
```json
{
    "status": "in_progress",
    "priority": "high"
}
```

---

### Dashboard (Admin only)

#### Statistics
```
GET /api/dashboard/stats/
```
Response `200`:
```json
{
    "total_complaints": 42,
    "by_status": {
        "open": 10,
        "in_progress": 8,
        "resolved": 15,
        "closed": 9
    },
    "by_priority": {
        "low": 5,
        "medium": 12,
        "high": 18,
        "urgent": 7
    },
    "by_category": {
        "Technical Support": 20,
        "Billing": 12,
        "General": 10
    },
    "average_resolution_time_hours": 4.5,
    "this_month_count": 15,
    "last_month_count": 27
}
```

#### Recent Activity
```
GET /api/dashboard/recent/
```
Response `200`:
```json
{
    "recent_complaints": [...],
    "recent_status_changes": [...]
}
```

---

### Error Format

All errors follow this format:

```json
{
    "error": "Validation failed.",
    "details": {
        "password": ["This password is too common."]
    }
}
```
