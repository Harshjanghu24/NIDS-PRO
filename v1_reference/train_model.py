"""In-memory training pipeline for the Network Intrusion Detection System.

Trains two candidate models (RandomForest, XGBoost) on the NSL-KDD dataset,
evaluates both with emphasis on the heavily imbalanced U2R and R2L classes,
and persists the better model (by macro F1) along with the fitted
preprocessor.
"""

import json
import logging
import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from preprocessing import (
    CATEGORICAL_COLS,
    NON_FEATURE_COLS,
    build_preprocessor,
    load_column_names,
    prepare_dataframe,
    save_preprocessor,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TRAIN_PATH = "NSL_Dataset/Train.txt"
TEST_PATH = "NSL_Dataset/Test.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _evaluate(name: str, model, X_test, y_test, label_encoder=None) -> dict:
    """Print classification report, confusion matrix, and return the
    per-class report dict for further comparison.

    If *label_encoder* is given, predictions are decoded back to string
    labels (needed for XGBoost which requires numeric targets).
    """
    y_pred = model.predict(X_test)
    if label_encoder is not None:
        y_pred = label_encoder.inverse_transform(y_pred)

    logger.info("=" * 60)
    logger.info("  %s -- Classification Report", name)
    logger.info("=" * 60)
    report_dict = classification_report(
        y_test, y_pred, output_dict=True, zero_division=0,
    )
    print(classification_report(y_test, y_pred, zero_division=0))

    # Confusion matrix
    labels = sorted(y_test.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print(f"Confusion Matrix (rows=true, cols=pred)  labels={labels}")
    print(cm)

    # Minority-class recall callout
    for cls in ("U2R", "R2L"):
        if cls in report_dict:
            recall = report_dict[cls]["recall"]
            logger.info("  >> %s recall: %.4f", cls, recall)

    return report_dict


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.perf_counter()

    # === 1. Load data =====================================================
    logger.info("=" * 60)
    logger.info("Step 1 -- Loading datasets")
    logger.info("=" * 60)

    col_names = load_column_names()
    df_train = pd.read_csv(TRAIN_PATH, names=col_names, header=None)
    df_test = pd.read_csv(TEST_PATH, names=col_names, header=None)
    logger.info("  Train rows: %s", f"{len(df_train):,}")
    logger.info("  Test  rows: %s", f"{len(df_test):,}")

    # === 2. Prepare features and labels ===================================
    logger.info("=" * 60)
    logger.info("Step 2 -- Preparing dataframes (attack_type -> category)")
    logger.info("=" * 60)

    X_train, y_train = prepare_dataframe(df_train)
    X_test, y_test = prepare_dataframe(df_test)
    logger.info("  X_train shape: %s", X_train.shape)
    logger.info("  X_test  shape: %s", X_test.shape)
    logger.info("  Train label distribution:\n%s", y_train.value_counts().to_string())

    # === 3. Build & fit preprocessor ======================================
    logger.info("=" * 60)
    logger.info("Step 3 -- Building and fitting preprocessor")
    logger.info("=" * 60)

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    logger.info("  Transformed X_train shape: %s", X_train_t.shape)
    logger.info("  Transformed X_test  shape: %s", X_test_t.shape)

    # === 4. Train candidate models ========================================

    # --- 4a. RandomForestClassifier ---------------------------------------
    logger.info("=" * 60)
    logger.info("Step 4a -- Training RandomForestClassifier "
                "(n_estimators=200, class_weight='balanced')")
    logger.info("=" * 60)

    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
    )
    rf.fit(X_train_t, y_train)
    logger.info("  [OK] RandomForest training complete")

    # --- 4b. XGBClassifier ------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 4b -- Training XGBClassifier (with balanced sample_weight)")
    logger.info("=" * 60)

    sample_weights = compute_sample_weight("balanced", y_train)

    # XGBoost requires numeric labels
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)

    xgb = XGBClassifier(
        n_estimators=200,
        eval_metric="mlogloss",
        random_state=42,
    )
    xgb.fit(X_train_t, y_train_enc, sample_weight=sample_weights)
    logger.info("  [OK] XGBoost training complete")

    # === 5. Evaluate both models ==========================================
    logger.info("=" * 60)
    logger.info("Step 5 -- Evaluating models on test set")
    logger.info("=" * 60)

    rf_report = _evaluate("RandomForest", rf, X_test_t, y_test)
    xgb_report = _evaluate("XGBoost", xgb, X_test_t, y_test, label_encoder=le)

    # === 6. Pick the better model & save ==================================
    logger.info("=" * 60)
    logger.info("Step 6 -- Selecting best model and saving artefacts")
    logger.info("=" * 60)

    rf_macro_f1 = rf_report["macro avg"]["f1-score"]
    xgb_macro_f1 = xgb_report["macro avg"]["f1-score"]

    if rf_macro_f1 >= xgb_macro_f1:
        best_name, best_model, best_f1 = "RandomForest", rf, rf_macro_f1
        best_report = rf_report
        best_label_encoder = None        # RF predicts string labels directly
    else:
        best_name, best_model, best_f1 = "XGBoost", xgb, xgb_macro_f1
        best_report = xgb_report
        best_label_encoder = le           # XGB needs numeric -> string decoding

    joblib.dump(best_model, "model.pkl")
    logger.info("  -> model.pkl  (saved %s)", best_name)

    joblib.dump(best_label_encoder, "label_encoder.pkl")
    logger.info("  -> label_encoder.pkl  (%s)",
                "active" if best_label_encoder else "None")

    save_preprocessor(preprocessor, "preprocessor.pkl")
    logger.info("  -> preprocessor.pkl")

    # === 7. Final summary & artifact exports =================================
    u2r_recall = best_report.get("U2R", {}).get("recall", float("nan"))
    r2l_recall = best_report.get("R2L", {}).get("recall", float("nan"))

    elapsed = time.perf_counter() - t_start

    os.makedirs("results", exist_ok=True)
    report_payload = {
        "best_model": best_name,
        "macro_f1": round(best_f1, 4),
        "u2r_recall": round(u2r_recall, 4),
        "r2l_recall": round(r2l_recall, 4),
        "elapsed_seconds": round(elapsed, 2),
        "classification_report": best_report,
    }
    with open("results/evaluation_report.json", "w") as f:
        json.dump(report_payload, f, indent=2)
    logger.info("  -> results/evaluation_report.json")

    if hasattr(best_model, "feature_importances_"):
        cat_cols = list(preprocessor.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_COLS))
        all_cols = load_column_names()
        num_cols = [c for c in all_cols if c not in CATEGORICAL_COLS and c not in NON_FEATURE_COLS]
        feature_names = cat_cols + num_cols

        importances = best_model.feature_importances_
        fi_sorted = [
            {"feature": feat, "importance": round(float(imp), 6)}
            for feat, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        ]
        with open("results/feature_importance.json", "w") as f:
            json.dump(fi_sorted, f, indent=2)
        logger.info("  -> results/feature_importance.json (top feature: %s)", fi_sorted[0]["feature"])

    logger.info("=" * 60)
    logger.info("  FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info("  Chosen model : %s", best_name)
    logger.info("  Macro F1     : %.4f", best_f1)
    logger.info("  U2R recall   : %.4f", u2r_recall)
    logger.info("  R2L recall   : %.4f", r2l_recall)
    logger.info("  Elapsed time : %.1fs", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
