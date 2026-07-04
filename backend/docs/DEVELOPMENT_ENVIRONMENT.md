# FraudWatch Development Environment Setup

This guide covers setting up a professional Python development environment for FraudWatch.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Activation](#activation)
- [Installing Dependencies](#installing-dependencies)
- [Running Services](#running-services)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 13+ (running via Docker or local installation)
- Redis (running via Docker or local installation)
- Git

## Virtual Environment Setup

The project uses an isolated virtual environment located at `backend/.venv`.

### Create Virtual Environment

```bash
# From the backend directory
python -m venv .venv
```

### Verify Installation

```bash
# Check Python points to virtual environment
python --version

# Check pip points to virtual environment
pip --version
```

Expected output should show paths under `backend/.venv`.

## Activation

### Windows - PowerShell

```powershell
# Activate virtual environment
backend\.venv\Scripts\Activate.ps1

# Deactivate when done
deactivate
```

### Windows - Command Prompt (CMD)

```cmd
# Activate virtual environment
backend\.venv\Scripts\activate.bat

# Deactivate when done
deactivate
```

### Windows - Git Bash

```bash
# Activate virtual environment
source backend/.venv/Scripts/activate

# Deactivate when done
deactivate
```

### Linux / macOS

```bash
# Activate virtual environment
source backend/.venv/bin/activate

# Deactivate when done
deactivate
```

## Installing Dependencies

### Install All Dependencies

```bash
# From backend directory with virtual environment activated
pip install -r requirements.txt
```

### Install Development Dependencies Only

```bash
pip install black isort flake8 mypy
```

### Update Dependencies

```bash
# Upgrade a specific package
pip install --upgrade package-name

# Update requirements-lock.txt
pip freeze > requirements-lock.txt
```

## Running Services

### Start PostgreSQL and Redis with Docker

```bash
# From project root
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

### Run FastAPI Development Server

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Run Alembic Migrations

```bash
# Check current migration status
alembic current

# Generate new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Run Celery Worker

#### Windows Development

```bash
# Windows requires solo pool
celery -A app.workers.celery worker --pool=solo --loglevel=info
```

#### Linux / macOS / Docker

```bash
# Default worker pool (prefork)
celery -A app.workers.celery worker --loglevel=info
```

#### Celery Beat (Scheduler)

```bash
celery -A app.workers.celery beat --loglevel=info
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login
```

## Development Workflow

### Code Quality

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Run linter
flake8 .

# Type check
mypy .
```

### Validate Environment

Run the validation script to ensure everything is configured correctly:

```bash
# From backend directory
python scripts/validate_environment.py
```

This script checks:
- Python version
- Virtual environment activation
- Required packages installed
- PostgreSQL connectivity
- Redis connectivity
- Alembic configuration
- FastAPI imports
- Project structure
- Environment variables
- Platform compatibility

### Environment Variables

Create a `.env` file in the backend directory based on `.env.example`:

```bash
# Copy example file
cp .env.example .env

# Edit with your settings
# Ensure these are set:
# - DATABASE_URL
# - DATABASE_SYNC_URL
# - REDIS_URL
# - CELERY_BROKER_URL
# - CELERY_RESULT_BACKEND
# - JWT_SECRET_KEY
```

## Common Windows Issues

### PowerShell Execution Policy

If you get an error activating the virtual environment in PowerShell:

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Confirm
Y
```

### PostgreSQL Connection Refused

Ensure PostgreSQL is running:
```bash
# Check if Docker container is running
docker-compose ps postgres

# Start if not running
docker-compose up -d postgres
```

### Port Already in Use

If port 8000, 5432, or 6379 is already in use:

```powershell
# Find process using the port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Long Path Issues

Windows has a default 260-character path limit. To enable long paths:

```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

## Linux Deployment Notes

### Environment Variables

Set environment variables in your deployment platform (Render, Railway, VPS):

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export DATABASE_SYNC_URL="postgresql://user:pass@host:5432/dbname"
export REDIS_URL="redis://host:6379/0"
export CELERY_BROKER_URL="redis://host:6379/1"
export CELERY_RESULT_BACKEND="redis://host:6379/2"
export JWT_SECRET_KEY="your-production-secret-key"
```

### Production Dependencies

Install only production dependencies:

```bash
pip install -r requirements.txt
```

### Gunicorn for Production

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Systemd Service (Linux VPS)

Create `/etc/systemd/system/fraudwatch.service`:

```ini
[Unit]
Description=FraudWatch API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=fraudwatch
WorkingDirectory=/opt/fraudwatch/backend
Environment="PATH=/opt/fraudwatch/backend/.venv/bin"
ExecStart=/opt/fraudwatch/backend/.venv/bin/gunicorn app.main:app --workers 4 --bind unix:/run/fraudwatch.sock

[Install]
WantedBy=multi-user.target
```

## Quality Assurance

### Pre-commit Checks

Before committing, ensure:

1. All tests pass: `pytest`
2. Code is formatted: `black .`
3. Imports are sorted: `isort .`
4. No linting errors: `flake8 .`
5. No type errors: `mypy .`

### VS Code Integration

The project includes `.vscode/settings.json` with:
- Python interpreter path
- Format on save (Black)
- Import organization (isort)
- Linting (flake8, mypy)
- Test discovery (pytest)
- Type checking (strict mode)

## Project Structure

```
FraudWatch/
├── backend/
│   ├── .venv/                    # Virtual environment (gitignored)
│   ├── alembic/                  # Database migrations
│   ├── app/                      # Application code
│   │   ├── api/                  # API routes
│   │   ├── core/                 # Core functionality
│   │   ├── dependencies/         # FastAPI dependencies
│   │   ├── models/               # SQLAlchemy models
│   │   ├── repositories/         # Data access layer
│   │   ├── schemas/              # Pydantic schemas
│   │   └── services/             # Business logic
│   ├── docs/                     # Documentation
│   ├── seed/                     # Database seeders
│   ├── scripts/                  # Utility scripts
│   ├── alembic.ini               # Alembic configuration
│   ├── requirements.txt          # Direct dependencies
│   └── requirements-lock.txt     # Locked dependencies
├── docker/                       # Docker configurations
├── frontend/                     # Next.js frontend
└── ml/                           # Machine learning models
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)

## Support

For environment setup issues:
1. Check this guide's Troubleshooting section
2. Run `python scripts/validate_environment.py`
3. Consult `docker-compose.yml` for service configuration
4. Review `.env.example` for required environment variables
