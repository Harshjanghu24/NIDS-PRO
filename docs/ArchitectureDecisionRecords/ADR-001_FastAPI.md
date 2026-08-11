# ADR-001: Selection of FastAPI as Core Backend API Framework

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Lead Backend Engineer, Principal Software Architect  

---

## 1. Problem Statement
Version 1.0 of the project utilized Flask as its backend web framework. While Flask sufficed for static file uploads and simple REST routes, Version 2.0 requires high-concurrency real-time WebSocket broadcasting, non-blocking asynchronous database operations, strict request input schema validation, and auto-generated API contracts (OpenAPI 3.0). Synchronous Flask threads struggle to scale under high-frequency WebSocket streams without complex greenlet extensions (e.g. Gevent/Eventlet).

## 2. Decision
Migrate the primary API tier to **FastAPI** running on the **Uvicorn** ASGI web server.

## 3. Alternatives Considered
- **Flask (Retained V1.0)**: Simple and familiar, but synchronous WSGI model limits concurrency for WebSockets and async I/O; lacks native schema validation.
- **Django + Django REST Framework (DRF)**: Extremely feature-rich ORM and admin interface, but heavier footprint, slower execution overhead, and less suited for pure microservice API interfaces.
- **Node.js + Express**: High I/O performance, but introduces multi-language stack complexity when interfacing with Python-based ML libraries (Scikit-Learn, XGBoost, SHAP).

## 4. Consequences & Impact
- **Positive**: Native asynchronous syntax (`async`/`await`), built-in Pydantic schema validation, automatically generated Swagger UI documentation (`/docs`), and up to 3x higher request throughput.
- **Negative**: Development team must write fully non-blocking code and use asynchronous drivers (`asyncpg`, `redis-py` async).

## 5. Tradeoffs & Risk Mitigation
- *Risk*: Mixing blocking CPU-heavy operations (e.g., model inference) in async route handlers will freeze the Uvicorn event loop.
- *Mitigation*: Heavy CPU operations (ML inference, SHAP, packet capture) are offloaded to background Celery worker processes via Redis queues.
