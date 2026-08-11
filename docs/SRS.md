# Software Requirements Specification (SRS)
## AI-Powered Network Intrusion Detection Platform (Version 2.0)

**Document Version:** 2.0.0-DRAFT  
**Standard:** IEEE Std 29148-2018 / IEEE Std 830-1998 Compliant  
**Status:** Approved for Architectural Design Phase (Phase A.1)  
**Authors:** Enterprise Product & Architecture Team  
- *Principal Software Architect*  
- *Senior Cybersecurity Engineer*  
- *Senior Machine Learning Engineer*  
- *Senior Backend Engineer*  
- *Product Manager*  
- *Technical Writer*  

---

## 1. Project Vision

### 1.1 Mission Statement
To transform an academic proof-of-concept into an enterprise-grade, modular, real-time AI-powered Network Intrusion Detection Platform (NIDS) that seamlessly bridges live network flow interception, online machine learning threat inference, and actionable SOC (Security Operations Center) telemetry.

### 1.2 Core Vision & Value Proposition
Version 1.0 demonstrated the feasibility of applying XGBoost and Out-of-Core SGD classification to the benchmark NSL-KDD dataset via static CSV batch processing. Version 2.0 represents a complete architectural evolution: evolving from an offline prediction tool into a decoupled, micro-service ready, production-grade cybersecurity platform. The system combines real-time raw socket packet capture, high-throughput flow assembly, dynamic model orchestration (MLOps), and intuitive SOC analytics into a cohesive operational ecosystem.

### 1.3 High-Level Goals
1. **Real-Time Traffic Ingestion**: Transition from batch CSV processing to live network interface tapping using Scapy/eBPF flow extraction.
2. **Enterprise Architecture**: Replace single-threaded monolithic Flask scripting with a modern, decoupled asynchronous backend (FastAPI/Asynchronous Workers) and a responsive single-page web interface (React/TypeScript).
3. **MLOps & Adaptive Intelligence**: Support multi-model management, automated drift detection, model versioning, feature attribution (SHAP/LIME), and continuous retraining pipelines.
4. **Production Readiness**: Provide robust RBAC authentication, PostgreSQL event persistence, Redis pub/sub streaming, Docker orchestration, and Prometheus/Grafana observability.

### 1.4 Success Criteria
- **Detection Efficacy**: Macro F1 $\ge 0.85$ across balanced attack classes, with minority class (U2R/R2L) recall $\ge 0.75$.
- **Real-Time Latency**: End-to-end flow processing latency (packet capture to alert generation) $\le 50\text{ ms}$.
- **System Stability**: Zero memory leaks under sustained 1 Gbps traffic flow ingestion using out-of-core streaming primitives.
- **Portfolio & Interview Standard**: High technical documentation clarity, clean architectural separation, $>85\%$ test coverage, and single-command containerized deployment.

### 1.5 Business & Portfolio Value
- **Industry Relevance**: Demonstrates mastery of real-world cybersecurity protocols, low-level packet processing, scalable machine learning engineering, and secure system design.
- **Architectural Rigor**: Serves as a reference implementation for decoupled ML pipelines, event-driven microservices, and modern SOC tooling.

---

## 2. Executive Summary

### 2.1 Problem Overview
Modern enterprise network perimeters face sophisticated cyber attack vectors, including zero-day exploits, distributed denial-of-service (DDoS), fileless malware, and privilege escalation techniques. Traditional security controls rely heavily on static signature matching (e.g., Snort/Suricata rules). These signature-based systems fail when encountering obfuscated threats, novel attack variants, or high-velocity encrypted traffic streams.

### 2.2 Operational Significance
While machine learning provides superior generalization capabilities for anomaly detection, existing open-source ML tools often exist as academic scripts restricted to static, offline CSV datasets. Security Analysts and SOC Engineers require an operational platform that bridge ML models with live network streams, providing real-time alert triage, automated flow telemetry, and actionable threat intelligence without introducing system instability or excessive false positive rates.

### 2.3 Target User Community
The platform targets cybersecurity students, machine learning researchers, SOC analysts, network administrators, and technical recruiters seeking a reference-grade demonstration of applied machine learning in infrastructure security.

---

## 3. Problem Statement

### 3.1 Limitations of Traditional Signature-Based IDS
- **Zero-Day Vulnerability**: Signature-based IDS rely on pre-existing database signatures. Novel attacks pass undetected until a signature is authored, tested, and distributed.
- **Rule Explosion & Maintenance Overhead**: As network complexity grows, rule engines suffer performance degradation due to thousands of complex regex operations per packet.
- **Rigidity**: Unable to detect contextual anomalies, such as legitimate commands executed at abnormal frequencies or times.

### 3.2 Deficiencies of Offline CSV-Only Analysis (Version 1.0 Limitations)
- **Synthetic Feature Disconnect**: Standard benchmark datasets (NSL-KDD, CIC-IDS2017) provide pre-calculated flow attributes. Offline CSV tools cannot inspect live packet headers or construct real-time flow states.
- **Lack of Actionable Triage**: CSV prediction yields static tables without real-time alerting, socket notifications, or active threat mitigation hooks.
- **Latency & Batch Constraints**: Processing static files introduces human intervention lag, making automated intrusion response impossible.

### 3.3 Modern Enterprise Network Security Challenges
- **High Traffic Velocity**: Modern network links process thousands of packets per second, demanding non-blocking, asynchronous packet parsing.
- **Extreme Class Imbalance**: Malicious network flows account for less than $0.1\%$ of total enterprise network traffic, leading to high false-positive fatigue if classifiers are improperly calibrated.
- **Resource Constraints**: High-throughput analysis can easily consume system RAM, causing Out-Of-Memory (OOM) failures on standard gateway hardware.

