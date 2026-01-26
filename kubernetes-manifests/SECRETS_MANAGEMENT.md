# 🔐 GenovaAI Secrets Management

## Quick Start (للتشغيل المحلي)

```bash
# 1. انسخ الـ template
cp kubernetes-manifests/secrets.template.yaml kubernetes-manifests/secrets.local.yaml

# 2. عدّل secrets.local.yaml واستبدل {{PLACEHOLDERS}} بقيمك الحقيقية
#    - GEMINI_API_KEY: احصل عليه من https://aistudio.google.com/apikey

# 3. طبّق على Kubernetes
kubectl apply -k kubernetes-manifests/
```

---

## Overview

This document explains how to manage secrets securely for GenovaAI deployments.

**⚠️ IMPORTANT: Never commit real secrets to Git!**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                        │
├─────────────────────────────────────────────────────────────┤
│  secrets.template.yaml  ← Template with {{PLACEHOLDERS}}    │
│  configmap.yaml         ← Non-sensitive configuration       │
│  .gitignore            ← Ignores generated secrets files    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Secrets                           │
├─────────────────────────────────────────────────────────────┤
│  FLASK_SECRET_KEY                                           │
│  POSTGRES_PASSWORD                                          │
│  MONGO_PASSWORD                                             │
│  REDIS_PASSWORD                                             │
│  RABBITMQ_PASSWORD                                          │
│  GEMINI_API_KEY                                             │
│  LANGCHAIN_API_KEY (optional)                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ CI/CD Pipeline
┌─────────────────────────────────────────────────────────────┐
│              secrets.generated.yaml                         │
│              (Created at deployment time)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                        │
│                   (genovaai-secrets)                        │
└─────────────────────────────────────────────────────────────┘
```

## Setting Up GitHub Secrets

### Step 1: Navigate to Repository Settings

1. Go to your GitHub repository: `https://github.com/AmrDabour/DNA`
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Step 2: Add Required Secrets

Add each of the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `FLASK_SECRET_KEY` | Flask session encryption key | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `POSTGRES_PASSWORD` | PostgreSQL database password | Strong random password |
| `MONGO_PASSWORD` | MongoDB database password | Strong random password |
| `REDIS_PASSWORD` | Redis cache password | Strong random password |
| `RABBITMQ_PASSWORD` | RabbitMQ message broker password | Strong random password |
| `GEMINI_API_KEY` | Google Gemini AI API key | Get from [Google AI Studio](https://aistudio.google.com/apikey) |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional) | Get from [LangSmith](https://smith.langchain.com/) |

### Step 3: Add GCP Secrets (for GKE deployment)

| Secret Name | Description |
|-------------|-------------|
| `GCP_PROJECT_ID` | Your Google Cloud Project ID |
| `GCP_SA_KEY` | Service Account JSON key for GKE access |

## Getting a New Gemini API Key

Your current API key has expired. To get a new one:

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key and add it to GitHub Secrets as `GEMINI_API_KEY`

## Local Development

For local development, create a `secrets.local.yaml` file (already in `.gitignore`):

```bash
# Copy the template
cp kubernetes-manifests/secrets.template.yaml kubernetes-manifests/secrets.local.yaml

# Edit with your local values
# Replace {{PLACEHOLDERS}} with actual values
```

Or use the generate script:

```bash
# Set environment variables
export FLASK_SECRET_KEY="local-dev-key"
export POSTGRES_PASSWORD="local-password"
export MONGO_PASSWORD="local-password"
export REDIS_PASSWORD="local-password"
export RABBITMQ_PASSWORD="local-password"
export GEMINI_API_KEY="your-gemini-api-key"

# Generate secrets
./kubernetes-manifests/generate-secrets.sh

# Apply to local Kubernetes
kubectl apply -f kubernetes-manifests/secrets.generated.yaml
```

## Environment-Specific Configurations

### Production
- Use GitHub Secrets
- Enable MongoDB/Redis authentication
- Use strong, unique passwords
- Enable TLS/SSL

### Staging
- Can use separate GitHub environment secrets
- Same security practices as production

### Local Development
- Use `secrets.local.yaml`
- Can disable authentication for simplicity
- Use simple passwords

## Files Reference

| File | Purpose | Git Tracked |
|------|---------|-------------|
| `secrets.template.yaml` | Template with placeholders | ✅ Yes |
| `secrets.generated.yaml` | Generated from template | ❌ No |
| `secrets.local.yaml` | Local development secrets | ❌ No |
| `configmap.yaml` | Non-sensitive config | ✅ Yes |

## Security Best Practices

1. **Rotate secrets regularly** - Change passwords every 90 days
2. **Use strong passwords** - Minimum 32 characters, mixed case, numbers, symbols
3. **Limit access** - Only give team members necessary access to secrets
4. **Audit access** - Review who has access to secrets regularly
5. **Never log secrets** - Ensure application doesn't log sensitive data
6. **Use environment-specific secrets** - Different secrets for prod/staging/dev

## Troubleshooting

### Secret not found in Kubernetes
```bash
# Check if secret exists
kubectl get secrets -n genovaai

# View secret (base64 encoded)
kubectl get secret genovaai-secrets -n genovaai -o yaml
```

### API Key Expired
1. Generate new key from respective service
2. Update GitHub Secret
3. Re-run deployment workflow

### Permission Denied
Ensure the GitHub Actions workflow has access to secrets:
- Repository secrets are available to all workflows
- Environment secrets require workflow to specify the environment
