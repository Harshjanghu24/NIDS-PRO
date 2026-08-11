# ADR-003: Selection of Redis as Message Broker, Cache & Pub/Sub Engine

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Lead Backend Engineer, DevOps Architect  

---

## 1. Problem Statement
Real-time packet ingestion produces thousands of network flow vectors per second. To prevent dropping packets or blocking HTTP API execution, the ingestion pipeline requires an ultra-low latency memory buffer, background task message queue, and real-time event pub/sub channel for WebSockets.

## 2. Decision
Deploy **Redis 7** as the unified in-memory broker, task queue storage, pub/sub broadcaster, and ephemeral cache.

## 3. Alternatives Considered
- **RabbitMQ**: Excellent AMQP message broker with complex routing, but adds operational overhead and lacks built-in key-value caching capabilities.
- **Apache Kafka**: Exceptional log streaming performance for massive enterprise scale, but far too complex and resource-heavy for containerized local portfolio/single-server deployments.
- **In-Memory Python Queues (`queue.Queue`)**: Zero external dependencies, but cannot share queue state across multiple worker containers or processes.

## 4. Consequences & Impact
- **Positive**: Sub-millisecond queue operations, unified broker for Celery and WebSocket pub/sub, simple Docker deployment, built-in memory eviction policies.
- **Negative**: Volatile memory storage requires configuring `appendonly yes` (AOF) persistence to prevent data loss during container restarts.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: Memory exhaustion under high unconsumed packet queues.
- *Mitigation*: Configure Redis `maxmemory` caps with `allkeys-lru` eviction policy and monitor queue depth metrics via Prometheus.
