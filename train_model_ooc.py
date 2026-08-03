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

import time
from collections import Counter

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix

from preprocessing_ooc import (
    CATEGORY_VALUES,
    RunningScaler,
    get_attack_category_map,
    prepare_chunk,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRAIN_PATH = "NSL_Dataset/Train.txt"
TEST_PATH = "NSL_Dataset/Test.txt"
CHUNKSIZE = 10_000
N_EPOCHS = 5

# The 5 target classes (alphabetical for deterministic ordering)
ALL_CLASSES = sorted(set(get_attack_category_map().values()))

# Column names (41 features + attack_type + difficulty_level)
COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "attack_type", "difficulty_level",
]


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
    print("=" * 60)
    print("PASS 1 / 2 — Fitting RunningScaler on training data")
    print("=" * 60)

    scaler = RunningScaler()
    class_counts: Counter = Counter()
    rows_pass1 = 0

    for i, chunk in enumerate(_read_chunks(TRAIN_PATH), start=1):
        _, y_chunk = prepare_chunk(chunk, scaler, fitted=False)
        class_counts.update(y_chunk)
        rows_pass1 += len(chunk)
        print(f"  [scaler] chunk {i:>4d}  |  rows so far: {rows_pass1:>9,}")

    print(f"  ✓ Scaler fitted on {rows_pass1:,} rows  "
          f"({scaler.mean.shape[0]} numeric features)")

    # --- Compute balanced class weights from observed distribution --------
    # Formula: weight_c = n_samples / (n_classes * count_c)
    # This is the same formula sklearn uses for class_weight='balanced'.
    n_samples = sum(class_counts.values())
    n_classes = len(ALL_CLASSES)
    CLASS_WEIGHTS = {
        cls: n_samples / (n_classes * class_counts[cls])
        for cls in ALL_CLASSES
    }

    print(f"  Class counts (Train.txt): {dict(class_counts)}")
    print(f"  Balanced class weights:   {CLASS_WEIGHTS}\n")

    # === PASS 2 — Incremental training (multi-epoch) ======================
    print("=" * 60)
    print(f"PASS 2 / 2 — Training SGDClassifier (partial_fit, "
          f"{N_EPOCHS} epochs)")
    print("=" * 60)

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
            print(f"  [train]  epoch {epoch}/{N_EPOCHS}  |  "
                  f"chunk {i:>4d}  |  rows so far: {rows_epoch:>9,}")
        print(f"  ✓ Epoch {epoch}/{N_EPOCHS} complete — "
              f"{rows_epoch:,} rows\n")

    print(f"  ✓ Training complete — {N_EPOCHS} epochs "
          f"× {rows_epoch:,} rows\n")

    # === EVALUATION on test set ===========================================
    print("=" * 60)
    print("Evaluating on test set (chunked)")
    print("=" * 60)

    all_y_true: list[np.ndarray] = []
    all_y_pred: list[np.ndarray] = []
    rows_test = 0

    for i, chunk in enumerate(_read_chunks(TEST_PATH), start=1):
        X, y = prepare_chunk(chunk, scaler, fitted=True)
        preds = model.predict(X)
        all_y_true.append(y)
        all_y_pred.append(preds)
        rows_test += len(chunk)
        print(f"  [eval]   chunk {i:>4d}  |  rows so far: {rows_test:>9,}")

    y_true = np.concatenate(all_y_true)
    y_pred = np.concatenate(all_y_pred)

    print(f"\n  ✓ Evaluated on {rows_test:,} test rows\n")

    # --- Classification report ---
    report = classification_report(y_true, y_pred, target_names=ALL_CLASSES)
    print("=" * 60)
    print("Classification Report")
    print("=" * 60)
    print(report)

    # --- Call out minority-class recall ---
    per_class = classification_report(
        y_true, y_pred, target_names=ALL_CLASSES, output_dict=True,
    )
    for cls in ("U2R", "R2L"):
        if cls in per_class:
            recall = per_class[cls]["recall"]
            print(f"  ⚠  {cls} recall: {recall:.4f}")

    # --- Confusion matrix ---
    cm = confusion_matrix(y_true, y_pred, labels=ALL_CLASSES)
    print(f"\nConfusion Matrix (rows=true, cols=pred)  labels={ALL_CLASSES}")
    print(cm)

    # === SAVE ARTEFACTS ===================================================
    print("\n" + "=" * 60)
    print("Saving artefacts")
    print("=" * 60)

    joblib.dump(model, "model_ooc.pkl")
    print("  → model_ooc.pkl")

    preprocessor_state = {
        "scaler": scaler,
        "category_values": CATEGORY_VALUES,
    }
    joblib.dump(preprocessor_state, "preprocessor_ooc.pkl")
    print("  → preprocessor_ooc.pkl")

    elapsed = time.perf_counter() - t_start
    print(f"\n  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
