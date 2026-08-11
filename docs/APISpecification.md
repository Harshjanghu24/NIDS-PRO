# REST & WebSocket API Specification
## AI-Powered Network Intrusion Detection Platform (Version 2.0)

**Document Version:** 2.0.0-DRAFT  
**Protocol Standard:** OpenAPI 3.0.3 & RFC 6455 WebSockets  
**Base URL:** `/api/v2`  
**Authentication Scheme:** HTTP Bearer JWT & HTTP-Only Cookies  
**Status:** Approved for Implementation (Sprint 1 Ready)  
**Authors:** Senior Backend Engineer & Lead API Architect  

---

## 1. Global API Standards & Conventions

### 1.1 Content Negotiation & Encoding
- All REST requests and responses use `Content-Type: application/json` unless handling binary uploads/exports (`multipart/form-data` or `application/pdf`).
- Datetime fields are formatted strictly according to **ISO-8601 UTC** string format (e.g. `2026-08-04T00:35:14Z`).

### 1.2 Unified HTTP Status Code Mapping

| Status Code | Status Name | Operational Context |
| :--- | :--- | :--- |
| `200 OK` | Successful Execution | Request processed successfully; payload returned. |
| `201 Created` | Resource Created | User registered, model artifact registered, alert created. |
| `202 Accepted` | Async Processing | Asynchronous task (e.g., CSV prediction batch) queued. |
| `400 Bad Request` | Invalid Operation | Malformed syntax or invalid state transition. |
| `401 Unauthorized` | Authentication Failure| Missing, invalid, or expired JWT access token. |
| `403 Forbidden` | Access Denied | User role insufficient (e.g. `Viewer` triggering packet capture). |
| `404 Not Found` | Resource Missing | Specified model ID, alert ID, or endpoint not found. |
| `422 Unprocessable`| Validation Failure | Input payload failed Pydantic schema validation. |
| `429 Too Many Req` | Rate Limit Exceeded | Client exceeded configured request rate limit. |
| `500 Internal Error`| Server Failure | Unhandled internal exception; returns correlation ID. |

---

## 2. Authentication & Authorization Routes (`/api/v2/auth`)

