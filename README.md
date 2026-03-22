# Adhesive ERP - Industrial ERP System

A comprehensive Enterprise Resource Planning (ERP) system built for the adhesive tapes industry, featuring fully customizable forms, comprehensive inventory management, and sophisticated multi-stage production modules.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Frontend**: React with Vite
- **Authentication**: JWT-based authentication

## Architecture

The application follows a **layered architecture**:

```
/app/backend/
├── api/v1/           # API Routes (FastAPI routers)
├── services/         # Business Logic Layer
├── repositories/     # Data Access Layer (Repository pattern)
├── models/
│   ├── entities/     # SQLAlchemy ORM models
│   └── schemas/      # Pydantic schemas
├── core/             # Core utilities (config, database, security)
│   ├── database.py   # PostgreSQL connection management
│   ├── config.py     # Application settings
│   ├── security.py   # Authentication utilities
│   └── legacy_db.py  # MongoDB-compatibility layer for legacy routes
└── routes/           # Legacy API routes (being migrated)
```

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+
- npm/yarn

## Local Development Setup

### 1. Database Setup

```bash
# Install PostgreSQL
sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo service postgresql start

# Create database and user
sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'erp_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE adhesive_erp OWNER erp_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE adhesive_erp TO erp_user;"
```

### 2. Backend Setup

```bash
cd /app/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL

# Run migrations (tables are auto-created on startup)
# Start the server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 3. Frontend Setup

```bash
cd /app/frontend

# Install dependencies
yarn install

# Start development server
yarn dev
```

## Environment Variables

### Backend (.env)

```env
# PostgreSQL Connection (required)
DATABASE_URL=postgresql+asyncpg://erp_user:erp_secure_password@localhost:5432/adhesive_erp

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=*

# Optional - AI Features
EMERGENT_LLM_KEY=sk-your-key
```

### Frontend (.env)

```env
VITE_BACKEND_URL=http://localhost:8001
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Key Modules

1. **CRM** - Lead management, accounts, quotations, samples
2. **Inventory** - Item master, warehouses, stock management, batches
3. **Production** - Order sheets, work orders, 7-stage workflow
4. **Procurement** - Suppliers, purchase orders, GRN
5. **Accounts** - Invoices, payments, ledgers, GST compliance
6. **HRMS** - Employees, attendance, payroll, leaves
7. **Quality** - QC inspections, customer complaints, TDS
8. **Sales Incentives** - Targets, slabs, payouts

## Database Schema

All database models are defined in `/app/backend/models/entities/`. The schema uses:
- **UUID** primary keys for all tables
- **JSONB** columns for flexible/custom fields
- Proper **foreign keys** and **indexes** for performance
- Automatic **timestamps** (created_at, updated_at) on all tables

## Migration from MongoDB

This project was migrated from MongoDB to PostgreSQL. The `core/legacy_db.py` module provides a compatibility layer that allows legacy routes (in `/routes/`) to continue working with MongoDB-like syntax while using PostgreSQL under the hood.

New code should use:
- Services in `/services/` for business logic
- Repositories in `/repositories/` for data access
- API routes in `/api/v1/` for endpoints

## Testing

```bash
# Run backend tests
cd /app/backend
pytest tests/

# Run frontend tests
cd /app/frontend
yarn test
```

## Production Deployment

1. Set secure values for all environment variables
2. Use a proper PostgreSQL instance (not local)
3. Configure CORS_ORIGINS properly
4. Enable SSL/TLS for database connections
5. Set up proper logging and monitoring

## License

Proprietary - All rights reserved
