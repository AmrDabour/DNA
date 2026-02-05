# Genetic Prediction System (GenovaAI)

A Flask-based web application for genetic predictions using machine learning models. The system can predict gender and ancestry based on genetic data, and uses Google's Gemini AI to generate predictions about physical characteristics and disease risks.

## Features

- Gender and ancestry prediction based on genetic data
- Physical characteristics prediction using Google Gemini AI
- Genetic disease risk assessment
- Support for sample data analysis and visualization
- Admin dashboard for user and system management
- Celery-based task queue for async processing

---

## 🐳 Running with Docker Compose (Recommended)

### Prerequisites

1. **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
   - Windows/Mac: Docker Desktop
   - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)

2. **Verify Installation**:
   ```bash
   docker --version
   docker compose version
   ```

### Quick Start

```bash
# 1. Clone the repository (if not already done)
git clone https://github.com/AmrDabour/DNA.git
cd DNA

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env and configure your settings
# At minimum, set your GEMINI_API_KEY
# You can also customize database passwords and other settings

# 4. Start all services
docker compose up -d

# 5. Wait for services to be healthy (usually 1-2 minutes)
docker compose ps

# 6. Access the application
# Open http://localhost:8080 in your browser
```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Required - Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secure_secret_key_here

# PostgreSQL Database
POSTGRES_DB=genovaai
POSTGRES_USER=genovaai_user
POSTGRES_PASSWORD=your_secure_postgres_password

# MongoDB Database
MONGO_DB=genovaai
MONGO_USER=genovaai_mongo_user
MONGO_PASSWORD=your_secure_mongo_password

# RabbitMQ Message Broker
RABBITMQ_USER=genovaai
RABBITMQ_PASSWORD=your_secure_rabbitmq_password

# Admin Account
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_secure_admin_password

# Flower Monitoring (Optional)
FLOWER_USER=admin
FLOWER_PASSWORD=your_flower_password

# LangSmith Tracing (Optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=genovaai-production
```

### Service Ports

| Service       | Port  | URL/Access                          |
|---------------|-------|-------------------------------------|
| Web App       | 8080  | http://localhost:8080               |
| API (Direct)  | 5001  | http://localhost:5001               |
| PostgreSQL    | 5432  | `localhost:5432`                    |
| MongoDB       | 27017 | `localhost:27017`                   |
| Redis         | 6379  | `localhost:6379`                    |
| RabbitMQ      | 5672  | `localhost:5672`                    |
| RabbitMQ UI   | 15672 | http://localhost:15672              |
| Flower        | 5555  | http://localhost:5555               |

### Docker Compose Commands

```bash
# Start all services in background
docker compose up -d

# Start and rebuild images
docker compose up -d --build

# View running containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs for specific service
docker compose logs -f genovaai

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: Deletes all data!)
docker compose down -v

# Restart a specific service
docker compose restart genovaai

# Execute command in running container
docker compose exec genovaai bash

# Scale Celery workers
docker compose up -d --scale celery-worker=3
```

### Health Checks

```bash
# Check if all services are healthy
docker compose ps

# Check individual service health
docker inspect genovaai-app --format='{{.State.Health.Status}}'

# View service logs if unhealthy
docker compose logs genovaai
```

### Troubleshooting

1. **Services not starting**: Check logs with `docker compose logs -f`

2. **Database connection errors**: Ensure PostgreSQL/MongoDB are healthy:
   ```bash
   docker compose ps postgres mongodb
   ```

3. **Port conflicts**: If ports are in use, modify them in `docker-compose.yml` or stop conflicting services

4. **Memory issues**: Increase Docker memory allocation in Docker Desktop settings

5. **Permission issues** (Linux): Add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

6. **Rebuild containers** after code changes:
   ```bash
   docker compose up -d --build
   ```

---

## 💻 Local Development Setup

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Secret Key - Used for session encryption
FLASK_SECRET_KEY=your_secure_flask_secret_key_here

# Google Gemini API Key
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
DEBUG=True
PORT=5001
```

### Installing Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install required packages
pip install -r requirements.txt
```

### Running the Application

1. Make sure you've set up the `.env` file with your Google Gemini API key
2. Start the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to: http://localhost:5001

---

## ☸️ Running on Kubernetes

### Local Development (Docker Desktop / Minikube)

```bash
# 1. Copy and edit the secrets file (one time only)
cp kubernetes-manifests/k8s.env.example kubernetes-manifests/k8s.env
# Edit k8s.env and add your GEMINI_API_KEY

# 2. Deploy! (reads from k8s.env automatically)
kubectl apply -k kubernetes-manifests/

# 3. Access the application
kubectl port-forward -n genovaai svc/genovaai 5000:5000
# Open: http://localhost:5000
```

### Production (GKE / Cloud)

1. Add secrets to GitHub Repository Settings → Secrets → Actions
2. Run the "Deploy to Kubernetes" workflow

For more details, see [kubernetes-manifests/SECRETS_MANAGEMENT.md](kubernetes-manifests/SECRETS_MANAGEMENT.md)

---

## 📝 Important Notes

- The AI-based predictions (physical characteristics and disease risks) require a valid Google Gemini API key
- The predictions are based on statistical correlations and should not be used for medical diagnosis
- Sample data must be properly formatted (see documentation)

---

## 📂 Project Structure

```
DNA/
├── agent/              # AI agent components
├── config/             # Configuration files
├── database/           # Database models and migrations
├── kubernetes-manifests/ # K8s deployment files
├── ml_models/          # Machine learning models
├── nginx/              # Nginx configuration
├── routes/             # API route handlers
├── scripts/            # Utility scripts
├── services/           # Business logic services
├── tasks/              # Celery async tasks
├── tests/              # Test suite
├── web/                # Frontend templates and static files
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Container build instructions
└── requirements.txt    # Python dependencies
```

---

## 📄 License

This project is proprietary software.