# REST API Reference Documentation

This document provides the complete API specification for the Network Intrusion Detection System Flask web application.

---

## Base URL
```
http://localhost:5000
```

---

## Endpoints Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | Render the interactive HTML upload dashboard | No |
| `GET` | `/health` | Lightweight status check for containers & load balancers | No |
| `POST` | `/predict` | Ingest CSV file and return intrusion predictions | No |

---

## 1. Get Application UI

- **Endpoint**: `/`
- **Method**: `GET`
- **Description**: Returns the single-page application dashboard styled with Tailwind CSS.
- **Response**: `200 OK` (HTML Document)

---

## 2. System Health Check

- **Endpoint**: `/health`
- **Method**: `GET`
- **Description**: Returns status for Docker health checks, Kubernetes liveness probes, and monitoring servers.

### Success Response (`200 OK`)
```json
{
  "status": "ok"
}
```

---

## 3. Classify CSV Traffic Stream

- **Endpoint**: `/predict`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (File, Required): CSV file containing network flow records with the 41 standard NSL-KDD columns. Maximum allowed file size is 5 MB.

### Success Response (`200 OK`)

```json
{
  "summary": {
    "DOS": {
      "count": 5,
      "percentage": 25.0
    },
    "Normal": {
      "count": 14,
      "percentage": 70.0
    },
    "PROBE": {
      "count": 1,
      "percentage": 5.0
    }
  },
  "predictions": [
    {
      "row": 0,
      "predicted_category": "DOS"
    },
    {
      "row": 1,
      "predicted_category": "Normal"
    },
    {
      "row": 2,
      "predicted_category": "PROBE"
    }
  ]
}
```

---

## Error Handling Specifications

All errors return JSON payloads with structured error messages. Stack traces are sanitized and never exposed to API callers.

### 1. Missing File Upload (`400 Bad Request`)
Returned when no file parameter is submitted in the request body.
```json
{
  "status": "error",
  "message": "No file uploaded"
}
```

### 2. CSV Parse Error (`400 Bad Request`)
Returned when the uploaded file is not valid UTF-8 CSV or contains malformed lines.
```json
{
  "status": "error",
  "message": "Failed to parse CSV file. Ensure it is valid UTF-8 CSV."
}
```

### 3. Missing Required Feature Columns (`400 Bad Request`)
Returned when the input CSV lacks required NSL-KDD columns.
```json
{
  "status": "error",
  "message": "Missing required columns",
  "missing_columns": ["protocol_type", "src_bytes"]
}
```

### 4. Resource Not Found (`404 Not Found`)
Returned when accessing undefined endpoints.
```json
{
  "status": "error",
  "message": "Resource not found"
}
```

### 5. File Size Exceeds Limit (`413 Payload Too Large`)
Returned when file upload exceeds 5 MB.
```json
{
  "status": "error",
  "message": "File too large. Maximum upload size is 5 MB."
}
```

### 6. Internal Server Error (`500 Internal Server Error`)
Returned on unexpected server failures.
```json
{
  "status": "error",
  "message": "An internal server error occurred."
}
```
