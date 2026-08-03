# Future Work & Project Roadmap

This document outlines planned enhancements, research directions, and architectural upgrades for future iterations of the Network Intrusion Detection System.

---

## 1. Feature & Model Enhancements

- [ ] **SHAP & LIME Explainability**: Implement local instance explainability to provide security analysts with feature attribution explanations for each flagged malicious flow (e.g. *"Flagged as DOS because dst_host_serror_rate > 0.8 and service = eco_i"*).
- [ ] **Deep Learning Architectures**: Benchmark Bidirectional LSTM (BiLSTM) and Temporal Convolutional Networks (TCN) for sequential packet flow analysis.
- [ ] **Cost-Sensitive Loss Optimization**: Implement custom Focal Loss functions in XGBoost to further boost U2R recall (currently 17.91%) and R2L recall (currently 6.96%).

---

## 2. Real-Time Network Packet Ingestion

- [ ] **Live Packet Sniffing (Scapy / PyShark Integration)**: Build a network interface sniffer that reconstructs TCP/IP flows in real time, extracts NSL-KDD style session metrics, and passes them to `app.py` via WebSockets.
- [ ] **PCAP File Upload Support**: Enable parsing of raw Wireshark/tcpdump `.pcap` files directly in the web UI.

---

## 3. Platform & Security Hardening

- [ ] **Database Persistence Layer**: Integrate PostgreSQL / TimescaleDB to persist historical alert streams, prediction audit logs, and analyst annotations.
- [ ] **OAuth2 / JWT Authentication**: Add enterprise role-based access control (RBAC) separating Security Analysts, Network Engineers, and System Administrators.
- [ ] **Automated CI/CD Security Scanning**: Integrate Bandit, Safety, and Trivy container vulnerability scanners into GitHub Actions workflows.