### 3.4 Rationale for AI-Assisted Intrusion Detection
Artificial Intelligence and Machine Learning models (specifically ensemble trees like XGBoost and incremental online estimators like SGDClassifier) excel at high-dimensional pattern recognition. By capturing statistical flow metrics (e.g., connection durations, byte rates, error flags, host access patterns), AI-driven NIDS can detect novel intrusion patterns without requiring explicit attack signatures.

---

## 4. Objectives

### 4.1 Primary Objectives
1. **Live Network Ingestion Engine**: Implement a real-time packet capture module capable of assembling raw network packets into 41+ flow features matching NSL-KDD / CIC flow schemas.
2. **Decoupled Asynchronous Architecture**: Build a high-performance backend using FastAPI, Redis pub/sub message brokering, and Celery task workers to isolate packet sniffing from ML inference and UI rendering.
3. **Interactive SOC Dashboard**: Construct a modern React-based user interface displaying live network throughput, threat severity distribution, real-time alert streams, and interactive flow charts.
4. **MLOps & Model Lifecycle**: Provide an administrative suite to upload, evaluate, switch, and benchmark multiple ML models (XGBoost, RandomForest, Neural Networks, SGD Out-of-Core) dynamically.

### 4.2 Secondary Objectives
1. **Explainable AI (XAI)**: Integrate SHAP (SHapley Additive exPlanations) to provide feature attribution scores for individual flagged threats, allowing analysts to understand *why* a flow was classified as malicious.
2. **Automated Report Generation**: Enable exporting of compliance-ready PDF/CSV summary reports for security audits.
3. **Role-Based Access Control (RBAC)**: Implement secure JWT-based authentication with fine-grained permissions (Admin, Analyst, Viewer).

### 4.3 Long-Term Product Vision (Version 3.0+)
- **Active Intrusion Prevention (NIPS)**: Automated integration with Linux IPTables / eBPF XDP to automatically drop or rate-limit malicious traffic in real time.
- **Distributed Agent Architecture**: Lightweight edge agents deployed across multiple subnet nodes reporting back to a centralized cloud management control plane.
- **Deep Learning Sequence Modeling**: Integration of Transformer and BiLSTM architectures for temporal sequence flow modeling.

---

## 5. Scope

```
+-------------------------------------------------------------------------------+
|                                VERSION 2.0 SCOPE                              |
|  +---------------------+  +----------------------+  +----------------------+  |
|  | Live Packet Capture |  | Decoupled FastAPI/   |  | React/TypeScript     |  |
|  | & Flow Processing   |  | Redis / PostgreSQL   |  | SOC UI Dashboard     |  |
|  +---------------------+  +----------------------+  +----------------------+  |
|  +---------------------+  +----------------------+  +----------------------+  |
|  | Multi-Model MLOps   |  | Explainable AI       |  | JWT RBAC & Audit     |  |
|  | & Active Switching  |  | (SHAP Feature Import)|  | Logging Subsystem    |  |
|  +---------------------+  +----------------------+  +----------------------+  |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                            FUTURE VERSION 3.0 SCOPE                           |
|  +---------------------+  +----------------------+  +----------------------+  |
|  | Active NIPS Blocking|  | eBPF / XDP High-     |  | Distributed Multi-   |  |
|  | (IPTables / XDP)    |  | Speed Filtering      |  | Agent Architecture   |  |
|  +---------------------+  +----------------------+  +----------------------+  |
+-------------------------------------------------------------------------------+
```

### 5.1 Version 2.0 In-Scope Functional & Architectural Modules
- **Authentication & RBAC**: User registration, login, JWT token refresh, role management (Admin, Analyst, Viewer).
- **Live Packet Capture**: Scapy-based network tap, socket binding, packet header extraction, dynamic flow windowing.
- **Batch CSV Ingestion**: Legacy support for uploading single/bulk CSV flow logs for offline analysis and benchmarking.
- **Prediction Engine**: Dual-mode execution (High-Accuracy In-Memory XGBoost vs. Memory-Bounded SGD Out-of-Core).
- **Alerting & Notification**: WebSocket real-time alerts, threshold configuration, email/webhook integration hooks.
- **SOC Visualization Dashboard**: Interactive charts (Chart.js / Recharts), throughput gauges, alert feed, category breakdown.
- **Explainability (XAI)**: SHAP-based feature importance breakdown for high-risk predictions.
- **Persistence & History**: PostgreSQL relational storage for alerts, audit logs, flow history, and user configurations.
- **Containerized Deployment**: Multi-stage `docker-compose` production configuration with health checks.

### 5.2 Future Version 3.0 Scope (Explicitly Planned for Next Iteration)
- Inline IPS auto-blocking via Linux `netfilter` / `iptables` / `eBPF`.
- Cloud-native distributed collector nodes (gRPC telemetry stream).
- Automated hyperparameter optimization (Optuna integration).

### 5.3 Out-of-Scope (Explicitly Excluded from Version 2.0)
- Deep packet inspection (DPI) of encrypted payload contents (TLS/SSL decryption).
- Custom hardware appliance / FPGA acceleration design.
- Proprietary SIEM vendor commercial integrations (Splunk Enterprise app store packaging).

---

## 6. Stakeholders

