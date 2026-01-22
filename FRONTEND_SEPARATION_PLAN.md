# Frontend Separation Plan - GenovaAI Microservices Architecture

## Current Architecture (Monolith)

```
┌─────────────────────────────────────────┐
│           Flask Application             │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  Templates  │  │   API Routes    │   │
│  │  (Jinja2)   │  │   (JSON API)    │   │
│  └─────────────┘  └─────────────────┘   │
│           ↓               ↓             │
│      HTML Pages      JSON Responses     │
└─────────────────────────────────────────┘
              ↓
    ┌─────────────────┐  ┌─────────────────┐
    │   PostgreSQL    │  │    MongoDB      │
    │   (Users/Auth)  │  │   (SNP Data)    │
    └─────────────────┘  └─────────────────┘
```

## Target Architecture (Microservices)

```
                    ┌─────────────────────┐
                    │      Nginx          │
                    │  (Reverse Proxy)    │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│     Frontend     │ │     Backend      │ │     Database     │
│   (React/Next)   │ │   (Flask API)    │ │                  │
│                  │ │                  │ │  ┌────────────┐  │
│  - Static Files  │ │  - REST API      │ │  │ PostgreSQL │  │
│  - SPA           │ │  - Auth          │ │  └────────────┘  │
│  - API Calls     │ │  - Business      │ │  ┌────────────┐  │
│                  │ │    Logic         │ │  │  MongoDB   │  │
│  Port: 3000      │ │  Port: 5001      │ │  └────────────┘  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Project Structure

```
genovaai/
├── frontend/                    # NEW - React/Next.js app
│   ├── src/
│   │   ├── app/                 # Next.js 14 App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Home
│   │   │   ├── dashboard/
│   │   │   ├── upload/
│   │   │   ├── samples/
│   │   │   ├── predictions/
│   │   │   ├── snp-database/
│   │   │   ├── risk-calculator/
│   │   │   ├── chat/
│   │   │   └── auth/
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   ├── layout/          # Navbar, Footer, Sidebar
│   │   │   └── features/        # Feature-specific components
│   │   ├── lib/
│   │   │   ├── api.ts           # API client
│   │   │   └── auth.ts          # Auth utilities
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   │   └── animations/
│   ├── Dockerfile
│   ├── package.json
│   └── next.config.js
│
├── backend/                     # RENAMED from root
│   ├── routes/                  # API routes only
│   ├── services/
│   ├── models/
│   ├── config/
│   ├── database/
│   ├── scripts/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml           # Updated
├── nginx/
│   └── nginx.conf               # Reverse proxy config
└── README.md
```

## Implementation Steps

### Phase 1: Setup Frontend Project

1. Create Next.js 14 app with TypeScript
2. Install dependencies:
   - Tailwind CSS for styling
   - Framer Motion for animations
   - Axios/fetch for API calls
   - NextAuth.js for authentication
   - Zustand for state management

### Phase 2: Build Core Components

1. **Layout Components:**
   - Navbar (with auth state)
   - Footer
   - Sidebar
   - Loading states

2. **UI Components:**
   - Cards
   - Buttons
   - Modals
   - Tables
   - Charts

### Phase 3: Convert Pages

| Jinja2 Template | React Page |
|-----------------|------------|
| index.html | app/page.tsx |
| dashboard.html | app/dashboard/page.tsx |
| upload.html | app/upload/page.tsx |
| samples.html | app/samples/page.tsx |
| prediction_results.html | app/predictions/[id]/page.tsx |
| snp_database.html | app/snp-database/page.tsx |
| risk_calculator.html | app/risk-calculator/page.tsx |
| chat.html | app/chat/page.tsx |
| history.html | app/history/page.tsx |
| auth/login.html | app/auth/login/page.tsx |
| auth/register.html | app/auth/register/page.tsx |
| auth/profile.html | app/auth/profile/page.tsx |

### Phase 4: Backend API Refactoring

1. Remove template rendering from Flask routes
2. Ensure all routes return JSON only
3. Add CORS configuration for frontend
4. Create standardized API response format:

```python
{
    "success": true,
    "data": {...},
    "message": "Operation successful",
    "error": null
}
```

### Phase 5: Docker & Deployment

1. Frontend Dockerfile (multi-stage build)
2. Update docker-compose.yml
3. Add Nginx reverse proxy
4. Configure environment variables

## Docker Compose Structure

```yaml
services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - frontend
      - backend

  # Frontend Service
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:5001

  # Backend API Service
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=...
      - MONGO_URI=...

  # Databases
  postgres:
    image: postgres:15-alpine

  mongodb:
    image: mongo:7.0
```

## API Endpoints Reference

### Authentication
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/logout
- GET /api/auth/me

### Predictions
- POST /api/predict/upload
- GET /api/predict/results/:id
- GET /api/predict/history

### SNP Database
- GET /api/snp/search
- GET /api/snp/:rs_id
- GET /api/snp/stats
- GET /api/snp/chromosomes
- GET /api/snp/genes

### Risk Calculator
- POST /api/risk/calculate
- GET /api/risk/diseases

### Samples
- GET /api/samples
- POST /api/samples
- GET /api/samples/:id

## Technology Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand
- **Charts:** Recharts
- **Animations:** Framer Motion
- **Auth:** NextAuth.js

### Backend
- **Framework:** Flask
- **Language:** Python 3.11
- **Database:** PostgreSQL + MongoDB
- **Auth:** Flask-Login + JWT

## Timeline Estimate

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1 | 1 day | Frontend setup, dependencies |
| Phase 2 | 2 days | Core components |
| Phase 3 | 3 days | Page conversions |
| Phase 4 | 1 day | Backend refactoring |
| Phase 5 | 1 day | Docker & deployment |

**Total: ~8 days**

## Next Steps

1. Create frontend directory and initialize Next.js
2. Build base layout and navigation
3. Start converting pages one by one
4. Test API integration
5. Update Docker setup

