# ADR-002: Selection of PostgreSQL as Primary Relational Database

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Database Architect, Lead Backend Engineer  

---

## 1. Problem Statement
Version 1.0 lacked persistent database storage, relying on ephemeral in-memory predictions or CSV file outputs. Version 2.0 requires robust ACID-compliant persistence for user accounts, RBAC permissions, audit trails, model registry metadata, and millions of historical classified network flow records.

## 2. Decision
Select **PostgreSQL 15** managed via **SQLAlchemy 2.0** (`asyncpg`) and **Alembic** migrations.

## 3. Alternatives Considered
- **SQLite**: Great for zero-config embedded testing, but lacks high concurrency, native JSONB indexing, and declarative partitioning for large log volumes.
- **MongoDB**: Schema-less document flexibility, but lacks strict relational integrity, complex JOIN capabilities for audit histories, and native RBAC relational mapping.
- **MySQL / MariaDB**: Strong relational database, but PostgreSQL provides superior JSONB query support, native range partitioning, and better async Python ecosystem integration (`asyncpg`).

## 4. Consequences & Impact
- **Positive**: Strict data integrity, native JSONB support for flexible 41-attribute flow vectors, declarative range partitioning by month, and async connection pooling.
- **Negative**: Requires managing PostgreSQL container instance, persistent Docker volumes, and schema migration scripts.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: High log volume could cause disk space exhaustion.
- *Mitigation*: Automated table range partitioning and background pruning of normal flows older than 30 days.
