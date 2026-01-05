# 🚀 GenovaAI Database Migration Plan: SQLite → PostgreSQL

## Executive Summary

This document outlines the complete migration strategy from SQLite to PostgreSQL (postgres:15-alpine) to make GenovaAI production-ready and microservices-compatible.

---

## 📊 Current State Analysis

### Current Database Configuration
- **Database**: SQLite (file-based: `genovaai.db`)
- **ORM**: SQLAlchemy 2.0.38
- **Location**: `instance/genovaai.db` (via Docker volume)
- **Connection**: `sqlite:///genovaai.db`

### Existing Tables (5 tables)
| Table | Purpose | Records Expected |
|-------|---------|------------------|
| `users` | User authentication & profiles | Low |
| `analysis_history` | DNA analysis results & history | High |
| `snp_info` | SNP database information | Very High |
| `notifications` | User notification system | Medium |
| `genetic_risk_profiles` | Risk calculation results | Medium |

### Current Issues with SQLite for Production
1. ❌ No concurrent write support (file-level locking)
2. ❌ Not suitable for multi-container/replicated deployments
3. ❌ No native JSON column support
4. ❌ Limited scalability
5. ❌ No connection pooling
6. ❌ Not microservices-friendly

---

## 🎯 Target Architecture

### PostgreSQL 15 Alpine Benefits
- ✅ ACID compliant with concurrent writes
- ✅ Native JSONB support for complex data
- ✅ Connection pooling ready
- ✅ Horizontal scaling support
- ✅ Kubernetes StatefulSet compatible
- ✅ Proper indexing and query optimization
- ✅ Full-text search capabilities
- ✅ Microservices architecture ready

---

## 📋 Migration Phases

### Phase 1: Infrastructure Setup (Week 1)
| Task | Description | Priority |
|------|-------------|----------|
| 1.1 | Create PostgreSQL Docker service | HIGH |
| 1.2 | Set up persistent volumes | HIGH |
| 1.3 | Configure networking | HIGH |
| 1.4 | Create health checks | MEDIUM |

### Phase 2: Code Updates (Week 1-2)
| Task | Description | Priority |
|------|-------------|----------|
| 2.1 | Update requirements.txt with psycopg2 | HIGH |
| 2.2 | Modify database connection strings | HIGH |
| 2.3 | Add Alembic for migrations | HIGH |
| 2.4 | Update model definitions for PostgreSQL | MEDIUM |

### Phase 3: Data Migration (Week 2)
| Task | Description | Priority |
|------|-------------|----------|
| 3.1 | Create migration scripts | HIGH |
| 3.2 | Test data integrity | HIGH |
| 3.3 | Validate foreign key relationships | MEDIUM |

### Phase 4: Kubernetes Preparation (Week 3)
| Task | Description | Priority |
|------|-------------|----------|
| 4.1 | Create K8s ConfigMaps/Secrets | HIGH |
| 4.2 | Create PostgreSQL StatefulSet | HIGH |
| 4.3 | Create application Deployment | HIGH |
| 4.4 | Set up Ingress/Services | MEDIUM |

---

## 📁 New File Structure

```
DNA/
├── docker-compose.yml          # Updated with PostgreSQL
├── docker-compose.dev.yml      # Development override
├── docker-compose.prod.yml     # Production override
│
├── database/
│   ├── __init__.py             # Updated exports
│   ├── models.py               # Updated for PostgreSQL
│   ├── migrations/             # Alembic migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── alembic.ini
│   └── init_scripts/
│       └── 01_init.sql         # PostgreSQL init
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # Environment-based config
│   └── database.py             # Database configuration
│
├── kubernetes/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── postgres/
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── app/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
│
└── scripts/
    ├── migrate_sqlite_to_postgres.py
    ├── backup_postgres.sh
    └── health_check.py
```

---

## 🔧 Configuration Changes

### Environment Variables (New)
```bash
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=genovaai
POSTGRES_USER=genovaai_user
POSTGRES_PASSWORD=<secure_password>

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Production Settings
DATABASE_URL=postgresql://genovaai_user:<password>@postgres:5432/genovaai
```

### Connection String Changes
| Environment | Old (SQLite) | New (PostgreSQL) |
|-------------|--------------|------------------|
| Development | `sqlite:///genovaai.db` | `postgresql://user:pass@localhost:5432/genovaai_dev` |
| Production | `sqlite:///genovaai.db` | `postgresql://user:pass@postgres:5432/genovaai` |
| Testing | `sqlite:///:memory:` | `postgresql://user:pass@localhost:5432/genovaai_test` |

---

## 🐳 Docker Compose Updates