| Stakeholder Role | Primary Interest / Goal | Technical Expertise | System Impact |
| :--- | :--- | :--- | :--- |
| **Cybersecurity Student** | Study network security concepts, test attack scenarios, gain practical portfolio experience. | Intermediate | Primary end user, relies on clear visualizations and documented setup. |
| **Academic / ML Researcher** | Evaluate model performance, benchmark algorithms against NSL-KDD, test out-of-core scaling. | Advanced (ML) | Uses model management suite, dataset evaluation, and metrics exporter. |
| **SOC Analyst (Tier 1/2)** | Monitor real-time alert feeds, triage network anomalies, investigate flagged suspicious flows. | Advanced (Sec) | Operates live dashboard, alert management, and SHAP explainability views. |
| **Network Administrator** | Ensure zero network disruption, monitor interface traffic throughput, configure sniffer interfaces. | Advanced (Net) | Configures packet capture settings, network interface bindings, system limits. |
| **System Administrator / DevOps** | Deploy platform reliably, maintain container health, manage database backups, monitor resources. | Advanced (Ops) | Manages Docker containers, PostgreSQL/Redis instances, environment configs. |
| **Technical Recruiter / Examiner** | Evaluate architectural quality, code organization, security practices, project completeness. | Varied | Assesses GitHub repository structure, SRS completeness, and system demo. |
| **Open-Source Community** | Extend functionality, submit bug fixes, adapt software for research or enterprise environments. | Intermediate - Adv | Consumes clean code, API specifications, modular architecture, unit tests. |

---

## 7. User Personas

### 7.1 Persona 1: Alex Chen - Cybersecurity Graduate Student & Researcher
- **Background**: Master’s student specializing in Applied Machine Learning for Network Defense.
- **Goals**: Wants a clean, well-documented platform to test novel classification algorithms on live network traffic and compare results against offline benchmark datasets.
- **Pain Points**: Existing open-source tools are either academic Jupyter Notebooks with no live capture capabilities or enterprise tools with complex licensing.
- **Expected Features**: Easy model upload interface, side-by-side metric comparison (F1, Recall, Precision), SHAP attribution plots, clear CSV export.

### 7.2 Persona 2: Marcus Vance - Tier 2 SOC Analyst
- **Background**: Enterprise SOC Analyst with 4 years of experience monitoring multi-gigabyte corporate networks.
- **Goals**: Needs rapid identification of malicious network anomalies (specifically high-risk U2R and R2L threats) without being drowned in false positives.
- **Pain Points**: Generic IDS solutions generate high volume of noisy alerts without explaining *why* an alert triggered, leading to analyst fatigue.
- **Expected Features**: Real-time WebSocket alert notifications, categorical threat severity tags (Critical, High, Medium, Low), detailed flow attribute inspector, SHAP explainability breakdown.

### 7.3 Persona 3: Elena Rostova - Senior Network Administrator
- **Background**: Infrastructure engineer managing campus network switches, firewalls, and edge routing.
- **Goals**: Wants an intrusion detection tool that can bind to mirror ports without consuming excessive RAM or causing network performance degradation.
- **Pain Points**: Heavy IDS applications crash due to memory leaks under high flow rates, impacting gateway stability.
- **Expected Features**: Memory-bounded Out-of-Core streaming mode, network interface selector, live packet loss/drop counters, containerized microservice deployment.

### 7.4 Persona 4: Dr. Aris Thorne - Machine Learning Engineer & Educator
- **Background**: University Professor and ML consultant evaluating portfolio projects for production architectural standards.
- **Goals**: Evaluates software for architectural separation, secure coding standards (OWASP), thorough requirements, and robust ML validation.
- **Pain Points**: Student projects frequently feature monolithic Flask scripts, hardcoded credentials, and deceptive accuracy metrics on imbalanced datasets.
- **Expected Features**: Strict API modularity, decoupled frontend/backend, comprehensive SRS and API docs, multi-metric evaluations (Macro F1, Confusion Matrix).

---

## 8. Functional Requirements

Requirements are categorized by module. Each requirement contains a unique ID, Priority (**P1: Critical**, **P2: High**, **P3: Medium**), Description, and explicit Acceptance Criteria.

### 8.1 Module 1: Authentication & User Management (AUTH)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-AUTH-001** | **P1** | The system shall provide secure user login authentication using email/username and password. | Password must be hashed using bcrypt (cost factor $\ge 12$). System returns a signed JWT access token (15-min expiry) and refresh token (7-day expiry). |
| **FR-AUTH-002** | **P1** | The system shall enforce Role-Based Access Control (RBAC) across three distinct user roles: `Admin`, `Analyst`, and `Viewer`. | `Viewer` can only read dashboard metrics; `Analyst` can trigger captures and export reports; `Admin` can manage users, configurations, and ML models. |
| **FR-AUTH-003** | **P2** | The system shall support user registration with email verification and password complexity checks. | Passwords must require min 12 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char. |
| **FR-AUTH-004** | **P2** | The system shall provide an endpoint to refresh expired JWT access tokens using a valid HTTP-only refresh cookie. | GET `/api/v2/auth/refresh` validates refresh token signature in DB and issues new short-lived access token. |
| **FR-AUTH-005** | **P3** | The system shall log all successful and failed authentication attempts with client IP and timestamp. | Audit table stores event type, user_id, ip_address, user_agent, and timestamp. |

### 8.2 Module 2: Dashboard & Visualization Engine (DASH)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-DASH-001** | **P1** | The dashboard shall display live network throughput metrics (Packets/Sec, Bytes/Sec, Active Flows). | Gauges and time-series charts update every 1,000 ms via WebSocket connections. |
| **FR-DASH-002** | **P1** | The dashboard shall display threat distribution breakdowns categorized into 5 primary classes: Normal, DOS, PROBE, R2L, U2R. | Dynamic Doughnut/Pie chart updates in real-time as predictions are generated. |
| **FR-DASH-003** | **P1** | The dashboard shall display a real-time stream of detected threat alerts with color-coded severity indicators. | Table updates seamlessly without page refresh; severity colors: Red (Critical/U2R), Orange (High/R2L), Yellow (Medium/DOS), Blue (Low/PROBE), Green (Normal). |
| **FR-DASH-004** | **P2** | The dashboard shall provide interactive filtering by date range, attack category, confidence threshold, and network interface. | Filters immediately update chart views and flow tables without full backend reload. |
| **FR-DASH-005** | **P2** | The dashboard shall display system resource utilization gauges (CPU, RAM, Disk I/O, Worker Status). | System status bar displays live stats fetched from `/api/v2/system/health`. |

