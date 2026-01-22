# =============================================================================
# GenovaAI Microservices - Build Script (Windows)
# =============================================================================
# Builds all Docker images for the microservices architecture
#
# Usage:
#   .\scripts\build-microservices.ps1              # Build all images
#   .\scripts\build-microservices.ps1 -Service auth    # Build specific service
#   .\scripts\build-microservices.ps1 -Push        # Build and push to registry
# =============================================================================

param(
    [string]$Service = "",
    [string]$Registry = "",
    [string]$Version = "latest",
    [switch]$Push
)

# Configuration
$Services = @("auth-service", "analysis-service", "prediction-service", "ai-service", "agent-service", "frontend-service")

function Write-Header($message) {
    Write-Host "============================================================" -ForegroundColor Blue
    Write-Host $message -ForegroundColor Blue
    Write-Host "============================================================" -ForegroundColor Blue
}

function Write-Success($message) {
    Write-Host "✓ $message" -ForegroundColor Green
}

function Write-Error($message) {
    Write-Host "✗ $message" -ForegroundColor Red
}

function Write-Info($message) {
    Write-Host "→ $message" -ForegroundColor Yellow
}

function Build-Service($serviceName) {
    $servicePath = "services\$serviceName"
    $imageName = "genovaai-$serviceName"
    
    if ($Registry) {
        $imageName = "$Registry/$imageName"
    }
    
    Write-Info "Building $serviceName..."
    
    if (-not (Test-Path $servicePath)) {
        Write-Error "Service directory not found: $servicePath"
        return $false
    }
    
    if (-not (Test-Path "$servicePath\Dockerfile")) {
        Write-Error "Dockerfile not found for $serviceName"
        return $false
    }
    
    docker build -t "${imageName}:${Version}" -f "$servicePath\Dockerfile" $servicePath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Built ${imageName}:${Version}"
        
        # Tag as latest if version is not latest
        if ($Version -ne "latest") {
            docker tag "${imageName}:${Version}" "${imageName}:latest"
            Write-Success "Tagged ${imageName}:latest"
        }
        return $true
    } else {
        Write-Error "Failed to build $serviceName"
        return $false
    }
}

function Push-Service($serviceName) {
    $imageName = "genovaai-$serviceName"
    
    if ($Registry) {
        $imageName = "$Registry/$imageName"
    }
    
    Write-Info "Pushing $serviceName..."
    
    docker push "${imageName}:${Version}"
    
    if ($Version -ne "latest") {
        docker push "${imageName}:latest"
    }
    
    Write-Success "Pushed $imageName"
}

# Main logic
Write-Header "GenovaAI Microservices Build"
Write-Host "Registry: $(if ($Registry) { $Registry } else { 'local' })"
Write-Host "Version: $Version"
Write-Host ""

if ($Service) {
    # Build specific service
    $targetService = $Service
    if (-not $targetService.EndsWith("-service")) {
        $targetService = "$targetService-service"
    }
    
    if ($Services -contains $targetService) {
        Build-Service $targetService
        if ($Push) {
            Push-Service $targetService
        }
    } else {
        Write-Error "Unknown service: $Service"
        Write-Host "Available services: $($Services -join ', ')"
        exit 1
    }
} else {
    # Build all services
    Write-Header "Building All Services"
    foreach ($svc in $Services) {
        Build-Service $svc
        Write-Host ""
    }
    
    if ($Push) {
        Write-Header "Pushing All Images"
        foreach ($svc in $Services) {
            Push-Service $svc
        }
    }
}

Write-Header "Build Complete!"
Write-Host ""
Write-Host "To run the microservices stack:"
Write-Host "  docker-compose -f docker-compose.microservices.yml up -d"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker-compose -f docker-compose.microservices.yml logs -f"
