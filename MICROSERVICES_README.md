# GenovaAI Microservices Architecture

## Overview

This document describes the microservices architecture for the GenovaAI DNA Analysis Platform. The application has been decomposed into 6 independent services plus a frontend API gateway.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend Service                                │
│                            (API Gateway :8080)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────┬───────────────┼───────────────┬─────────────┐
         │             │               │               │             │
         ▼             ▼               ▼               ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Auth     │ │  Analysis   │ │ Prediction  │ │     AI      │ │    Agent    │
│   Service   │ │   Service   │ │   Service   │ │   Service   │ │   Service   │
│   (:5001)   │ │   (:5002)   │ │   (:5003)   │ │   (:5004)   │ │   (:5005)   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
         │             │               │               │             │
         └─────────────┴───────────────┼───────────────┴─────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │       PostgreSQL        │
                          │         (:5432)         │
                          └─────────────────────────┘
```

## Services

### 1. Auth Service (Port 5001)
**Purpose**: User authentication and authorization

**Endpoints**:
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/validate` - Validate JWT token
- `GET /health` - Health check

### 2. Analysis Service (Port 5002)
**Purpose**: SNP analysis, file processing, and history management

**Endpoints**:
- `POST /api/upload/vcf` - Upload VCF/CSV/PED files
- `POST /api/analysis/start` - Start SNP analysis
- `GET /api/analysis/<id>` - Get analysis results
- `GET /api/history` - Get analysis history
- `GET /api/snp/*` - SNP database queries
- `GET /health` - Health check

### 3. Prediction Service (Port 5003)
**Purpose**: Machine learning predictions for gender and ancestry

**Endpoints**:
- `POST /api/predictions/gender` - Predict gender from SNPs
- `POST /api/predictions/ancestry` - Predict ancestry/region
- `POST /api/predictions/combined` - Combined prediction
- `GET /api/predictions/samples` - Sample analysis results
- `GET /health` - Health check

### 4. AI Service (Port 5004)
**Purpose**: Gemini AI integration for genetic interpretations

**Endpoints**:
- `POST /api/ai/physical` - Physical characteristics analysis
- `POST /api/ai/disease-risk` - Disease risk assessment
- `POST /api/ai/chat` - AI chat conversation
- `POST /api/ai/interpret-snp` - SNP interpretation
- `GET /health` - Health check

### 5. Agent Service (Port 5005)
**Purpose**: LangGraph-based DNA analysis conversational agent

**Endpoints**:
- `POST /api/agent/chat` - Chat with DNA agent
- `GET /api/agent/session/<id>` - Get session details
- `DELETE /api/agent/session/<id>` - Delete session
- `POST /api/agent/quick/*` - Quick analysis actions
- `GET /health` - Health check

### 6. Frontend Service (Port 8080)
**Purpose**: Web UI and API Gateway

**Features**:
- Serves HTML templates and static assets
- Routes API requests to backend services
- Session management
- User authentication state

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Gemini API Key (for AI/Agent services)

### 1. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_api_key_here
```

### 2. Build Images
```bash
# Windows PowerShell
.\scripts\build-microservices.ps1

# Linux/Mac
chmod +x scripts/build-microservices.sh
./scripts/build-microservices.sh
```

### 3. Start Services
```bash
# Start all services
docker-compose -f docker-compose.microservices.yml up -d

# View logs
docker-compose -f docker-compose.microservices.yml logs -f

# Stop services
docker-compose -f docker-compose.microservices.yml down
```

### 4. Access Application
- **Web UI**: http://localhost:8080
- **Auth API**: http://localhost:5001
- **Analysis API**: http://localhost:5002
- **Prediction API**: http://localhost:5003
- **AI API**: http://localhost:5004
- **Agent API**: http://localhost:5005

## Development

### Building Individual Services
```bash
# Windows
.\scripts\build-microservices.ps1 -Service auth

# Linux/Mac
./scripts/build-microservices.sh auth
```

### Service Directory Structure
```
services/
├── auth-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── routes/
│       └── auth_routes.py
├── analysis-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── routes/
│       ├── analysis_routes.py
│       ├── history_routes.py
│       ├── upload_routes.py
│       └── snp_routes.py
├── prediction-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── models/
│   └── routes/
│       └── prediction_routes.py
├── ai-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── routes/
│       └── ai_routes.py
├── agent-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── agent/
│   └── routes/
│       └── agent_routes.py
├── frontend-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/
│   └── static/
└── shared/
    └── database/
        ├── __init__.py
        └── models.py
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes (for AI/Agent) |
| `FLASK_SECRET_KEY` | Flask session secret | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured |

## Health Checks

All services expose a `/health` endpoint that returns:
```json
{
  "status": "healthy",
  "service": "service-name",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Scaling

Each service can be scaled independently:
```bash
# Scale prediction service to 3 replicas
docker-compose -f docker-compose.microservices.yml up -d --scale prediction-service=3
```

## Monitoring

View service status:
```bash
# All services
docker-compose -f docker-compose.microservices.yml ps

# Service logs
docker-compose -f docker-compose.microservices.yml logs -f [service-name]

# Frontend status endpoint
curl http://localhost:8080/api/status
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Ensure PostgreSQL is healthy: `docker-compose logs postgres`
   - Check DATABASE_URL environment variable

2. **Service not starting**
   - Check logs: `docker-compose logs [service-name]`
   - Verify required environment variables

3. **AI/Agent not working**
   - Verify GEMINI_API_KEY is set correctly
   - Check API quota on Google Cloud Console

## Migration from Monolith

The microservices architecture maintains backward compatibility:
- All API endpoints remain the same
- Database schema unchanged
- Frontend templates unchanged

The main difference is that requests are now routed through the API Gateway (Frontend Service) to appropriate backend services.
