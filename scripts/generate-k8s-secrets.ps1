# ============================================================
# GenovaAI - Generate Kubernetes Secrets from .env file
# ============================================================
# Usage: .\scripts\generate-k8s-secrets.ps1
# This script reads from .env and creates secrets.local.yaml
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectRoot ".env"
$OutputFile = Join-Path $ProjectRoot "kubernetes-manifests\secrets.local.yaml"

Write-Host "🔐 GenovaAI - Kubernetes Secrets Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ .env file not found at: $EnvFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create .env file with at least:" -ForegroundColor Yellow
    Write-Host "  GEMINI_API_KEY=your_api_key_here" -ForegroundColor White
    Write-Host ""
    Write-Host "Get your API key from: https://aistudio.google.com/apikey" -ForegroundColor Cyan
    exit 1
}

# Read .env file
$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        $envVars[$key] = $value
    }
}

# Set defaults for missing values
$GEMINI_API_KEY = if ($envVars.ContainsKey('GEMINI_API_KEY')) { $envVars['GEMINI_API_KEY'] } else { "" }
$FLASK_SECRET_KEY = if ($envVars.ContainsKey('FLASK_SECRET_KEY')) { $envVars['FLASK_SECRET_KEY'] } else { "local-dev-secret-key-$(Get-Random)" }
$POSTGRES_PASSWORD = if ($envVars.ContainsKey('POSTGRES_PASSWORD')) { $envVars['POSTGRES_PASSWORD'] } else { "local-postgres-pwd" }
$MONGO_PASSWORD = if ($envVars.ContainsKey('MONGO_PASSWORD')) { $envVars['MONGO_PASSWORD'] } else { "local-mongo-pwd" }
$REDIS_PASSWORD = if ($envVars.ContainsKey('REDIS_PASSWORD')) { $envVars['REDIS_PASSWORD'] } else { "" }
$RABBITMQ_PASSWORD = if ($envVars.ContainsKey('RABBITMQ_PASSWORD')) { $envVars['RABBITMQ_PASSWORD'] } else { "local-rabbitmq-pwd" }
$LANGCHAIN_API_KEY = if ($envVars.ContainsKey('LANGCHAIN_API_KEY')) { $envVars['LANGCHAIN_API_KEY'] } else { "" }

# Validate required
if ([string]::IsNullOrEmpty($GEMINI_API_KEY)) {
    Write-Host "❌ GEMINI_API_KEY is missing in .env" -ForegroundColor Red
    Write-Host ""
    Write-Host "Add this line to your .env file:" -ForegroundColor Yellow
    Write-Host "  GEMINI_API_KEY=your_api_key_here" -ForegroundColor White
    Write-Host ""
    Write-Host "Get your API key from: https://aistudio.google.com/apikey" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Found GEMINI_API_KEY" -ForegroundColor Green

# Generate secrets.local.yaml
$secretsContent = @"
# ============================================================
# GenovaAI - Kubernetes Secrets (Auto-generated from .env)
# ============================================================
# Generated on: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# DO NOT COMMIT THIS FILE TO GIT!
# ============================================================
apiVersion: v1
kind: Secret
metadata:
  name: genovaai-secrets
  namespace: genovaai
type: Opaque
stringData:
  # Flask
  FLASK_SECRET_KEY: "$FLASK_SECRET_KEY"
  
  # PostgreSQL
  POSTGRES_USER: "genovaai"
  POSTGRES_PASSWORD: "$POSTGRES_PASSWORD"
  POSTGRES_DB: "genovaai"
  DATABASE_URL: "postgresql://genovaai:$POSTGRES_PASSWORD@postgres:5432/genovaai"
  
  # MongoDB (no auth for local dev)
  MONGO_INITDB_ROOT_USERNAME: "genovaai"
  MONGO_INITDB_ROOT_PASSWORD: "$MONGO_PASSWORD"
  MONGO_INITDB_DATABASE: "genovaai"
  MONGO_URI: "mongodb://mongodb:27017/genovaai"
  MONGODB_URI: "mongodb://mongodb:27017/genovaai"
  
  # Redis
  REDIS_PASSWORD: "$REDIS_PASSWORD"
  REDIS_URL: "redis://redis:6379/0"
  
  # RabbitMQ
  RABBITMQ_DEFAULT_USER: "genovaai"
  RABBITMQ_DEFAULT_PASS: "$RABBITMQ_PASSWORD"
  CELERY_BROKER_URL: "amqp://genovaai:$RABBITMQ_PASSWORD@rabbitmq:5672//"
  CELERY_RESULT_BACKEND: "redis://redis:6379/0"
  
  # Gemini API
  GEMINI_API_KEY: "$GEMINI_API_KEY"
  
  # LangSmith (optional)
  LANGCHAIN_API_KEY: "$LANGCHAIN_API_KEY"
  LANGCHAIN_PROJECT: "GenovaAI"
"@

# Write to file
$secretsContent | Out-File -FilePath $OutputFile -Encoding UTF8 -Force

Write-Host "✅ Generated: $OutputFile" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  kubectl apply -k kubernetes-manifests/" -ForegroundColor White
Write-Host "  kubectl port-forward -n genovaai svc/genovaai 5000:5000" -ForegroundColor White
Write-Host ""
Write-Host "Then open: http://localhost:5000" -ForegroundColor Cyan
