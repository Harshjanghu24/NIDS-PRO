# ADR-007: Integration of SHAP for Explainable AI (XAI) Feature Attribution

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Senior ML Engineer, Senior Cybersecurity Engineer  

---

## 1. Problem Statement
Machine learning models are frequently criticized in security operational environments for acting as "black boxes." Security analysts triaging intrusion alerts require clear mathematical rationale explaining *why* a particular flow was flagged as a specific threat (e.g. U2R or R2L) before initiating costly incident response procedures.

## 2. Decision
Integrate **SHAP (SHapley Additive exPlanations)** natively into the threat prediction pipeline.

## 3. Alternatives Considered
- **LIME (Local Interpretable Model-agnostic Explanations)**: Provides local interpretability, but uses sampling approximations that can produce inconsistent attribution scores across identical predictions.
- **Global Feature Importance Graphs**: Displays overall model feature rankings, but fails to explain individual flow instances.
- **Raw Threshold Rules**: Traditional static rule logic, but defeats the adaptive benefits of machine learning anomaly detection.

## 4. Consequences & Impact
- **Positive**: Game-theoretic consistency, exact per-flow feature contribution scores, enhanced SOC analyst trust, and actionable remediation telemetry.
- **Negative**: SHAP calculation introduces additional CPU compute overhead during inference.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: High computation latency slowing down real-time prediction pipelines.
- *Mitigation*: TreeSHAP is executed asynchronously in background Celery workers *only* when a flow is classified as a malicious intrusion category (`DOS`, `PROBE`, `R2L`, `U2R`), skipping normal flows.
