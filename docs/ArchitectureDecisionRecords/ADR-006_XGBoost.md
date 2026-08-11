# ADR-006: Selection of XGBoost as Primary Classifier Engine

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Senior ML Engineer, Principal Software Architect  

---

## 1. Problem Statement
The NSL-KDD tabular network flow dataset contains non-linear numerical features, categorical protocol flags, and severe class imbalance (U2R and R2L threats comprise <1% of records). The primary classifier must maximize overall Macro F1 ($\ge 0.85$) and minority class recall while maintaining fast sub-10ms inference execution per flow vector.

## 2. Decision
Utilize **XGBoost Classifier** with cost-sensitive sample weighting as the primary high-accuracy in-memory classification model.

## 3. Alternatives Considered
- **RandomForestClassifier**: Strong baseline (Macro F1 `0.5110` in V1.0), but struggled with minority class recall compared to gradient boosting.
- **Deep Neural Networks (MLP / CNN)**: Capable models, but require longer training cycles, lack tabular efficiency, and introduce heavier execution overhead without yielding significant performance gains over XGBoost on tabular flow data.
- **Logistic Regression**: Fast, but unable to capture complex non-linear feature interactions present in network flow attack patterns.

## 4. Consequences & Impact
- **Positive**: State-of-the-art tabular classification accuracy, native support for sample weighting, fast C++ C-extension execution runtime, and direct compatibility with TreeSHAP.
- **Negative**: Model artifacts (`.pkl`) require pre-loading into RAM across worker instances.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: Memory boundary limits during massive multi-gigabyte log analysis.
- *Mitigation*: The system retains the Out-of-Core `SGDClassifier` pipeline as a selectable fallback mode for memory-constrained environments.