### 2.1 `POST /api/v2/auth/login`
- **Description**: Authenticates user credentials and issues short-lived JWT access token and refresh cookie.
- **Request Body** (`application/json`):
```json
{
  "username": "marcus_analyst",
  "password": "SecurePassword123!"
}
```
- **Responses**:
  - `200 OK`: Access token returned; refresh token set in HTTP-Only cookie.
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "username": "marcus_analyst",
    "email": "marcus@enterprise.sec",
    "role": "ANALYST"
  }
}
```
  - `401 Unauthorized`: Invalid credentials.

### 2.2 `POST /api/v2/auth/refresh`
- **Description**: Exchanging a valid HTTP-Only refresh cookie for a new short-lived JWT access token.
- **Responses**: `200 OK` (New Access Token), `401 Unauthorized` (Expired/Invalid Refresh Cookie).

---

## 3. Prediction & Inference Routes (`/api/v2/predict`)

### 3.1 `POST /api/v2/predict/realtime`
- **Description**: Evaluates single 41-feature flow vector for real-time intrusion classification.
- **Security**: Requires `ANALYST` or `ADMIN` role.
- **Request Body** (`application/json`):
```json
{
  "duration": 0.0,
  "protocol_type": "tcp",
  "service": "http",
  "flag": "SF",
  "src_bytes": 215,
  "dst_bytes": 45076,
  "land": 0,
  "wrong_fragment": 0,
  "urgent": 0,
  "count": 1,
  "srv_count": 1,
  "serror_rate": 0.0,
  "srv_serror_rate": 0.0,
  "same_srv_rate": 1.0,
  "diff_srv_rate": 0.0,
  "dst_host_count": 255,
  "dst_host_srv_count": 255,
  "dst_host_same_srv_rate": 1.0,
  "dst_host_diff_srv_rate": 0.0
}
```
- **Response** (`200 OK`):
```json
{
  "flow_id": 1029384,
  "predicted_category": "Normal",
  "confidence_score": 0.9842,
  "probabilities": {
    "Normal": 0.9842,
    "DOS": 0.0112,
    "PROBE": 0.0031,
    "R2L": 0.0010,
    "U2R": 0.0005
  },
  "shap_attributions": null,
  "inference_latency_ms": 7.42,
  "active_model_version": "v2.1.0-xgboost"
}
```

### 3.2 `POST /api/v2/predict/csv`
- **Description**: Upload bulk CSV flow dataset for async batch processing.
- **Request**: `multipart/form-data` with `file` payload (<50MB).
- **Response** (`202 Accepted`):
```json
{
  "task_id": "task-789a0b1c-2d3e",
  "status": "QUEUED",
  "message": "CSV batch prediction task queued successfully.",
  "status_poll_url": "/api/v2/tasks/task-789a0b1c-2d3e"
}
```

---

## 4. Live Packet Capture Routes (`/api/v2/capture`)

### 4.1 `POST /api/v2/capture/start`
- **Description**: Binds to target OS network interface and initiates background packet sniffer loop.
- **Security**: Requires `ADMIN` role.
- **Request Body**:
```json
{
  "interface_name": "eth0",
  "bpf_filter": "tcp port 80 or tcp port 443",
  "promiscuous_mode": true
}
```
- **Response** (`200 OK`):
```json
{
  "status": "RUNNING",
  "interface_name": "eth0",
  "bpf_filter": "tcp port 80 or tcp port 443",
  "started_at": "2026-08-04T00:35:14Z"
}
```

### 4.2 `POST /api/v2/capture/stop`
- **Description**: Stops active background packet sniffer loop.

---

## 5. Alerts & Triage Routes (`/api/v2/alerts`)

### 5.1 `GET /api/v2/alerts`
- **Description**: Fetch paginated, multi-criterion filtered alert stream.
- **Query Parameters**:
  - `page`: int (Default: `1`)
  - `page_size`: int (Default: `50`)
  - `category`: string (Optional: `DOS`, `PROBE`, `R2L`, `U2R`)
  - `severity`: string (Optional: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
  - `status`: string (Optional: `NEW`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_POSITIVE`)
- **Response** (`200 OK`):
```json
{
  "items": [
    {
      "id": "c9d8e7f6-a5b4-3c2d-1e0f-9a8b7c6d5e4f",
      "flow_id": 1029390,
      "alert_timestamp": "2026-08-04T00:35:10Z",
      "attack_category": "U2R",
      "severity_level": "CRITICAL",
      "status": "NEW",
      "shap_attributions": {
        "num_root": 0.421,
        "root_shell": 0.284,
        "su_attempted": 0.152
      }
    }
  ],
  "total_count": 142,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

---

## 6. MLOps & Model Registry Routes (`/api/v2/models`)

### 6.1 `GET /api/v2/models`
- **Description**: List all registered ML model artifacts, versions, and validation metrics.

### 6.2 `PUT /api/v2/models/{model_id}/activate`
- **Description**: Hot-swaps the active classification model in production.
- **Security**: Requires `ADMIN` role.

---

## 7. Real-Time WebSocket Specifications (`/api/v2/ws`)

### 7.1 `GET /api/v2/ws/alerts`
- **Protocol**: WebSocket (`wss://`)
- **Authentication**: Query parameter token (`?token=<JWT_TOKEN>`)
- **Direction**: Server-to-Client Push
- **Sample Event Payload**:
```json
{
  "event_type": "THREAT_ALERT",
  "timestamp": "2026-08-04T00:35:14Z",
  "data": {
    "alert_id": "c9d8e7f6-a5b4-3c2d-1e0f-9a8b7c6d5e4f",
    "attack_category": "U2R",
    "severity_level": "CRITICAL",
    "confidence": 0.965,
    "source_ip": "192.168.1.105",
    "destination_port": 22,
    "shap_attributions": {
      "num_root": 0.421,
      "root_shell": 0.284
    }
  }
}
```

### 7.2 `GET /api/v2/ws/metrics`
- **Protocol**: WebSocket (`wss://`)
- **Direction**: Server-to-Client Push (Every 1,000ms)
- **Sample Event Payload**: Live system throughput, packets/sec, bytes/sec, active flow count, and worker RAM usage.
