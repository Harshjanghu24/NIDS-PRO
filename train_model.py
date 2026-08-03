"""In-memory training pipeline for the Network Intrusion Detection System.

Trains two candidate models (RandomForest, XGBoost) on the NSL-KDD dataset,
evaluates both with emphasis on the heavily imbalanced U2R and R2L classes,
and persists the better model (by macro F1) along with the fitted
preprocessor.
"""

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
    build_preprocessor,
    load_column_names,
    prepare_dataframe,
    save_preprocessor,
)

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

    print(f"\n{'=' * 60}")
    print(f"  {name} -- Classification Report")
    print("=" * 60)
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
            print(f"\n  >> {cls} recall: {recall:.4f}")

    return report_dict


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.perf_counter()

    # === 1. Load data =====================================================
    print("=" * 60)
    print("Step 1 -- Loading datasets")
    print("=" * 60)

    col_names = load_column_names()
    df_train = pd.read_csv(TRAIN_PATH, names=col_names, header=None)
    df_test = pd.read_csv(TEST_PATH, names=col_names, header=None)
    print(f"  Train rows: {len(df_train):,}")
    print(f"  Test  rows: {len(df_test):,}")

    # === 2. Prepare features and labels ===================================
    print(f"\n{'=' * 60}")
    print("Step 2 -- Preparing dataframes (attack_type -> category)")
    print("=" * 60)

    X_train, y_train = prepare_dataframe(df_train)
    X_test, y_test = prepare_dataframe(df_test)
    print(f"  X_train shape: {X_train.shape}")
    print(f"  X_test  shape: {X_test.shape}")
    print(f"  Train label distribution:\n{y_train.value_counts().to_string()}")

    # === 3. Build & fit preprocessor ======================================
    print(f"\n{'=' * 60}")
    print("Step 3 -- Building and fitting preprocessor")
    print("=" * 60)

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    print(f"  Transformed X_train shape: {X_train_t.shape}")
    print(f"  Transformed X_test  shape: {X_test_t.shape}")

    # === 4. Train candidate models ========================================

    # --- 4a. RandomForestClassifier ---------------------------------------
    print(f"\n{'=' * 60}")
    print("Step 4a -- Training RandomForestClassifier "
          "(n_estimators=200, class_weight='balanced')")
    print("=" * 60)

    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
    )
    rf.fit(X_train_t, y_train)
    print("  [OK] RandomForest training complete")

    # --- 4b. XGBClassifier ------------------------------------------------
    print(f"\n{'=' * 60}")
    print("Step 4b -- Training XGBClassifier (with balanced sample_weight)")
    print("=" * 60)

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
    print("  [OK] XGBoost training complete")

    # === 5. Evaluate both models ==========================================
    print(f"\n{'=' * 60}")
    print("Step 5 -- Evaluating models on test set")
    print("=" * 60)

    rf_report = _evaluate("RandomForest", rf, X_test_t, y_test)
    xgb_report = _evaluate("XGBoost", xgb, X_test_t, y_test, label_encoder=le)

    # === 6. Pick the better model & save ==================================
    print(f"\n{'=' * 60}")
    print("Step 6 -- Selecting best model and saving artefacts")
    print("=" * 60)

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
    print(f"  -> model.pkl  (saved {best_name})")

    joblib.dump(best_label_encoder, "label_encoder.pkl")
    print(f"  -> label_encoder.pkl  ({'active' if best_label_encoder else 'None'})")

    save_preprocessor(preprocessor, "preprocessor.pkl")
    print("  -> preprocessor.pkl")

    # === 7. Final summary =================================================
    u2r_recall = best_report.get("U2R", {}).get("recall", float("nan"))
    r2l_recall = best_report.get("R2L", {}).get("recall", float("nan"))

    elapsed = time.perf_counter() - t_start

    print(f"\n{'=' * 60}")
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"  Chosen model : {best_name}")
    print(f"  Macro F1     : {best_f1:.4f}")
    print(f"  U2R recall   : {u2r_recall:.4f}")
    print(f"  R2L recall   : {r2l_recall:.4f}")
    print(f"  Elapsed time : {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
