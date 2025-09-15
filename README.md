# Sales Dashboard

A modern sales analytics dashboard built with Flask, featuring automated deployment, structured logging, caching, and comprehensive testing.

## Architecture Overview

```
Sales Dashboard
├── deploy_ready_app.py      # Main Flask application (production entrypoint)
├── config.py                # Centralized configuration management
├── frontend/                # Static HTML dashboards  
├── tests/                   # Test suite (pytest)
├── .github/workflows/       # CI/CD automation
└── archive/                 # Legacy code snapshots
```

### Key Features
- **Multi-format Data Loading**: Automatic TSV/CSV/Excel detection with fallback paths
- **In-Memory Caching**: Response caching with TTL for expensive analytics endpoints
- **Structured Logging**: JSON-formatted logs for Azure monitoring and debugging
- **Health Monitoring**: Comprehensive health checks with system metrics
- **Automated CI/CD**: GitHub Actions for testing and Azure deployment
- **Configuration Management**: Environment-driven settings with feature flags

## Setup and Development

### Prerequisites
- Python 3.11+ (see `runtime.txt`)
- Virtual environment (recommended)

### Installation
```bash
# Clone and navigate to project
git clone <repository-url>
cd Sales-dashboard-1

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Locally
```bash
# Development server
python deploy_ready_app.py

# Production-like server
gunicorn --bind 0.0.0.0:5000 deploy_ready_app:app
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=deploy_ready_app

# Run specific test suites
pytest tests/test_api.py      # API endpoint tests
pytest tests/test_cache.py    # Caching behavior tests
```

## Configuration

The application uses `config.py` for centralized configuration:

```python
# Environment variables
ENV = "production"           # development, staging, production  
LOG_LEVEL = "INFO"          # DEBUG, INFO, WARNING, ERROR

# Feature flags
ENABLE_REFRESH = True       # Enable /api/refresh-data endpoint
ENABLE_STATS = True         # Show cache stats in health endpoint

# Data file candidates (prioritized search paths)
DATA_FILE_CANDIDATES = [
    "Sales data",
    "Sales data - Filtered", 
    "./Sales data.csv",
    # ... additional paths
]
```

## API Endpoints

### Core Endpoints
- `GET /` - API information and service status
- `GET /api/health` - Comprehensive health check with system metrics
- `GET /api/data-info` - Data loading status and file metadata

### Analytics Endpoints  
- `GET /api/overall_sales_performance` - Sales performance analytics (cached)

### Dashboard Views
- `GET /operational` - Operational dashboard view
- `GET /strategic` - Strategic dashboard view

### Management Endpoints
- `POST /api/refresh-data` - Force data reload and cache invalidation

## Deployment (Azure App Service)

### Production Configuration
- **Entrypoint**: `deploy_ready_app.py` 
- **WSGI**: Gunicorn via `Procfile`
- **Runtime**: Python 3.11 (see `runtime.txt`)
- **Dependencies**: `requirements.txt` (consolidated)

### GitHub Actions Workflows

#### CI Pipeline (`.github/workflows/ci.yml`)
- Runs on every push/PR
- Tests across Python versions
- Validates import and endpoint functionality

#### Deployment Pipeline (`.github/workflows/deploy.yml`)
- Triggers on pushes to `main` branch
- Deploys to Azure App Service
- Requires secrets: `AZURE_WEBAPP_NAME`, `AZURE_WEBAPP_PUBLISH_PROFILE`

### Manual Deployment
```bash
# Local build test
pip install -r requirements.txt
pytest
gunicorn --check-config deploy_ready_app:app

# Push to main branch triggers auto-deployment
git push origin main
```

### Monitoring and Troubleshooting

#### Health Monitoring
- Monitor via: `https://<your-app>.azurewebsites.net/api/health`
- Status page: `frontend/status.html` (manual refresh and diagnostics)

#### Common Issues

**ModuleNotFoundError**: 
- Verify `requirements.txt` is up to date
- Check Azure build logs in Kudu console
- Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

**Cache Issues**:
- Cache TTL: 60 seconds (configurable via `CACHE_TTL_SECONDS`)
- Manual cache clear: `POST /api/refresh-data`
- Cache stats: Check `/api/health` response

**Data Loading Failures**:
- Check `/api/data-info` for detailed error messages
- Verify data file exists in expected paths
- Review structured logs for path resolution details

#### Structured Logging Format
```json
{
  "msg": "Request processed", 
  "ts": "2025-09-15T10:30:00Z",
  "event": "request",
  "method": "GET", 
  "path": "/api/health",
  "status_code": 200,
  "duration_ms": 15.2,
  "cache_hit": false
}
```

## Development Workflow

### Adding New Features
1. Create feature branch from `main`
2. Add tests for new functionality
3. Update configuration if needed
4. Run full test suite: `pytest`
5. Submit PR with CI passing

### Cache Management
- Use `@cache_response(ttl=60)` decorator for expensive endpoints
- Cache keys include query parameters
- Cache automatically cleared on data refresh

### Legacy Code
Archived files in `archive/` directory:
- `app_stable.py` - Previous backend implementation
- `deploy_ready_app_fixed.py` - Experimental deployment variant
- `deploy_ready_app_sql.py` - SQL integration experiment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure CI passes
5. Submit pull request

For questions or issues, check the health endpoint and structured logs first, then consult this documentation.