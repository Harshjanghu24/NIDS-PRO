"""Out-of-core training pipeline for the Network Intrusion Detection System.

==========================================================================
WHY THIS EXISTS
==========================================================================
train_model.py loads the entire dataset into memory at once, which is fine
for the ~125 K-row NSL-KDD files but will fail on multi-GB real-world
packet captures.

This pipeline processes data in **fixed-size chunks** (default 10 000 rows)
so peak memory stays roughly constant regardless of file size.  The trade-
off is that we must use a linear model (SGDClassifier with log_loss ≈
logistic regression) instead of tree-based models, because decision trees
/ random forests / gradient-boosted trees require the full dataset in
memory to build their splits.

Two-pass design
---------------
Pass 1 — **Scaler fitting**: stream through the training file once to
         accumulate running mean / variance via Welford's algorithm.
Pass 2 — **Model training**: stream through the training file a second
         time, applying the now-fitted scaler + one-hot encoding to each
         chunk, then calling ``SGDClassifier.partial_fit()`` incrementally.

Evaluation is also done in chunks: we accumulate lightweight predictions
and true labels (strings, not feature arrays) so memory remains low.
==========================================================================
"""

from collections import Counter
import json
import logging
import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix

from preprocessing import load_column_names
from preprocessing_ooc import (
    CATEGORY_VALUES,
    RunningScaler,
    get_attack_category_map,
    prepare_chunk,
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
# Configuration
# ---------------------------------------------------------------------------

TRAIN_PATH = "NSL_Dataset/Train.txt"
TEST_PATH = "NSL_Dataset/Test.txt"
CHUNKSIZE = 10_000
N_EPOCHS = 5

# The 5 target classes (alphabetical for deterministic ordering)
ALL_CLASSES = sorted(set(get_attack_category_map().values()))

# Column names imported from the shared preprocessing module
COLUMN_NAMES = load_column_names()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_chunks(path: str):
    """Yield chunks from *path* as DataFrames."""
    return pd.read_csv(
        path,
        names=COLUMN_NAMES,
        header=None,
        chunksize=CHUNKSIZE,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.perf_counter()

    # === PASS 1 — Fit the running scaler =================================
    logger.info("=" * 60)
    logger.info("PASS 1 / 2 — Fitting RunningScaler on training data")
    logger.info("=" * 60)

    scaler = RunningScaler()
    class_counts: Counter = Counter()
    rows_pass1 = 0

    for i, chunk in enumerate(_read_chunks(TRAIN_PATH), start=1):
        _, y_chunk = prepare_chunk(chunk, scaler, fitted=False)
        class_counts.update(y_chunk)
        rows_pass1 += len(chunk)
        logger.info("  [scaler] chunk %4d  |  rows so far: %9s", i, f"{rows_pass1:,}")

    logger.info("  [OK] Scaler fitted on %s rows (%d numeric features)",
                f"{rows_pass1:,}", scaler.mean.shape[0])

    # --- Compute balanced class weights from observed distribution --------
    # Formula: weight_c = n_samples / (n_classes * count_c)
    # This is the same formula sklearn uses for class_weight='balanced'.
    n_samples = sum(class_counts.values())
    n_classes = len(ALL_CLASSES)
    CLASS_WEIGHTS = {
        cls: n_samples / (n_classes * class_counts[cls])
        for cls in ALL_CLASSES
    }

    logger.info("  Class counts (Train.txt): %s", dict(class_counts))
    logger.info("  Balanced class weights:   %s", CLASS_WEIGHTS)

    # === PASS 2 — Incremental training (multi-epoch) ======================
    logger.info("=" * 60)
    logger.info("PASS 2 / 2 — Training SGDClassifier (partial_fit, %d epochs)", N_EPOCHS)
    logger.info("=" * 60)

    model = SGDClassifier(
        loss="log_loss",
        random_state=42,
        max_iter=1,           # partial_fit ignores this, but keeps lint happy
    )

    for epoch in range(1, N_EPOCHS + 1):
        rows_epoch = 0
        for i, chunk in enumerate(_read_chunks(TRAIN_PATH), start=1):
            X, y = prepare_chunk(chunk, scaler, fitted=True)
            sample_weight = np.array([CLASS_WEIGHTS[label] for label in y])
            model.partial_fit(X, y, classes=ALL_CLASSES,
                              sample_weight=sample_weight)
            rows_epoch += len(chunk)
            logger.info("  [train]  epoch %d/%d  |  chunk %4d  |  rows so far: %9s",
                        epoch, N_EPOCHS, i, f"{rows_epoch:,}")
        logger.info("  [OK] Epoch %d/%d complete — %s rows",
                    epoch, N_EPOCHS, f"{rows_epoch:,}")

    logger.info("  [OK] Training complete — %d epochs x %s rows",
                N_EPOCHS, f"{rows_epoch:,}")

    # === EVALUATION on test set ===========================================
    logger.info("=" * 60)
    logger.info("Evaluating on test set (chunked)")
    logger.info("=" * 60)

    all_y_true: list[np.ndarray] = []
    all_y_pred: list[np.ndarray] = []
    rows_test = 0

    for i, chunk in enumerate(_read_chunks(TEST_PATH), start=1):
        X, y = prepare_chunk(chunk, scaler, fitted=True)
        preds = model.predict(X)
        all_y_true.append(y)
        all_y_pred.append(preds)
        rows_test += len(chunk)
        logger.info("  [eval]   chunk %4d  |  rows so far: %9s", i, f"{rows_test:,}")

    y_true = np.concatenate(all_y_true)
    y_pred = np.concatenate(all_y_pred)

    logger.info("  [OK] Evaluated on %s test rows", f"{rows_test:,}")

    # --- Classification report ---
    report_dict = classification_report(
        y_true, y_pred, target_names=ALL_CLASSES, output_dict=True, zero_division=0,
    )
    print("=" * 60)
    print("Classification Report")
    print("=" * 60)
    print(classification_report(y_true, y_pred, target_names=ALL_CLASSES, zero_division=0))

    # --- Call out minority-class recall ---
    for cls in ("U2R", "R2L"):
        if cls in report_dict:
            recall = report_dict[cls]["recall"]
            logger.info("  >> %s recall: %.4f", cls, recall)

    # --- Confusion matrix ---
    cm = confusion_matrix(y_true, y_pred, labels=ALL_CLASSES)
    print(f"\nConfusion Matrix (rows=true, cols=pred)  labels={ALL_CLASSES}")
    print(cm)

    # === SAVE ARTEFACTS ===================================================
    logger.info("=" * 60)
    logger.info("Saving artefacts")
    logger.info("=" * 60)

    joblib.dump(model, "model_ooc.pkl")
    logger.info("  -> model_ooc.pkl")

    preprocessor_state = {
        "scaler": scaler,
        "category_values": CATEGORY_VALUES,
    }
    joblib.dump(preprocessor_state, "preprocessor_ooc.pkl")
    logger.info("  -> preprocessor_ooc.pkl")

    elapsed = time.perf_counter() - t_start

    os.makedirs("results", exist_ok=True)
    ooc_report_payload = {
        "model": "SGDClassifier",
        "epochs": N_EPOCHS,
        "chunksize": CHUNKSIZE,
        "macro_f1": round(report_dict.get("macro avg", {}).get("f1-score", 0.0), 4),
        "u2r_recall": round(report_dict.get("U2R", {}).get("recall", 0.0), 4),
        "r2l_recall": round(report_dict.get("R2L", {}).get("recall", 0.0), 4),
        "elapsed_seconds": round(elapsed, 2),
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
    }
    with open("results/ooc_evaluation_report.json", "w") as f:
        json.dump(ooc_report_payload, f, indent=2)
    logger.info("  -> results/ooc_evaluation_report.json")

    logger.info("  Done in %.1fs", elapsed)


if __name__ == "__main__":
    main()