### 8.3 Module 3: Inference & Prediction Engine (PRED)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-PRED-001** | **P1** | The engine shall accept raw 41-feature flow records (JSON or CSV stream) and execute ML inference. | Endpoint `/api/v2/predict/batch` processes array of flows and returns predicted class, category probability vector, and inference latency. |
| **FR-PRED-002** | **P1** | The engine shall support dual execution pipelines: High-Accuracy In-Memory (XGBoost) and Memory-Bounded Out-of-Core (SGDClassifier). | Engine dynamically routes inference based on active model selection without service restart. |
| **FR-PRED-003** | **P2** | The engine shall compute SHAP feature importance attributions for high-severity threat detections (U2R, R2L, DOS). | Response includes top 5 feature contribution scores explaining why the flow was flagged. |
| **FR-PRED-004** | **P2** | The engine shall sanitize and impute missing or infinite flow feature values prior to model prediction. | Preprocessor replaces `NaN`/`Inf` values with training set medians and scales continuous variables using pre-fitted `StandardScaler` artifacts. |
| **FR-PRED-005** | **P3** | The engine shall support configurable probability decision thresholds per attack category. | Admins can lower U2R detection threshold (e.g., to 0.3) to maximize recall on minority attack vectors. |

### 8.4 Module 4: Live Packet Capture & Ingestion (CAP)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-CAP-001** | **P1** | The capture engine shall bind to specified network interfaces (e.g., `eth0`, `wlan0`, `lo`) and capture live IP traffic. | Administrator selects target interface via UI; system initializes background socket capture loop using Scapy/PyPcap. |
| **FR-CAP-002** | **P1** | The engine shall assemble raw packets into flow sessions and extract 41 NSL-KDD compliant features in real time. | Flow accumulator computes connection duration, protocol type, service, flag, src/dst byte counts, and host error rates over sliding window buffers. |
| **FR-CAP-003** | **P2** | The capture engine shall support BPF (Berkeley Packet Filter) syntax to filter captured traffic. | Users can input BPF strings (e.g., `tcp port 80 or tcp port 443`) to limit sniffing scope. |
| **FR-CAP-004** | **P2** | The capture subsystem shall execute in a dedicated, isolated worker thread/process to prevent UI blockages. | Packet sniffing runs asynchronously via Celery worker/multiprocessing without dropping backend HTTP request responsiveness. |
| **FR-CAP-005** | **P3** | The capture engine shall detect packet drop rates and log buffer overflow metrics. | Interface metrics tab displays total captured vs. dropped packets by kernel buffers. |

### 8.5 Module 5: Alerting & Notification Pipeline (ALT)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-ALT-001** | **P1** | The system shall dispatch instant alert notifications over WebSockets when a predicted flow exceeds severity thresholds. | WebSockets push payload containing alert ID, timestamp, source IP, attack type, and confidence score within 50ms of prediction. |
| **FR-ALT-002** | **P2** | The system shall support outbound Webhooks (Slack, Discord, Custom HTTP POST) for Critical/High alerts. | Configured webhook receives formatted JSON payload with alert metadata when U2R or R2L attacks occur. |
| **FR-ALT-003** | **P2** | The system shall allow analysts to acknowledge, dismiss, or tag alerts with resolution notes. | Analysts can update alert state from `NEW` to `ACKNOWLEDGED`, `FALSE_POSITIVE`, or `RESOLVED`. |
| **FR-ALT-004** | **P3** | The system shall support automated alert aggregation/deduplication to prevent alert storms during floods. | Multiple identical attack events from the same source within a 5-second window are aggregated into a single alert with a count multiplier. |

### 8.6 Module 6: Reporting & Export Engine (REP)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-REP-001** | **P1** | The system shall export filtered prediction logs and alert histories to CSV and JSON formats. | User clicks "Export"; system generates downloadable file matching current active filter criteria. |
| **FR-REP-002** | **P2** | The system shall generate comprehensive executive PDF security summary reports. | PDF includes executive overview, attack volume breakdown, top targeted ports, model performance stats, and recommended remediation steps. |
| **FR-REP-003** | **P3** | The system shall support scheduled daily/weekly report generation sent via SMTP email. | Background scheduler runs cron task to send executive summary PDF to configured recipient list. |

### 8.7 Module 7: History & Audit Logging (HIST)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-HIST-001** | **P1** | The system shall persist all classified flows, predictions, and metadata into PostgreSQL storage. | Historical flow record table stores timestamp, 41 raw features, predicted label, actual label (if verified), model ID, and execution latency. |
| **FR-HIST-002** | **P1** | The system shall log all administrative actions (model updates, configuration changes, user role modifications). | Audit log table captures user_id, action, target_resource, previous_state, new_state, timestamp. |
| **FR-HIST-003** | **P2** | The history module shall support paginated, multi-criterion database queries with sub-second response times. | API endpoint `/api/v2/history` returns paginated results (50 items/page) with full-text search and column sorting. |

