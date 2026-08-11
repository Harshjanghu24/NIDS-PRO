# ADR-004: Selection of Celery for Asynchronous Background Processing

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Lead Backend Engineer, Senior ML Engineer  

---

## 1. Problem Statement
Heavy operations such as bulk CSV flow preprocessing, XGBoost inference matrix calculation, SHAP explainability attribution generation, and model retraining tasks require CPU-intensive computation. Executing these on the main API web server thread causes severe request latency spikes and WebSocket starvation.

## 2. Decision
Adopt **Celery 5.3** as the distributed asynchronous task queue manager backed by Redis.

## 3. Alternatives Considered
- **FastAPI `BackgroundTasks`**: Built into FastAPI, but runs within the same Python web process; unsuited for heavy CPU-bound tasks or multi-container horizontal worker scaling.
- **RQ (Redis Queue)**: Lightweight Python queue library, but lacks advanced task routing, rate limiting, and multi-worker orchestration features provided by Celery.
- **ARQ**: Asyncio-native Redis queue, but has smaller ecosystem maturity for complex task retries, progress tracking, and worker management compared to Celery.

## 4. Consequences & Impact
- **Positive**: Complete isolation of heavy CPU tasks from API web workers, horizontal worker scaling via `docker-compose scale`, automatic task retries, and task progress monitoring.
- **Negative**: Adds Celery worker process overhead and state serialization management.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: Celery worker process crashes during heavy SHAP computations.
- *Mitigation*: Celery tasks configure `acks_late=True` and `reject_on_worker_lost=True` to ensure crashed tasks are automatically re-queued.
