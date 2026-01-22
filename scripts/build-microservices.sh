#!/bin/bash
# =============================================================================
# GenovaAI Microservices - Build Script
# =============================================================================
# Builds all Docker images for the microservices architecture
#
# Usage:
#   ./scripts/build-microservices.sh          # Build all images
#   ./scripts/build-microservices.sh auth     # Build specific service
#   ./scripts/build-microservices.sh --push   # Build and push to registry
# =============================================================================

set -e

# Configuration
REGISTRY="${DOCKER_REGISTRY:-}"
VERSION="${VERSION:-latest}"
SERVICES=("auth-service" "analysis-service" "prediction-service" "ai-service" "agent-service" "frontend-service")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

build_service() {
    local service=$1
    local service_path="services/${service}"
    local image_name="genovaai-${service}"
    
    if [ -n "$REGISTRY" ]; then
        image_name="${REGISTRY}/${image_name}"
    fi
    
    print_info "Building ${service}..."
    
    if [ ! -d "$service_path" ]; then
        print_error "Service directory not found: ${service_path}"
        return 1
    fi
    
    if [ ! -f "${service_path}/Dockerfile" ]; then
        print_error "Dockerfile not found for ${service}"
        return 1
    fi
    
    docker build -t "${image_name}:${VERSION}" -f "${service_path}/Dockerfile" "${service_path}"
    
    if [ $? -eq 0 ]; then
        print_success "Built ${image_name}:${VERSION}"
        
        # Tag as latest if version is not latest
        if [ "$VERSION" != "latest" ]; then
            docker tag "${image_name}:${VERSION}" "${image_name}:latest"
            print_success "Tagged ${image_name}:latest"
        fi
    else
        print_error "Failed to build ${service}"
        return 1
    fi
}

push_service() {
    local service=$1
    local image_name="genovaai-${service}"
    
    if [ -n "$REGISTRY" ]; then
        image_name="${REGISTRY}/${image_name}"
    fi
    
    print_info "Pushing ${service}..."
    
    docker push "${image_name}:${VERSION}"
    
    if [ "$VERSION" != "latest" ]; then
        docker push "${image_name}:latest"
    fi
    
    print_success "Pushed ${image_name}"
}

# Main logic
PUSH=false
SPECIFIC_SERVICE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        *)
            SPECIFIC_SERVICE="$1"
            shift
            ;;
    esac
done

print_header "GenovaAI Microservices Build"
echo "Registry: ${REGISTRY:-local}"
echo "Version: ${VERSION}"
echo ""

# Build services
if [ -n "$SPECIFIC_SERVICE" ]; then
    # Build specific service
    if [[ " ${SERVICES[*]} " =~ " ${SPECIFIC_SERVICE} " ]] || [[ " ${SERVICES[*]} " =~ " ${SPECIFIC_SERVICE}-service " ]]; then
        # Add -service suffix if not present
        if [[ ! "$SPECIFIC_SERVICE" =~ -service$ ]]; then
            SPECIFIC_SERVICE="${SPECIFIC_SERVICE}-service"
        fi
        build_service "$SPECIFIC_SERVICE"
        if [ "$PUSH" = true ]; then
            push_service "$SPECIFIC_SERVICE"
        fi
    else
        print_error "Unknown service: ${SPECIFIC_SERVICE}"
        echo "Available services: ${SERVICES[*]}"
        exit 1
    fi
else
    # Build all services
    print_header "Building All Services"
    for service in "${SERVICES[@]}"; do
        build_service "$service"
        echo ""
    done
    
    if [ "$PUSH" = true ]; then
        print_header "Pushing All Images"
        for service in "${SERVICES[@]}"; do
            push_service "$service"
        done
    fi
fi

print_header "Build Complete!"
echo ""
echo "To run the microservices stack:"
echo "  docker-compose -f docker-compose.microservices.yml up -d"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.microservices.yml logs -f"