### 8.8 Module 8: System Administration & Health (ADM)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-ADM-001** | **P1** | The system shall expose health check endpoints for container orchestrators (`/health/live`, `/health/ready`). | Returns HTTP `200 OK` with JSON indicating DB connectivity, Redis status, ML model availability, and disk space. |
| **FR-ADM-002** | **P2** | Admins shall be able to clear cache buffers, reset test databases, and prune old alert history. | Admin interface provides trigger buttons with mandatory "Confirm" modal dialogs. |
| **FR-ADM-003** | **P2** | The system shall monitor network interface statistics and hardware utilization. | Admin status panel reports RAM, CPU, disk usage, active socket listeners, and worker thread counts. |

### 8.9 Module 9: Model Management & MLOps (MDL)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-MDL-001** | **P1** | The system shall provide a model registry to store, version, and activate ML model artifacts (`.pkl`, `.onnx`, `.joblib`). | Admins can view uploaded models, set `active=True` for a selected model, and view artifact creation metadata. |
| **FR-MDL-002** | **P1** | The system shall allow hot-swapping active classification models without downtime or server restarts. | Switching active model instantly updates inference worker pipeline state; incoming predictions immediately use new model. |
| **FR-MDL-003** | **P2** | The system shall track and display evaluation metrics for all registered models on standard validation datasets. | Registry displays Accuracy, Macro F1, Weighted F1, DOS F1, Normal F1, PROBE F1, R2L Recall, U2R Recall, and confusion matrix. |
| **FR-MDL-004** | **P2** | The system shall support incremental model retraining on newly collected and verified network flow datasets. | Admin can trigger background retraining task (e.g. SGD Out-of-Core `partial_fit` or XGBoost retrain) using historical stored flows. |
| **FR-MDL-005** | **P3** | The system shall monitor data drift by comparing incoming live flow feature distributions against training baseline distributions. | System calculates Population Stability Index (PSI); flags warning alert if PSI $> 0.25$ for critical features. |

### 8.10 Module 10: Settings & System Configurations (SET)

| Requirement ID | Priority | Description | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| **FR-SET-001** | **P1** | The system shall persist environment and system settings securely in database/environment configurations. | Admin UI allows modifying global alert thresholds, packet buffer sizes, email SMTP configs, and log levels. |
| **FR-SET-002** | **P2** | The system shall support dark/light theme toggles and responsive layout adjustments in the user interface. | UI preferences persist across user sessions in local storage and user profile DB. |

---

## 9. Non-Functional Requirements

### 9.1 Performance & Latency (PERF)

```
[Raw Network Packet] ---> (Scapy Header Extractor: <15ms)
                             │
                             ▼
[41-Feature Flow Vector] -> (XGBoost / SGD Inference: <10ms)
                             │
                             ▼
[Prediction + SHAP] ------> (PostgreSQL Log & Redis Pub: <15ms)
                             │
                             ▼
[WebSocket Push to UI] ---> (Render Alert on React SOC Dashboard: <10ms)
-------------------------------------------------------------------------
TOTAL END-TO-END LATENCY TARGET: ≤ 50ms
```

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-PERF-001** | Inference Speed | $\le 15\text{ ms}$ per flow | Single flow prediction latency shall not exceed 15ms under 95th percentile load. |
| **NFR-PERF-002** | End-to-End Latency | $\le 50\text{ ms}$ total | Time elapsed from packet arrival at network interface to WebSocket UI render shall be $\le 50\text{ ms}$. |
| **NFR-PERF-003** | Batch Processing | $\ge 5,000\text{ flows/sec}$ | CSV batch prediction pipeline shall process at least 5,000 flow records per second in in-memory mode. |
| **NFR-PERF-004** | API Response Time | $\le 200\text{ ms}$ (99th percentile) | Standard non-ML REST API requests (dashboard stats, history queries) shall respond in under 200ms. |

### 9.2 Security & Data Protection (SEC)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-SEC-001** | Authentication | JWT + Bcrypt | Passwords must be hashed using bcrypt ($cost \ge 12$). JWT tokens signed with SHA-256 (min 256-bit secret key). |
| **NFR-SEC-002** | Transport Security | TLS 1.3 Encryption | All client-server communications, WebSockets, and API endpoints must mandate HTTPS/WSS in non-dev environments. |
| **NFR-SEC-003** | Input Sanitization | OWASP Top 10 | All inputs must be strictly validated against Pydantic schemas. Protection against SQLi, XSS, CSRF, Path Traversal, and Command Injection must be verified via automated security testing. |
| **NFR-SEC-004** | Least Privilege | Non-root containers | Docker containers for web backend and Celery workers must execute under dedicated non-root users (`uid: 10001`). Socket sniffing process must use Linux capabilities (`CAP_NET_RAW`, `CAP_NET_ADMIN`) rather than full `root`. |

### 9.3 Availability & Fault Tolerance (AVAIL)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-AVAIL-001** | System Uptime | 99.9% Uptime | Backend architecture must tolerate worker thread restarts without dropping active HTTP sessions or UI connections. |
| **NFR-AVAIL-002** | Database Resiliency | Graceful degradation | If PostgreSQL connection fails, incoming alerts must queue in Redis memory buffer without crashing the capture engine. |

### 9.4 Reliability & Data Integrity (REL)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-REL-001** | Out-of-Core Memory | Zero OOM Crashes | Under sustained multi-gigabyte log ingestion, memory footprint shall remain strictly bounded ($\le 512\text{ MB}$ RAM for streaming processes). |
| **NFR-REL-002** | Data Consistency | Zero loss of alerts | High-severity alerts (U2R/R2L) must be committed to persistent disk storage within 100ms of detection. |

### 9.5 Maintainability & Architecture (MAINT)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-MAINT-001** | Modular Separation | Clean Code Architecture | Backend code must follow strict separation of concerns: Routers -> Services -> Repositories -> Models. |
| **NFR-MAINT-002** | Test Coverage | $\ge 85\%$ Code Coverage | Unit and integration test suite (pytest) must cover $>85\%$ of backend code paths, including preprocessors and routes. |
| **NFR-MAINT-003** | Type Hints & Linting | Zero PEP8 / Flake8 errors | All Python code must strictly enforce static typing (`mypy`) and pass code linting (`ruff`, `black`). |

