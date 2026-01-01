# Crop Risk Prediction Platform

AI-powered full-stack platform for agricultural risk management in Rwanda and East Africa.

## 📦 Project Structure

```
crop-risk-backend/
├── app/                    # FastAPI backend application
│   ├── api/               # API endpoints
│   ├── core/              # Auth, config
│   ├── db/                # Database setup
│   ├── ml/                # Machine learning models
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── tasks/             # Celery tasks (auto-processing)
│   └── utils/             # Utilities
├── frontend/              # React frontend application
│   ├── public/
│   └── src/
│       ├── components/    # React components
│       ├── pages/         # Page components
│       └── api.js         # API client
├── data/                  # Satellite imagery data
├── scripts/               # Data processing scripts
├── migrations/            # Alembic database migrations
└── docker-compose.yml     # Docker orchestration

```

## 🌟 Features

- **Automated Satellite Image Processing**: Celery-based auto-processing with NDVI computation
- **Real-time Monitoring**: Dashboard with crop health visualization
- **Scalable Architecture**: PostgreSQL + Redis + Celery worker pool
- **REST API**: FastAPI backend with authentication
- **Modern UI**: React frontend with responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

Alternatively you can run the entire stack with Docker (recommended for reproducible deployments).

### Installation

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Setup database:
```bash
# In pgAdmin or psql, create database:
CREATE DATABASE crop_risk_db;
```

4. Configure environment:
```bash
# Update .env file with your actual values
# Especially DATABASE_PASSWORD and SECRET_KEY
```

5. Run locally (development):
```bash
python main.py
```

6. Or using Docker (recommended):
```bash
# build and start the app and a local Postgres instance
make up

# view logs
make logs

# stop
make down
```

API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
crop-risk-backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configs
│   ├── db/              # Database
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── ml/              # ML models & pipelines
│   └── utils/           # Utilities
├── tests/               # Tests
├── scripts/             # Helper scripts
├── data/                # Data storage
├── logs/                # Logs
└── migrations/          # Alembic migrations
```

## 🛠️ Development

Run tests:
```bash
pytest
```

Format code:
```bash
black .
isort .
```

## 📚 API Endpoints

- /api/v1/predictions - Crop risk predictions
- /api/v1/farms - Farm management
- /api/v1/users - User management
- /api/v1/alerts - Alert system

## 🔧 Technologies

- FastAPI - Web framework
- PostgreSQL + PostGIS - Database
- Redis - Caching
- SQLAlchemy - ORM
- Celery - Background tasks
- XGBoost/LightGBM - ML models
