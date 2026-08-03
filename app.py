import io

import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify

from preprocessing import load_column_names, load_preprocessor

app = Flask(__name__)

# Cap file uploads at 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# ---------------------------------------------------------------------------
# Load model, preprocessor & label encoder once at startup (not per-request)
# ---------------------------------------------------------------------------
model = joblib.load("model.pkl")
preprocessor = load_preprocessor("preprocessor.pkl")
label_encoder = joblib.load("label_encoder.pkl")  # None when RF was chosen

# The 41 feature columns that prediction input files must contain
# (excludes attack_type and difficulty_level which are unknown for new data)
_all_cols = load_column_names()
EXPECTED_FEATURE_COLS = [
    c for c in _all_cols if c not in ("attack_type", "difficulty_level")
]


@app.route("/")
def index():
    """Render the main upload page."""
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """Accept a CSV file upload and return per-row predictions + summary."""

    # --- file presence check (kept from original) -------------------------
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    try:
        # --- read CSV into DataFrame --------------------------------------
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            df = pd.read_csv(stream)
        except Exception as exc:
            return jsonify({
                "status": "error",
                "message": f"Failed to parse CSV file: {exc}",
            }), 400

        # --- validate columns ---------------------------------------------
        missing = [c for c in EXPECTED_FEATURE_COLS if c not in df.columns]
        if missing:
            return jsonify({
                "status": "error",
                "message": "Missing required columns",
                "missing_columns": missing,
            }), 400

        # Keep only the expected feature columns (in the correct order)
        df = df[EXPECTED_FEATURE_COLS]

        # --- transform & predict ------------------------------------------
        X = preprocessor.transform(df)
        preds = model.predict(X)

        # Decode numeric labels back to category names when needed
        if label_encoder is not None:
            preds = label_encoder.inverse_transform(preds)

        preds = [str(p) for p in preds]

        # --- build summary ------------------------------------------------
        total = len(preds)
        counts = {}
        for p in preds:
            counts[p] = counts.get(p, 0) + 1

        summary = {
            category: {
                "count": cnt,
                "percentage": round(cnt / total * 100, 2),
            }
            for category, cnt in sorted(counts.items())
        }

        # --- per-row predictions ------------------------------------------
        predictions = [
            {"row": idx, "predicted_category": cat}
            for idx, cat in enumerate(preds)
        ]

        print(f"[predict] {total} rows processed from '{file.filename}'")

        return jsonify({"summary": summary, "predictions": predictions})

    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Prediction failed: {exc}",
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