### 9.6 Scalability & Resource Allocation (SCALE)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-SCALE-001** | Horizontal Workers | Linear worker scaling | System performance shall scale horizontally by adding Celery inference worker containers subscribed to Redis queues. |
| **NFR-SCALE-002** | DB Connection Pool | Dynamic pooling | PostgreSQL connection pool scales dynamically up to 50 concurrent connections using `SQLAlchemy` async connection pooling. |

### 9.7 Usability & Accessibility (USE)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-USE-001** | Response UX | Immediate Feedback | Interactive UI actions (button clicks, filter updates, model switches) must visually respond within 100ms. |
| **NFR-USE-002** | Accessibility | WCAG 2.1 Level AA | Color contrasts, font sizes, and ARIA labels in the Web UI must meet WCAG 2.1 AA standards. |

### 9.8 Portability & Containerization (PORT)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-PORT-001** | Multi-OS Support | Cross-Platform | Platform shall run on Linux (Ubuntu 20.04+), macOS (ARM64/x86), and Windows 11 (via WSL2/Docker Desktop). |
| **NFR-PORT-002** | Docker Deployment | Single command startup | Complete environment (FastAPI, React, PostgreSQL, Redis, Worker) shall launch via single `docker-compose up --build` command. |

### 9.9 Logging, Telemetry & Observability (LOG)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-LOG-001** | Structured Logging | JSON Log Format | All backend logs must be output in structured JSON format with fields: `timestamp`, `level`, `module`, `correlation_id`, `message`. |
| **NFR-LOG-002** | Telemetry Metrics | Prometheus Endpoint | System shall expose standard `/metrics` endpoint formatted for Prometheus scraping (request counts, latency histograms, prediction counters). |

### 9.10 Compliance & Regulatory Standards (COMP)

| NFR ID | Category | Target Metric | Description & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **NFR-COMP-001** | NIST SP 800-94 | Security Logging | Logging structures comply with NIST Guidelines on Intrusion Detection and Prevention Systems (IDPS). |
| **NFR-COMP-002** | GDPR / Privacy | No PII Capture | System captures only network flow header statistics; no sensitive packet payload data or PII is recorded. |

---

## 10. System Constraints

### 10.1 Budgetary Constraints
- **Zero Software Licensing Cost**: Platform must be constructed exclusively using open-source libraries, frameworks, and tools (Python, Scikit-learn, XGBoost, FastAPI, React, PostgreSQL, Docker).
- **Resource-Efficient Infrastructure**: Platform must be deployable on basic developer laptops or modest cloud instances (e.g., 2 vCPU, 4GB RAM cloud VM).

### 10.2 Hardware Constraints
- **Minimum Requirements**: Dual-core x86_64 or ARM64 processor, 4 GB RAM, 10 GB free disk space.
- **Recommended Requirements**: Quad-core CPU, 8 GB+ RAM, Dedicated Gigabit Network Interface Controller (NIC).

### 10.3 Operating System Constraints
- **Target OS Environments**: Linux (Ubuntu 22.04 LTS recommended for raw socket capture), macOS, Windows 11 (WSL2 required for native raw packet capture support).
- **Kernel Privileges**: Packet sniffing requires elevated Linux capabilities (`CAP_NET_RAW` / `CAP_NET_ADMIN`) or administrative privileges on the target NIC.

### 10.4 Python Runtime Constraints
- **Python Version**: Python 3.10 or 3.11 required (for optimal async performance and C-extension library compatibility).
- **Dependency Isolation**: All Python dependencies must be strictly isolated via virtual environments (`venv`) or Docker container volumes.

### 10.5 Network Permission Constraints
- Interface packet sniffing requires promiscuous mode binding permission on target physical or virtual network switches.

---

## 11. Assumptions

1. **Dataset Representation**: The 41 features defined in the NSL-KDD benchmark represent a valid statistical abstraction of IP flow characteristics.
2. **Network Tap Availability**: The deployment environment allows binding network sockets to an active network interface or mirror/SPAN port.
3. **Model Pre-Training**: Initial system deployment includes pre-trained XGBoost and SGDClassifier model artifacts (`.pkl`) ready for immediate cold-start inference.
4. **Asynchronous Client Support**: Modern browser clients connecting to the dashboard support HTML5 WebSockets and ES6+ JavaScript.
5. **Trusted Internal Network**: The database (PostgreSQL) and message broker (Redis) run within an isolated container network, protected from direct exposure to public internet traffic.

---

## 12. System Dependencies

### 12.1 Technical Stack & Dependency Blueprint

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND TIER                                     |
|  React 18  |  TypeScript  |  Tailwind CSS  |  Chart.js / Recharts  |  Lucide Icons  |
+-----------------------------------------------------------------------------------+
                                        │ (REST / WebSockets)
                                        ▼
+-----------------------------------------------------------------------------------+
|                                  BACKEND API TIER                                 |
|  FastAPI (Python 3.10+)  |  Uvicorn (ASGI)  |  Pydantic v2  |  SQLAlchemy (Async)|
+-----------------------------------------------------------------------------------+
                     │                                           │
                     ▼                                           ▼
+------------------------------------------+  +-------------------------------------+
|        DATA & MESSAGING INFRASTRUCTURE   |  |     ML INFERENCE & CAPTURE TIER     |
| PostgreSQL 15 | Redis 7 (Pub/Sub & Cache)|  | Scapy | XGBoost | Scikit-learn | SHAP|
+------------------------------------------+  +-------------------------------------+
                                        │
                                        ▼
