"""Pydantic v2 schemas for prediction request/response bodies."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# ── 41 NSL-KDD Feature Names (excludes attack_type and difficulty_level) ──

NSL_KDD_FEATURES: list[str] = [
    "duration", "protocol_type", "service", "flag",
    "src_bytes", "dst_bytes", "land", "wrong_fragment", "urgent",
    "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count",
    "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate",
    "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
    "dst_host_count", "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
]


# ── Request Schemas ──


class PredictRequest(BaseModel):
    """Single-flow prediction request matching the 41 NSL-KDD features."""
    features: Dict[str, object] = Field(
        ...,
        description="Dictionary of 41 NSL-KDD feature name → value pairs",
    )


# ── Response Schemas ──


class ShapContribution(BaseModel):
    feature: str
    value: float


class SinglePredictionResponse(BaseModel):
    predicted_category: str
    confidence_scores: Dict[str, float]
    shap_top_features: List[ShapContribution] = []
    inference_latency_ms: float


class BatchRowPrediction(BaseModel):
    row: int
    predicted_category: str
    confidence_score: float


class CategoryCount(BaseModel):
    count: int
    percentage: float


class BatchPredictionResponse(BaseModel):
    total_rows: int
    summary: Dict[str, CategoryCount]
    predictions: List[BatchRowPrediction]
    inference_latency_ms: float


class FlowHistoryItem(BaseModel):
    id: int
    captured_at: str
    predicted_category: str
    confidence_score: float
    inference_latency_ms: float
    protocol_type: Optional[str] = None

    model_config = {"from_attributes": True}


class PredictionHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[FlowHistoryItem]