### Services Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (genovaai-network)        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │   genovaai-app  │─────▶│   PostgreSQL    │               │
│  │   (Flask App)   │      │   (postgres:15) │               │
│  │   Port: 5001    │      │   Port: 5432    │               │
│  └─────────────────┘      └─────────────────┘               │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │    Volumes:     │      │    Volumes:     │               │
│  │  - uploads      │      │  - pg-data      │               │
│  │  - results      │      │  - pg-backups   │               │
│  └─────────────────┘      └─────────────────┘               │
│                                                             │
│  ┌─────────────────┐  (Future)                              │
│  │     Redis       │                                        │
│  │   Port: 6379    │                                        │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ☸️ Kubernetes Architecture (Microservices Ready)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                            │
│                     Namespace: genovaai-prod                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        Ingress Controller                     │   │
│  │                    (NGINX / Traefik / Cloud LB)              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│              ┌───────────────┴───────────────┐                      │
│              ▼                               ▼                       │
│  ┌─────────────────────┐      ┌─────────────────────┐              │
│  │  GenovaAI Service   │      │   API Gateway       │              │
│  │  (ClusterIP)        │      │   (Future)          │              │
│  └─────────────────────┘      └─────────────────────┘              │
│              │                                                       │
│              ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    GenovaAI Deployment                       │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  (HPA: 2-10 replicas)│    │
│  │  │ Pod 1   │  │ Pod 2   │  │ Pod N   │                      │    │
│  │  │ (Flask) │  │ (Flask) │  │ (Flask) │                      │    │
│  │  └─────────┘  └─────────┘  └─────────┘                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│              │                                                       │
│              ▼                                                       │
│  ┌─────────────────────┐      ┌─────────────────────┐              │
│  │  PostgreSQL Service │      │  Redis Service      │              │
│  │  (ClusterIP)        │      │  (ClusterIP)        │              │
│  └─────────────────────┘      └─────────────────────┘              │
│              │                        │                              │
│              ▼                        ▼                              │
│  ┌─────────────────────┐      ┌─────────────────────┐              │
│  │  PostgreSQL         │      │  Redis              │              │
│  │  StatefulSet        │      │  StatefulSet        │              │
│  │  (1 replica + PVC)  │      │  (1 replica + PVC)  │              │
│  └─────────────────────┘      └─────────────────────┘              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Persistent Volume Claims                   │   │
│  │  • postgres-data-pvc (10Gi)                                  │   │
│  │  • redis-data-pvc (1Gi)                                      │   │
│  │  • uploads-pvc (50Gi)                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Model Changes Required

### PostgreSQL-Specific Optimizations

```python
# Before (SQLite)
full_results = db.Column(db.Text)  # JSON as text

# After (PostgreSQL)
from sqlalchemy.dialects.postgresql import JSONB
full_results = db.Column(JSONB)  # Native JSON support
```

### Index Improvements
```python
# Add GIN indexes for JSONB columns
Index('idx_full_results_gin', AnalysisHistory.full_results, postgresql_using='gin')

# Add partial indexes
Index('idx_active_users', User.id, postgresql_where=User.is_active == True)
```

---

## 🔄 Migration Script Overview

```python
# scripts/migrate_sqlite_to_postgres.py
"""
Migration steps:
1. Export SQLite data to JSON
2. Create PostgreSQL schema
3. Import data with transformations
4. Validate data integrity
5. Update sequences
"""
```

---

## ✅ Pre-Migration Checklist

- [ ] Backup current SQLite database
- [ ] Document current data volume
- [ ] Test PostgreSQL connection locally
- [ ] Verify all models work with PostgreSQL
- [ ] Test Alembic migrations
- [ ] Prepare rollback plan

---

## 🚨 Rollback Plan

1. **Docker Compose**: Keep `docker-compose.sqlite.yml` backup
2. **Data**: Daily backups to external storage
3. **Code**: Feature branch for migration changes
4. **Quick Switch**: Environment variable to switch DB backend

---

## 📅 Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Infrastructure | PostgreSQL container, configs, health checks |
| 1-2 | Code Updates | Updated models, Alembic, connection handling |
| 2 | Data Migration | Migration scripts, data validation |
| 3 | Kubernetes | K8s manifests, secrets, deployments |
| 4 | Testing & Go-Live | Load testing, production deployment |

---

## 🔜 Next Steps

1. **Approve this plan** and proceed with implementation
2. **Create PostgreSQL Docker configuration**
3. **Update application code for PostgreSQL**
4. **Set up Alembic migrations**
5. **Create Kubernetes manifests**

Ready to proceed? Let me know which phase to start implementing!
