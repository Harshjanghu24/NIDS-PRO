# Machine Learning Evaluation & Feature Importance

This document details model selection, class imbalance mitigation, evaluation metrics, and feature importance analysis for the Network Intrusion Detection System.

---

## 1. Candidate Models Evaluated

Two primary candidate architectures were evaluated during batch in-memory model selection (`train_model.py`):
1. **RandomForestClassifier**: Ensemble of 200 decision trees trained with `class_weight='balanced'`.
2. **XGBoostClassifier (Chosen)**: Gradient boosted decision tree ensemble (200 trees) trained with sample weighting computed via `compute_sample_weight('balanced', y_train)`.

In addition, an **Out-of-Core Linear Classifier (`SGDClassifier`)** was implemented for streaming memory-constrained execution (`train_model_ooc.py`).

---

## 2. Evaluation Results on Unseen Test Data (`Test.txt` — 22,544 rows)

### Performance Comparison Matrix

| Evaluation Metric | RandomForest | XGBoost (Selected) | SGDClassifier (OOC) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 75.21% | **77.03%** | 74.00% |
| **Macro F1 Score** | 0.5110 | **0.5684** | 0.5200 |
| **Weighted F1 Score** | 0.7012 | **0.7323** | 0.7300 |
| **DOS Class F1** | 84.80% | **88.09%** | 82.00% |
| **Normal Class F1** | 78.31% | **79.39%** | 86.00% |
| **PROBE Class F1** | 74.20% | **75.81%** | 57.00% |
| **R2L Class Recall** | 1.59% | **6.96%** | 11.01% |
| **U2R Class Recall** | 10.45% | **17.91%** | 52.24% |

XGBoost achieved the highest Macro F1 Score (**0.5684**) and was selected as the active production model (`model.pkl`).

---

## 3. Confusion Matrix Breakdown (XGBoost)

Labels: `['DOS', 'Normal', 'PROBE', 'R2L', 'U2R']`

```
               Predicted DOS  Predicted Normal  Predicted PROBE  Predicted R2L  Predicted U2R
True DOS               6044              1322               92              0              0
True Normal              56              9445              206              2              2
True PROBE              165               592             1664              0              0
True R2L                  0              2674                7            201              5
True U2R                  0                50                0              5             12
```

---

## 4. Top Feature Importances Analysis

Feature importances extracted from the fitted XGBoost model pipeline (`results/feature_importance.json`):

| Rank | Feature Name | Importance | Description / Cyber Context |
| :---: | :--- | :---: | :--- |
| 1 | `service_eco_i` | **19.39%** | ICMP Echo Request service (commonly used in Ping flood / DoS attacks). |
| 2 | `service_telnet` | **12.42%** | Unencrypted remote terminal protocol (frequently targeted by R2L / brute force). |
| 3 | `service_smtp` | **10.58%** | Simple Mail Transfer Protocol (targeted by mailbomb DoS). |
| 4 | `flag_S0` | **8.50%** | Connection attempt seen with SYN packet but no ACK response (SYN Flood / Stealth Scan). |
| 5 | `dst_host_serror_rate` | **5.13%** | Destination host SYN error rate (indicator of port scanning / DoS probes). |
| 6 | `num_failed_logins` | **3.66%** | Number of failed authentication attempts (Password guessing / Brute force). |
| 7 | `count` | **3.58%** | Number of connection attempts to same host in 2 seconds. |
| 8 | `root_shell` | **3.43%** | Root access privilege obtained (U2R privilege escalation indicator). |
| 9 | `service_domain_u` | **2.68%** | DNS UDP service requests. |
| 10 | `is_guest_login` | **2.46%** | Guest account logins (R2L unauthorized entry vector). |

---

## 5. Artifact Exports

Evaluation metrics and model state are persisted to disk upon training completion:
- `model.pkl`: Serialized XGBoost model object.
- `preprocessor.pkl`: Serialized `ColumnTransformer` object.
- `label_encoder.pkl`: Active `LabelEncoder` mapping string labels to numeric targets.
- `results/evaluation_report.json`: JSON payload containing complete per-class precision, recall, and F1 scores.
- `results/feature_importance.json`: Complete 122-feature importance ranking array.
