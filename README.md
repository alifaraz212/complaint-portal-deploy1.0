# Complaint & Feedback Portal

A Django REST Framework-based portal where users submit complaints, track their status, and communicate with administrators. Admins manage complaints through a dashboard — assign priority, respond, and resolve issues.

## Tech Stack

- Django 5.1 + Django REST Framework
- PostgreSQL 15
- JWT Authentication (djangorestframework-simplejwt)
- Docker + Docker Compose
- Python 3.12

## Project Structure

```
complaint-portal/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/        # Django project settings, URLs
│   ├── accounts/      # Custom User model, auth
│   ├── complaints/    # Complaint, Category, Response, ActivityLog models
│   └── dashboard/     # Stats and reporting (upcoming)
```

## How to Run

### Fresh Setup

```
git clone <repo-url>
cd complaint-portal
docker compose up --build
```

### Run migrations

```
docker compose exec app python manage.py migrate
```

### Create admin user

```
docker compose exec app python manage.py createsuperuser
```

### Access admin panel

```
http://localhost:8000/admin
```

## Important: Database Reset

If you get this error after pulling a new branch:

```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

It means migrations were already applied on a previous schema. Fix it by wiping the database volume and starting fresh:

```
docker compose down -v
docker compose up --build
docker compose exec app python manage.py migrate
```

The `-v` flag removes named volumes including PostgreSQL data. You will need to recreate your superuser after this.

## User Roles

- **User** — register, submit complaints, track status, reply to admin responses
- **Admin** — view all complaints, assign priority, change status, respond, view dashboard