+-----------------------------------------------------------------------------------+
|                              DEPLOYMENT INFRASTRUCTURE                            |
|     Docker Engine  |  Docker Compose  |  Prometheus Exporter  |  Gunicorn/Uvicorn   |
+-----------------------------------------------------------------------------------+
```

| Dependency Category | Technology / Library | Version Constraint | Role & Purpose |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python | `^3.10` | Core backend logic, packet processing, and ML execution environment. |
| **Backend Framework**| FastAPI | `^0.100.0` | High-performance asynchronous REST API and WebSocket controller. |
| **ASGI Web Server** | Uvicorn / Gunicorn | `^0.22.0` | Production ASGI web server running asynchronous request loops. |
| **Data Processing** | NumPy & Pandas | `^1.24.0` | Array manipulation, data matrix transformations, and flow processing. |
| **Machine Learning** | Scikit-Learn | `^1.3.0` | Preprocessing (`StandardScaler`, `ColumnTransformer`), `RandomForest`, `SGDClassifier`. |
| **Machine Learning** | XGBoost | `^1.7.0` | High-accuracy gradient boosted decision tree classifier. |
| **Explainability** | SHAP | `^0.42.0` | SHapley Additive exPlanations for feature attribution plots. |
| **Packet Capture** | Scapy | `^2.5.0` | Low-level network packet sniffing, header parsing, and flow feature calculation. |
| **Task Queue** | Celery & Redis | `Celery ^5.3`, `Redis ^7.0` | Asynchronous task queue for long-running captures and model retraining. |
| **Relational Database**| PostgreSQL | `^15.0` | Persistent storage for users, alert history, flow records, and system logs. |
| **Database ORM** | SQLAlchemy & Alembic | `^2.0.0` | Asynchronous ORM and database schema migration engine. |
| **Frontend UI** | React & TypeScript | `React ^18.2`, `TS ^5.0` | Single-page application interface for SOC analytics. |
| **Styling & Charts** | Tailwind CSS & Chart.js| `Tailwind ^3.3`, `Chart.js ^4.3` | Modern visual design system and dynamic metric plotting. |
| **Containerization** | Docker & Compose | `Docker ^24.0`, `Compose v2` | Container orchestration and isolated multi-service execution. |

---

## 13. Risk Analysis & Mitigation Matrix

### 13.1 Technical Risks (R-TECH)

| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **R-TECH-01** | High network traffic causes packet drops in Scapy sniffer loop. | **High** | High | High | Implement out-of-core streaming queues, migrate to low-level native sockets (`socket.AF_PACKET`) or `eBPF` bindings if Python GIL throttles capture. |
| **R-TECH-02** | High-dimensional SHAP calculations introduce latency during real-time inference. | **Medium** | High | Medium | Execute SHAP feature attribution asynchronously in background Celery workers only for high-severity alerts (U2R/R2L), avoiding blocking main inference path. |
| **R-TECH-03** | Database storage exhaustion due to millions of logged normal network flows. | **High** | Medium | High | Implement automated database table partitioning by date and a configurable data retention policy (e.g. auto-purge normal flows after 7 days, retain alerts permanently). |

### 13.2 Security Risks (R-SEC)

| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **R-SEC-01** | Unauthorized access to packet capture interface allowing network eavesdropping. | **Critical** | Low | Critical | Strict RBAC enforcement; raw capture triggers restricted exclusively to authenticated `Admin` users with MFA enablement. |
| **R-SEC-02** | Malicious CSV file upload containing malformed inputs or catastrophic regular expression payloads. | **High** | Medium | High | Enforce strict file size limits (50 MB max), schema validation via Pydantic, and sanitization of incoming strings prior to parsing. |

### 13.3 Deployment Risks (R-DEP)

| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **R-DEP-01** | Lack of raw socket access permissions when running inside unprivileged Docker containers. | **High** | Medium | High | Configure precise container privileges in `docker-compose.yml` (`cap_add: [NET_ADMIN, NET_RAW]`) rather than running entire container in privileged mode. |
| **R-DEP-02** | PostgreSQL database schema mismatch during production rolling updates. | **Medium** | Low | Medium | Enforce automated `Alembic` database migrations on container startup with rollback capabilities. |

### 13.4 Machine Learning Risks (R-ML)

| Risk ID | Risk Description | Severity | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **R-ML-01** | Low minority class recall (U2R / R2L) due to severe dataset class imbalance. | **High** | High | High | Employ cost-sensitive sample weighting during model training, apply SMOTE / Focal Loss techniques, and allow customizable lower decision thresholds per class. |
| **R-ML-02** | Concept Drift: Model accuracy degrades over time as network protocols and attack patterns evolve. | **High** | Medium | High | Implement population stability monitoring (PSI) on incoming flow features and provide incremental online retraining workflows (`SGDClassifier.partial_fit`). |

---

## 14. Success Metrics & Key Performance Indicators (KPIs)

```
                       +-----------------------------------+
                       |    SUCCESS METRIC BENCHMARKS      |
                       +-----------------------------------+
                       | Macro F1 Score    |  ≥ 0.85       |
                       | Minority Recall   |  ≥ 0.75       |
                       | False Pos Rate    |  ≤ 2.0%       |
                       | E2E Alert Latency |  ≤ 50 ms      |
                       | Test Coverage     |  ≥ 85%        |
                       | Stream Stability  |  0 OOM Crashes|
                       +-----------------------------------+
