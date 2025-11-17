# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ControlHS** is a FastAPI-based REST API for asset management (patrimônios) built for Health Safety. It handles authentication, asset tracking, transfers, inventory management, and audit logging.

**Tech Stack:**
- FastAPI 0.110.0
- PostgreSQL + SQLAlchemy 2.0.29
- JWT authentication (python-jose)
- Password hashing (bcrypt)
- Gunicorn + Uvicorn
- Docker + Traefik reverse proxy

## Architecture

### Directory Structure

```
app/
├── api/          # API route handlers (one file per domain)
├── core/         # Core configuration and security
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic schemas for request/response validation
└── utils/        # Database session and logging utilities
```

### Key Architectural Patterns

**Database Session Management:**
- Database connections use dependency injection via `get_db()` from `app/utils/db.py`
- All endpoints receive `db: Session = Depends(get_db)`
- Sessions auto-close after each request

**Authentication Flow:**
- JWT tokens created on `/login` with payload: `{user_id, username, role, setor_id}`
- Protected routes use `current_user: User = Depends(get_current_user)`
- Token validation in `app/core/security.py` via `get_current_user()`

**User-Setor Relationship:**
- Users can be assigned to a `setor` (department/sector) via `user.setor_id`
- This relationship was recently added and affects authorization logic
- The `setor_id` is included in JWT tokens and returned on login

**File Upload System:**
- Attachments (anexos) stored in `uploads/anexos/` directory
- 10MB file size limit enforced via custom middleware `LimitUploadSize` in `main.py`
- Upload directory auto-created on startup (`UPLOAD_DIR.mkdir(parents=True, exist_ok=True)`)

**CORS Configuration:**
- Explicit allowed origins list in `app/main.py` (lines 68-74)
- CORS middleware manually added to error responses in exception middleware
- Configured for production domains + local development ports

**Audit Logging:**
- Audit logs track changes to patrimonios via `app/models/log_auditoria.py`
- Log utilities in `app/utils/logs.py` provide helper functions

## Development Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (default port 8000)
uvicorn app.main:app --reload

# Run on custom port
uvicorn app.main:app --reload --port 9091
```

### Docker

```bash
# Build image
docker build -t controlhs-api .

# Run with environment variables
docker run -d \
  --name controlhs-api \
  -p 9091:9091 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your_secret_key \
  -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
  controlhs-api

# Run with docker-compose (includes Traefik)
docker-compose up -d
```

### Database

**No migration tool is currently configured.** Database schema is defined via SQLAlchemy models but there's no Alembic setup. Schema changes require manual SQL or recreation.

**Required environment variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)

## API Documentation

FastAPI auto-generates interactive docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main API Modules

| Module | File | Purpose |
|--------|------|---------|
| Authentication | `api/auth.py` | User registration, login, JWT tokens |
| Patrimonios | `api/patrimonios.py` | Asset CRUD operations |
| Categorias | `api/categorias.py` | Asset categories |
| Setores | `api/setores.py` | Departments/sectors |
| Transferencias | `api/transferencias.py` | Asset transfers between sectors |
| Baixas | `api/baixas.py` | Asset write-offs/disposals |
| Inventarios | `api/inventarios.py` | Inventory management |
| Anexos | `api/anexos.py` | File attachments for assets |
| Logs | `api/logs_auditoria.py` | Audit trail queries |

## Important Notes

**Models-Schemas Naming:**
- Models (`app/models/`) define database tables (SQLAlchemy)
- Schemas (`app/schemas/`) define API contracts (Pydantic)
- Naming generally matches: `models/patrimonio.py` ↔ `schemas/patrimonio.py`

**Role-Based Access:**
- Users have `role_id` referencing `roles` table
- Role names used in JWT tokens (e.g., "Admin", "Usuário")
- Role model defined in `app/models/role.py`

**Middleware Chain (order matters):**
1. `LimitUploadSize` - File upload size limits
2. CORS middleware - Cross-origin handling
3. `catch_exceptions_middleware` - Global error handler with CORS headers
4. `log_requests` - Request/response logging

**Production Deployment:**
- Runs on port 9091 (not default 8000)
- Uses Gunicorn with Uvicorn workers (`CMD` in Dockerfile)
- Traefik handles HTTPS/SSL termination
- Configured for domain: `authapi.seudominio.com`
