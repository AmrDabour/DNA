# GitHub Copilot Instructions for DNA Analysis Platform

## Project Overview

This is a DNA analysis platform that provides genomics-based predictions including gender and geographic region prediction from genetic data. The platform is built with Python and includes machine learning models, web interfaces, and comprehensive data processing capabilities.

## Architecture

- **Backend**: Python Flask/FastAPI application
- **Databases**: PostgreSQL (primary), MongoDB (document storage), Redis (caching/sessions)
- **ML Models**: Custom trained models for gender and region prediction from SNP data
- **Task Queue**: Celery with RabbitMQ for async processing
- **Deployment**: Kubernetes with Docker containers
- **Monitoring**: Prometheus and Grafana
- **Web Server**: Nginx as reverse proxy

## Key Components

### Core Application
- `app.py` - Main Flask application entry point
- `routes/` - API endpoints and web routes
- `services/` - Business logic and service layer
- `database/models.py` - SQLAlchemy/ODM models

### Machine Learning
- `ml_models/` - Contains trained ML models and prediction logic
- `ml_models/predictors.py` - Main prediction interface
- Gender and region prediction packages with trained models

### Data Processing
- `tasks/` - Celery tasks for async DNA analysis
- `utils/` - Utility functions for data processing
- Support for CSV upload and SNP analysis

### Configuration
- `config/` - Environment-specific configurations
- `kubernetes-manifests/` - K8s deployment configs
- `kubernetes-manifests/argocd/` - ArgoCD GitOps configs (separate namespace)
- `terraform/` - Infrastructure as Code

## Coding Standards

### Python Guidelines
- Use Python 3.9+ features
- Follow PEP 8 for code formatting
- Use type hints for function parameters and return values
- Prefer async/await for I/O operations where applicable
- Use dataclasses or Pydantic models for data structures

### Database Interactions
- Use SQLAlchemy ORM for PostgreSQL operations
- Implement proper connection pooling
- Use migrations for schema changes (Alembic)
- Always use parameterized queries to prevent SQL injection

### API Development
- RESTful API design principles
- Proper HTTP status codes
- Comprehensive error handling with meaningful messages
- Input validation using Pydantic or similar
- API versioning when making breaking changes

### Machine Learning Code
- Isolate ML logic in the `ml_models/` directory
- Use pickle or joblib for model serialization
- Implement proper model versioning
- Include model validation and performance metrics
- Handle edge cases in prediction pipelines

### Security Considerations
- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper authentication and authorization
- Validate and sanitize all user inputs
- Use HTTPS in production environments

### Testing
- Write unit tests for all business logic
- Use pytest as the testing framework
- Mock external dependencies
- Aim for >80% code coverage
- Include integration tests for API endpoints

### Docker & Kubernetes
- Use multi-stage Docker builds for optimization
- Follow container security best practices
- Use health checks in containers
- Implement proper resource limits in K8s manifests
- Use ConfigMaps and Secrets for configuration

### ArgoCD & GitOps
- ArgoCD configuration is in `kubernetes-manifests/argocd/` (separate namespace)
- Use ArgoCD Application CRDs to define deployments
- Enable automated sync with prune and self-heal for production
- Use ArgoCD Image Updater for automatic container image updates
- Prefer `semver` update strategy for production, `latest` for development
- Keep ArgoCD manifests separate from application manifests to avoid circular sync
- Use sync waves (`argocd.argoproj.io/sync-wave`) for deployment ordering
- Store ArgoCD credentials using Kubernetes secrets, not in Git

## File Naming Conventions
- Use snake_case for Python files and functions
- Use kebab-case for YAML/Docker files
- Descriptive names for ML model files
- Include version numbers in model artifacts

## Documentation
- Include docstrings for all functions and classes
- Use type hints extensively
- Update README.md for significant changes
- Document API endpoints with OpenAPI/Swagger
- Include setup instructions for new developers

## DNA Analysis Specific Guidelines

### Data Handling
- Always validate SNP data format before processing
- Implement proper error handling for malformed genetic data
- Use streaming for large genomic datasets
- Implement data privacy measures for genetic information

### Model Predictions
- Include confidence scores with predictions
- Handle missing or incomplete SNP data gracefully
- Log prediction requests for audit purposes
- Implement rate limiting for prediction endpoints

### Performance Considerations
- Cache frequently accessed genetic reference data
- Use async processing for time-consuming analyses
- Implement pagination for large result sets
- Monitor memory usage during genomic data processing

## Dependencies
- Keep requirements.txt updated
- Pin versions for production dependencies
- Use virtual environments for development
- Regular security audits of dependencies

## Deployment Notes
- Use blue-green deployment for production releases
- Implement proper logging and monitoring
- Use environment-specific configurations
- Backup databases before major deployments

## Common Patterns

When suggesting code, prefer these patterns:
- Use context managers for database connections
- Implement retry logic for external API calls
- Use structured logging with correlation IDs
- Implement circuit breakers for external services
- Use dependency injection for better testability

## Avoid These Patterns
- Hardcoded file paths or URLs
- Direct database queries outside the service layer
- Synchronous calls that could block the event loop
- Storing sensitive data in logs
- Coupling ML models tightly to web framework code