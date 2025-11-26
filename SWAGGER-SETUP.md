# Swagger UI Setup Guide for Scholarport API

## Overview
This document describes the Swagger UI implementation for the Scholarport Backend API using `drf-spectacular`.

## API Documentation URLs

### Development (Local)
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema (JSON/YAML)**: http://127.0.0.1:8000/api/schema/

### Production (Docker)
- **Swagger UI**: http://your-domain.com/api/docs/
- **ReDoc**: http://your-domain.com/api/redoc/
- **OpenAPI Schema**: http://your-domain.com/api/schema/

## Package Dependencies

Added to `requirements.txt`:
```
drf-spectacular==0.27.0
drf-spectacular-sidecar==2024.7.1
```

The `drf-spectacular-sidecar` package bundles Swagger UI and ReDoc static files locally, eliminating CDN dependencies for production environments.

## Configuration

### INSTALLED_APPS (settings/base.py)
```python
INSTALLED_APPS = [
    # ... other apps
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # ...
]
```

### REST_FRAMEWORK Setting
```python
REST_FRAMEWORK = {
    # ... other settings
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### SPECTACULAR_SETTINGS
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Scholarport API',
    'DESCRIPTION': '...',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    # ... more settings
}
```

### URL Configuration (scholarport_backend/urls.py)
```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # ... other urls
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

## API Endpoints Documented

### Chat Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/start/` | Start a new conversation |
| POST | `/api/chat/send/` | Send a message in conversation |
| GET | `/api/chat/conversation/{session_id}/` | Get conversation history |
| POST | `/api/chat/consent/` | Handle data consent |

### University Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/universities/` | List universities with filters |
| GET | `/api/chat/universities/{id}/` | Get university details |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/admin/stats/` | Dashboard statistics |
| GET | `/api/chat/admin/profiles/` | Student profiles |
| GET | `/api/chat/admin/export/` | Export to Excel |
| GET | `/api/chat/admin/firebase-export/` | Export Firebase data |

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/health/` | API health check |

## Running Locally (Development)

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
python manage.py runserver

# Access Swagger UI
# Open: http://127.0.0.1:8000/api/docs/
```

## Deploying to Production (Docker)

### 1. Build and Deploy
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### 2. Static Files
Static files including Swagger UI assets are automatically collected during container startup via `docker-entrypoint.sh`:
```bash
python manage.py collectstatic --noinput
```

### 3. Access Documentation
Once deployed, access the documentation at:
- `http://your-server-ip/api/docs/` - Swagger UI
- `http://your-server-ip/api/redoc/` - ReDoc

## Troubleshooting

### Static files not loading in production
```bash
# Enter the backend container
docker exec -it scholarport_backend bash

# Manually collect static files
python manage.py collectstatic --noinput

# Verify files exist
ls -la /app/staticfiles/drf-spectacular-sidecar/
```

### Schema generation errors
```bash
# Generate schema file for debugging
python manage.py spectacular --file schema.yml
```

### Nginx 502 Bad Gateway
Check if the backend container is running and healthy:
```bash
docker-compose ps
docker-compose logs backend
```

## Customization

### Adding tags to endpoints
Use `@extend_schema` decorator:
```python
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['MyTag'], summary='My endpoint')
@api_view(['GET'])
def my_endpoint(request):
    pass
```

### Adding request/response examples
```python
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

@extend_schema(
    responses={
        200: OpenApiResponse(
            description='Success',
            examples=[
                OpenApiExample(
                    'Example Name',
                    value={'key': 'value'}
                )
            ]
        )
    }
)
```

## Security Notes

1. The Swagger UI is publicly accessible. For production, consider adding authentication.
2. Add authentication by modifying the view permissions:
```python
from rest_framework.permissions import IsAdminUser

path('api/docs/', SpectacularSwaggerView.as_view(
    url_name='schema',
    permission_classes=[IsAdminUser]
), name='swagger-ui'),
```

## Version History
- v1.0.0 - Initial Swagger UI implementation with drf-spectacular
