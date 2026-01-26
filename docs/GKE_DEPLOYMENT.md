# GenovaAI - GKE Autopilot Deployment Guide

This guide covers deploying GenovaAI to Google Kubernetes Engine (GKE) Autopilot.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Manual Deployment](#manual-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required Tools

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Install kubectl
gcloud components install kubectl

# Install gke-gcloud-auth-plugin
gcloud components install gke-gcloud-auth-plugin

# Install Terraform
# https://www.terraform.io/downloads

# Install Docker (for local testing)
# https://docs.docker.com/get-docker/
```

### GCP Setup

1. **Create/Select GCP Project**
   ```bash
   gcloud projects create genovaai-prod --name="GenovaAI Production"
   gcloud config set project genovaai-prod
   ```

2. **Enable Billing**
   - Go to GCP Console → Billing → Link a billing account

3. **Enable Required APIs**
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable cloudtrace.googleapis.com
   gcloud services enable cloudprofiler.googleapis.com
   ```

4. **Create Service Account for CI/CD**
   ```bash
   # Create service account
   gcloud iam service-accounts create genovaai-cicd \
     --display-name="GenovaAI CI/CD Service Account"

   # Grant required roles
   gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
     --member="serviceAccount:genovaai-cicd@$(gcloud config get-value project).iam.gserviceaccount.com" \
     --role="roles/container.admin"

   gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
     --member="serviceAccount:genovaai-cicd@$(gcloud config get-value project).iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"

   # Create and download key
   gcloud iam service-accounts keys create gcp-sa-key.json \
     --iam-account=genovaai-cicd@$(gcloud config get-value project).iam.gserviceaccount.com
   ```

## Architecture Overview

```
                                    ┌─────────────────────────────────────────────────────────┐
                                    │                    GKE Autopilot Cluster                 │
                                    │                                                          │
        Internet                    │   ┌──────────────────────────────────────────────────┐  │
            │                       │   │              Nginx LoadBalancer (External IP)     │  │
            │                       │   └──────────────────────────────────────────────────┘  │
            ▼                       │                            │                             │
    ┌───────────────┐               │        ┌───────────────────┼───────────────────┐        │
    │  LoadBalancer │───────────────│────────▶                   │                   │        │
    └───────────────┘               │        │     ┌─────────────┴─────────────┐     │        │
                                    │        │     │                           │     │        │
                                    │        ▼     ▼                           ▼     │        │
                                    │   ┌─────────────┐    ┌──────────────┐   ┌───────────┐   │
                                    │   │  GenovaAI   │    │ Celery Worker│   │  Flower   │   │
                                    │   │  (Flask)    │    │   (x2)       │   │           │   │
                                    │   │   (x2)      │    └──────────────┘   └───────────┘   │
                                    │   └─────────────┘           │                           │
                                    │         │                   │                           │
                                    │         │        ┌──────────┴──────────┐                │
                                    │         │        │                     │                │
                                    │         ▼        ▼                     ▼                │
                                    │   ┌─────────────────┐          ┌─────────────┐          │
                                    │   │    RabbitMQ     │          │ Celery Beat │          │
                                    │   │  (StatefulSet)  │          │             │          │
                                    │   └─────────────────┘          └─────────────┘          │
                                    │                                                          │
                                    │   ┌─────────────┬─────────────┬─────────────┐           │
                                    │   │  PostgreSQL │   MongoDB   │    Redis    │           │
                                    │   │(StatefulSet)│(StatefulSet)│(StatefulSet)│           │
                                    │   └─────────────┴─────────────┴─────────────┘           │
                                    │                                                          │
                                    │   ┌─────────────────────────────────────────┐           │
                                    │   │         Monitoring Stack                 │           │
                                    │   │   ┌───────────┐      ┌───────────┐      │           │
                                    │   │   │Prometheus │──────▶  Grafana  │      │           │
                                    │   │   └───────────┘      └───────────┘      │           │
                                    │   └─────────────────────────────────────────┘           │
                                    │                                                          │
                                    └──────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Using Terraform (Recommended)

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var="gcp_project_id=YOUR_PROJECT_ID"

# Apply (creates cluster and deploys everything)
terraform apply -var="gcp_project_id=YOUR_PROJECT_ID" -auto-approve
```

### Option 2: Using GitHub Actions

1. **Configure GitHub Secrets**:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: Base64 encoded service account JSON key
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password/token

2. **Run Terraform Workflow**:
   - Go to Actions → "Terraform Infrastructure" → Run workflow
   - Select `apply` action

3. **Deploy Application**:
   - Go to Actions → "Deploy to Kubernetes" → Run workflow

## Manual Deployment

### Step 1: Create GKE Cluster

```bash
# Create Autopilot cluster
gcloud container clusters create-auto genovaai-cluster \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID

# Get credentials
gcloud container clusters get-credentials genovaai-cluster \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID
```

### Step 2: Update Secrets

Edit `kubernetes-manifests/secrets-configmap.yaml` with your actual credentials:

```yaml
stringData:
  FLASK_SECRET_KEY: "your-secure-random-string"
  POSTGRES_PASSWORD: "your-postgres-password"
  MONGO_INITDB_ROOT_PASSWORD: "your-mongo-password"
  REDIS_PASSWORD: "your-redis-password"
  RABBITMQ_DEFAULT_PASS: "your-rabbitmq-password"
  GEMINI_API_KEY: "your-gemini-api-key"
```

### Step 3: Deploy with Kustomize

```bash
# Apply all manifests
kubectl apply -k kubernetes-manifests/

# Watch pods come up
kubectl get pods -n genovaai -w

# Get external IP
kubectl get svc nginx -n genovaai
```

### Step 4: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n genovaai

# Check services
kubectl get svc -n genovaai

# Check logs
kubectl logs -f deployment/genovaai -n genovaai

# Get the external IP
EXTERNAL_IP=$(kubectl get svc nginx -n genovaai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Application URL: http://$EXTERNAL_IP"
```

## CI/CD Pipeline

### Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-and-test.yml` | Push/PR to main | Run tests and lint |
| `build-push-images.yml` | Push to main | Build and push Docker image |
| `deploy-kubernetes.yml` | Manual | Deploy to GKE |
| `terraform.yml` | Manual/PR | Manage infrastructure |
| `security-scan.yml` | Push/PR/Schedule | Security scanning |

### Setting Up CI/CD

1. **Docker Hub Setup**:
   ```bash
   # Create repository on Docker Hub
   # Name: amrdabour/genovaai
   ```

2. **GitHub Secrets Required**:
   ```
   DOCKER_USERNAME     - Docker Hub username
   DOCKER_PASSWORD     - Docker Hub access token
   GCP_PROJECT_ID      - GCP project ID (e.g., saedny)
   GCP_SA_KEY          - Service account JSON (base64 encoded)
   ```

3. **Encode Service Account Key**:
   ```bash
   base64 -w 0 gcp-sa-key.json
   ```

## Monitoring

### Accessing Dashboards

Once deployed, access monitoring via the LoadBalancer IP:

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Application | `http://EXTERNAL_IP/` | - |
| Grafana | `http://EXTERNAL_IP/grafana/` | admin/admin |
| Prometheus | `http://EXTERNAL_IP/prometheus/` | - |
| Flower | `http://EXTERNAL_IP/flower/` | - |
| RabbitMQ | `http://EXTERNAL_IP/rabbitmq/` | See secrets |

### Key Metrics

- **Application**: HTTP request rate, response times, error rates
- **Celery**: Task queue depth, worker count, task success/failure
- **Databases**: Connection count, query latency, storage usage
- **Infrastructure**: Pod CPU/memory, network I/O

### Alerting (Optional)

Add alerting rules to Prometheus:

```yaml
# Add to prometheus.yaml ConfigMap
rule_files:
  - /etc/prometheus/alerts/*.yml

# Create alerts ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
data:
  alerts.yml: |
    groups:
      - name: genovaai
        rules:
          - alert: HighErrorRate
            expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
            for: 5m
            labels:
              severity: critical
```

## Troubleshooting

### Common Issues

**Pods stuck in Pending**
```bash
# Check events
kubectl describe pod <pod-name> -n genovaai

# GKE Autopilot may take time to scale nodes
kubectl get events -n genovaai --sort-by='.lastTimestamp'
```

**Database connection errors**
```bash
# Verify database pods are running
kubectl get pods -n genovaai -l app=postgres
kubectl get pods -n genovaai -l app=mongodb
kubectl get pods -n genovaai -l app=redis

# Check logs
kubectl logs statefulset/postgres -n genovaai
```

**Celery workers not connecting**
```bash
# Check RabbitMQ status
kubectl exec -it statefulset/rabbitmq -n genovaai -- rabbitmqctl status

# Check worker logs
kubectl logs deployment/celery-worker -n genovaai
```

**LoadBalancer IP not assigned**
```bash
# Check service status
kubectl describe svc nginx -n genovaai

# May take 2-5 minutes for GCP to provision
```

### Useful Commands

```bash
# Port-forward for local debugging
kubectl port-forward svc/genovaai 5000:5000 -n genovaai

# Shell into a pod
kubectl exec -it deployment/genovaai -n genovaai -- /bin/bash

# View all resources
kubectl get all -n genovaai

# Delete and recreate deployment
kubectl rollout restart deployment/genovaai -n genovaai
```

## Security Considerations

### Production Checklist

- [ ] Change all default passwords in `secrets-configmap.yaml`
- [ ] Use Kubernetes Secrets with external secret manager (e.g., GCP Secret Manager)
- [ ] Enable network policies for pod-to-pod traffic isolation
- [ ] Configure HTTPS with SSL certificates
- [ ] Enable GKE Workload Identity
- [ ] Review RBAC permissions
- [ ] Enable audit logging
- [ ] Set up backup for persistent volumes

### Using External Secrets (Recommended)

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n genovaai

# Configure GCP Secret Manager integration
# See: https://external-secrets.io/latest/provider/google-secrets-manager/
```

### Network Policies

```yaml
# Example: Restrict database access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-policy
  namespace: genovaai
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: genovaai
      ports:
        - port: 5432
```

## Cost Optimization

GKE Autopilot pricing is based on pod resource requests:

| Resource | Approximate Cost |
|----------|------------------|
| vCPU | ~$0.04/hour |
| Memory | ~$0.004/GB/hour |
| Storage (PD) | ~$0.04/GB/month |

### Tips to Reduce Costs

1. Right-size resource requests
2. Use preemptible/spot pods for workers
3. Enable cluster autoscaling (automatic in Autopilot)
4. Use lifecycle policies for old data

## Scaling

### Horizontal Scaling

```bash
# Scale application replicas
kubectl scale deployment/genovaai --replicas=5 -n genovaai

# Scale Celery workers
kubectl scale deployment/celery-worker --replicas=4 -n genovaai
```

### Auto-scaling

```yaml
# Add HPA for automatic scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: genovaai-hpa
  namespace: genovaai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: genovaai
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Cleanup

```bash
# Delete all Kubernetes resources
kubectl delete -k kubernetes-manifests/

# Destroy GKE cluster (via Terraform)
cd terraform
terraform destroy -var="gcp_project_id=YOUR_PROJECT_ID"

# Or manually
gcloud container clusters delete genovaai-cluster --region=us-central1
```

---

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review pod logs and events
- Open an issue on GitHub
