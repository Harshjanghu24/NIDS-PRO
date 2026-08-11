# ADR-008: Multi-Container Orchestration via Docker Compose

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** DevOps Architect, Principal Software Architect  

---

## 1. Problem Statement
The Version 2.0 platform consists of multiple heterogeneous components (FastAPI, React, PostgreSQL, Redis, Celery Workers, Scapy Packet Sniffer). Deploying these components manually across different operating systems introduces dependency drift, port conflicts, privilege errors, and deployment friction.

## 2. Decision
Standardize container packaging using **Docker** containers managed by a single **Docker Compose** orchestration specification (`docker-compose.yml`).

## 3. Alternatives Considered
- **Bare Metal / VirtualEnv Setup**: Complex installation steps requiring manual PostgreSQL and Redis installation on host OS, prone to configuration drift.
- **Kubernetes (Minikube / K3s)**: Powerful container orchestrator, but introduces excessive overhead for local development, evaluation, and single-host portfolio demonstrations.
- **Vagrant Virtual Machines**: Heavier resource footprint (virtualizing full guest OS) compared to lightweight Linux containers.

## 4. Consequences & Impact
- **Positive**: Reproducible single-command deployment (`docker-compose up --build`), isolated microservice environments, simplified environment variable management, and clear Kubernetes migration path.
- **Negative**: Requires Docker Engine / Docker Desktop runtime installed on the deployment host.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: Raw socket sniffing inside Docker requires elevated host network privileges.
- *Mitigation*: The `packet_sniffer` service container is granted explicit capabilities (`cap_add: [NET_ADMIN, NET_RAW]`) rather than running all containers in privileged mode.
