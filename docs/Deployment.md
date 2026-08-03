# Containerization & Production Deployment Guide

This document details how to package, deploy, and operate the Network Intrusion Detection System in production environments using Docker and Gunicorn.

---

## 1. Production Architecture Overview

In production, Flask's built-in development web server (`app.run()`) is replaced by **Gunicorn**, a pre-fork WSGI HTTP server designed for production stability, concurrency, and performance.

```
                    ┌────────────────────────┐
                    │    Reverse Proxy       │
                    │   (Nginx / ALB / K8s)  │
                    └───────────┬────────────┘
                                │ HTTP :5000
                                ▼
                    ┌────────────────────────┐
                    │   Gunicorn WSGI Master │
                    └───────────┬────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
    ┌────────────────────────┐    ┌────────────────────────┐
    │  Gunicorn Worker 1     │    │  Gunicorn Worker 2     │
    │  Flask app instance    │    │  Flask app instance    │
    └────────────────────────┘    └────────────────────────┘
```

---

## 2. Dockerfile Configuration

The production `Dockerfile` leverages `python:3.12-slim` for a minimal container security surface (~250 MB total image size):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

EXPOSE 5000

# Production command using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

---

## 3. Environment Variables & Security

Configure runtime behavior via standard environment variables:

| Variable | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `FLASK_DEBUG` | `0` | Disables debug mode and tracebacks. |
| `SECRET_KEY` | High-entropy random string (e.g. `openssl rand -hex 32`) | Used to sign session cookies and request security tokens. |
| `PORT` | `5000` | Port on which Gunicorn binds. |

### Example Docker Run Command with Secrets
```bash
docker run -d \
  -p 5000:5000 \
  -e FLASK_DEBUG=0 \
  -e SECRET_KEY="c84f9a01e51b2d...prod_secret_key" \
  --name nids-prod \
  --restart unless-stopped \
  nids-app
```

---

## 4. Health Checks & Monitoring

### Docker Healthcheck Integration
Add the following healthcheck instruction to `docker-compose.yml` or container startup:

```yaml
version: '3.8'

services:
  nids-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_DEBUG=0
      - SECRET_KEY=prod_secret_key_change_me
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## 5. Performance Tuning & Concurrency

For production worker allocation, use the standard formula:

$$\text{Workers} = (2 \times \text{CPU Cores}) + 1$$

- **Small Instance (1 vCPU, 2 GB RAM)**: 2 Workers (`--workers 2`)
- **Standard Instance (2 vCPU, 4 GB RAM)**: 4 Workers (`--workers 4`)
- **Large Instance (4 vCPU, 8 GB RAM)**: 8 Workers (`--workers 8`)