```

### 14.1 Machine Learning & Detection Metrics
- **Macro F1 Score**: Overall macro-averaged F1 score $\ge 0.85$ across all 5 attack categories.
- **Minority Class Recall (U2R & R2L)**: Individual recall rate $\ge 0.75$ on unseen test datasets (overcoming V1.0 recall limitations).
- **False Positive Rate (FPR)**: False alert rate on legitimate normal traffic $\le 2.0\%$.
- **Detection Rate (Recall)**: Overall threat detection rate $\ge 90\%$.

### 14.2 System & Operational Performance Metrics
- **End-to-End Latency**: Time from packet capture to UI alert render $\le 50\text{ ms}$.
- **Throughput Capability**: CSV batch processing rate $\ge 5,000\text{ flows/sec}$.
- **Streaming RAM Stability**: Zero Out-of-Core memory leaks over 24-hour continuous packet capture streams ($\le 512\text{ MB}$ RAM footprint).
- **Container Build & Startup**: Cold system deployment (`docker-compose up`) completes within $\le 90\text{ seconds}$.

### 14.3 Engineering & Code Quality Metrics
- **Unit Test Coverage**: Backend code coverage $\ge 85\%$ measured via `pytest-cov`.
- **API Documentation Completeness**: $100\%$ OpenAPI 3.0 endpoint coverage via FastAPI Swagger UI.
- **Code Health**: Zero high-severity lint errors reported by `ruff` and zero type errors reported by `mypy`.

---

## 15. Technical Glossary

| Term | Full Name / Definition |
| :--- | :--- |
| **NIDS** | **Network Intrusion Detection System**: A system that monitors network traffic for suspicious activity and issues alerts when discovered. |
| **NIPS** | **Network Intrusion Prevention System**: An active security appliance that monitors network traffic and automatically drops or blocks malicious flows. |
| **NSL-KDD** | A refined benchmark dataset derived from KDD Cup 99, designed to evaluate intrusion detection systems without duplicate records causing skewed results. |
| **DOS** | **Denial of Service**: An attack class attempting to make a machine or network resource unavailable to its intended users (e.g., SYN flood, Smurf). |
| **PROBE** | **Probing / Port Scanning**: An attack class attempting to gather information about a network of computers for the purpose of circumventing its security controls (e.g., Nmap, IP sweep). |
| **R2L** | **Remote to Local**: An attack class where an attacker who does not have an account on a remote machine gains local access to that machine (e.g., password guessing, buffer overflow). |
| **U2R** | **User to Root**: An attack class where a local non-privileged user attempts to gain root privileges on a local system (e.g., privilege escalation exploit). |
| **Scapy** | A powerful Python-based interactive packet manipulation program and library capable of forging, decoding, and capturing network packets. |
| **eBPF** | **Extended Berkeley Packet Filter**: A revolutionary Linux kernel technology allowing sandboxed programs to run inside the kernel without changing kernel source code, used for high-speed packet filtering. |
| **XGBoost** | **eXtreme Gradient Boosting**: An optimized distributed gradient boosting library designed to be highly efficient, flexible, and portable. |
| **Out-of-Core Processing** | Processing data algorithms designed to handle datasets that exceed main memory (RAM) capacity by streaming data chunks incrementally from storage. |
| **Welford's Algorithm** | An online algorithm for computing running mean and sample variance in a single pass without storing all data points, preventing numerical instability. |
| **SHAP** | **SHapley Additive exPlanations**: A game-theoretic approach to explain the output of any machine learning model by computing feature contribution values. |
| **SOC** | **Security Operations Center**: A centralized unit that deals with security issues on an organizational and technical level. |
| **SIEM** | **Security Information and Event Management**: Software that aggregates and analyzes security log data from across an enterprise network. |
| **SOAR** | **Security Orchestration, Automation, and Response**: Technologies that enable organizations to collect security threats data and automate response workflows. |
| **RBAC** | **Role-Based Access Control**: An approach to restricting system access to authorized users based on defined user roles. |
| **JWT** | **JSON Web Token**: A compact, URL-safe means of representing claims to be transferred between two parties in client-server authentication. |
| **BPF** | **Berkeley Packet Filter**: A syntax and kernel filter mechanism used by tools like Tcpdump and Wireshark to filter specific network traffic. |
| **PSI** | **Population Stability Index**: A financial and ML metric used to measure how much a feature distribution has shifted over time (Data Drift). |

---

## 16. References & Standards

1. **IEEE Std 29148-2018**: *ISO/IEC/IEEE International Standard - Systems and software engineering - Life cycle processes - Requirements engineering*. IEEE Computer Society.
2. **IEEE Std 830-1998**: *IEEE Recommended Practice for Software Requirements Specifications*. IEEE Computer Society.
3. **NIST Special Publication 800-94**: *Guide to Intrusion Detection and Prevention Systems (IDPS)*. National Institute of Standards and Technology.
4. **OWASP Top 10 API Security Risks (2023)**: Open Web Application Security Project (OWASP) Foundation.
5. **Tavallaee, M., Bagheri, E., Lu, W., & Ghorbani, A. A. (2009)**: *A detailed analysis of the KDD CUP 99 data set*. IEEE Symposium on Computational Intelligence for Security and Defense Applications (CISDA).
6. **Chen, T., & Guestrin, C. (2016)**: *XGBoost: A Scalable Tree Boosting System*. ACM SIGKDD International Conference on Knowledge Discovery and Data Mining.
7. **Lundberg, S. M., & Lee, S. I. (2017)**: *A unified approach to interpreting model predictions*. Advances in Neural Information Processing Systems (NeurIPS).
8. **FastAPI Documentation**: *Modern, fast (high-performance), web framework for building APIs with Python 3.8+*. https://fastapi.tiangolo.com/
9. **Scikit-Learn Documentation**: *Machine Learning in Python*. https://scikit-learn.org/
10. **Scapy Packet Capture Library Documentation**: https://scapy.net/
