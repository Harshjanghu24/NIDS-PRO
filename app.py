"""Flask web application for the Network Intrusion Detection System.

Provides two routes:
    GET  /         — Upload page (index.html)
    POST /predict  — Accepts a CSV upload, returns per-row predictions + summary
    GET  /health   — Lightweight health-check for container orchestration
"""

import io
import logging
import os

import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException

from preprocessing import load_column_names, load_preprocessor

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory-style initialisation
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Secret key for session signing — read from env, fall back to random bytes.
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

# Cap file uploads at 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# ---------------------------------------------------------------------------
# Load model, preprocessor & label encoder once at startup (not per-request)
# ---------------------------------------------------------------------------
logger.info("Loading model artefacts …")
model = joblib.load("model.pkl")
preprocessor = load_preprocessor("preprocessor.pkl")
label_encoder = joblib.load("label_encoder.pkl")  # None when RF was chosen
logger.info("Model artefacts loaded successfully.")

# The 41 feature columns that prediction input files must contain
# (excludes attack_type and difficulty_level which are unknown for new data)
_all_cols = load_column_names()
EXPECTED_FEATURE_COLS: list[str] = [
    c for c in _all_cols if c not in ("attack_type", "difficulty_level")
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Render the main upload page."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Lightweight health-check endpoint for Docker / load balancers."""
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    """Accept a CSV file upload and return per-row predictions + summary."""

    # --- file presence check ------------------------------------------------
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    try:
        # --- read CSV into DataFrame ----------------------------------------
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            df = pd.read_csv(stream)
            if df.empty:
                return jsonify({
                    "status": "error",
                    "message": "CSV file is empty.",
                }), 400
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError, Exception) as exc:
            logger.warning("CSV parse failure from '%s': %s", file.filename, exc)
            return jsonify({
                "status": "error",
                "message": "Failed to parse CSV file. Ensure it is valid non-empty UTF-8 CSV.",
            }), 400

        # --- validate columns -----------------------------------------------
        missing = [c for c in EXPECTED_FEATURE_COLS if c not in df.columns]
        if missing:
            return jsonify({
                "status": "error",
                "message": "Missing required columns",
                "missing_columns": missing,
            }), 400

        # Keep only the expected feature columns (in the correct order)
        df = df[EXPECTED_FEATURE_COLS]

        # --- transform & predict --------------------------------------------
        X = preprocessor.transform(df)
        preds = model.predict(X)

        # Decode numeric labels back to category names when needed
        if label_encoder is not None:
            preds = label_encoder.inverse_transform(preds)

        preds = [str(p) for p in preds]

        # --- build summary --------------------------------------------------
        total = len(preds)
        counts: dict[str, int] = {}
        for p in preds:
            counts[p] = counts.get(p, 0) + 1

        summary = {
            category: {
                "count": cnt,
                "percentage": round(cnt / total * 100, 2),
            }
            for category, cnt in sorted(counts.items())
        }

        # --- per-row predictions --------------------------------------------
        predictions = [
            {"row": idx, "predicted_category": cat}
            for idx, cat in enumerate(preds)
        ]

        logger.info("%d rows processed from '%s'", total, file.filename)

        return jsonify({"summary": summary, "predictions": predictions})

    except Exception:
        logger.exception("Prediction failed for '%s'", file.filename)
        return jsonify({
            "status": "error",
            "message": "An internal error occurred. Please try again.",
        }), 500


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error: HTTPException):
    """Handle 404 errors."""
    return jsonify({"status": "error", "message": "Resource not found"}), 404


@app.errorhandler(413)
def file_too_large(error: HTTPException):
    """Handle file uploads that exceed MAX_CONTENT_LENGTH."""
    return jsonify({
        "status": "error",
        "message": "File too large. Maximum upload size is 5 MB.",
    }), 413


@app.errorhandler(500)
def internal_error(error: HTTPException):
    """Handle unexpected server errors."""
    logger.exception("Unhandled 500 error")
    return jsonify({
        "status": "error",
        "message": "An internal server error occurred.",
    }), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
