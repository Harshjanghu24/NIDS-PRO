"""Shared preprocessing pipeline for the Network Intrusion Detection System.

This module is imported by both train_model.py (offline training) and app.py
(live serving).  Keeping all column definitions, category mappings, and
transformer construction in one place prevents train/serve skew.

⚠  If you update the column list or attack-type mapping in eda.py, mirror
   the changes here so that training and prediction stay in sync.
"""

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------------------------
# 1. Column names (mirrors eda.py Cell 2)
# ---------------------------------------------------------------------------

def load_column_names() -> list[str]:
    """Return the 41 NSL-KDD feature names + attack_type + difficulty_level."""
    return [
        "duration",
        "protocol_type",
        "service",
        "flag",
        "src_bytes",
        "dst_bytes",
        "land",
        "wrong_fragment",
        "urgent",
        "hot",
        "num_failed_logins",
        "logged_in",
        "num_compromised",
        "root_shell",
        "su_attempted",
        "num_root",
        "num_file_creations",
        "num_shells",
        "num_access_files",
        "num_outbound_cmds",
        "is_host_login",
        "is_guest_login",
        "count",
        "srv_count",
        "serror_rate",
        "srv_serror_rate",
        "rerror_rate",
        "srv_rerror_rate",
        "same_srv_rate",
        "diff_srv_rate",
        "srv_diff_host_rate",
        "dst_host_count",
        "dst_host_srv_count",
        "dst_host_same_srv_rate",
        "dst_host_diff_srv_rate",
        "dst_host_same_src_port_rate",
        "dst_host_srv_diff_host_rate",
        "dst_host_serror_rate",
        "dst_host_srv_serror_rate",
        "dst_host_rerror_rate",
        "dst_host_srv_rerror_rate",
        "attack_type",
        "difficulty_level",
    ]


# ---------------------------------------------------------------------------
# 2. Attack-type → category mapping (mirrors eda.py Cell 3)
# ---------------------------------------------------------------------------

def get_attack_category_map() -> dict[str, str]:
    """Return the attack_type → category mapping (5 classes).

    Classes: Normal, DOS, PROBE, R2L, U2R.
    """
    return {
        # Normal
        "normal": "Normal",
        # DOS attacks
        "back": "DOS",
        "land": "DOS",
        "neptune": "DOS",
        "pod": "DOS",
        "smurf": "DOS",
        "teardrop": "DOS",
        "mailbomb": "DOS",
        "apache2": "DOS",
        "processtable": "DOS",
        "udpstorm": "DOS",
        # PROBE attacks
        "ipsweep": "PROBE",
        "nmap": "PROBE",
        "portsweep": "PROBE",
        "satan": "PROBE",
        "mscan": "PROBE",
        "saint": "PROBE",
        # R2L attacks
        "ftp_write": "R2L",
        "guess_passwd": "R2L",
        "imap": "R2L",
        "multihop": "R2L",
        "phf": "R2L",
        "spy": "R2L",
        "warezclient": "R2L",
        "warezmaster": "R2L",
        "sendmail": "R2L",
        "named": "R2L",
        "snmpgetattack": "R2L",
        "snmpguess": "R2L",
        "xlock": "R2L",
        "xsnoop": "R2L",
        "worm": "R2L",
        "httptunnel": "R2L",
        # U2R attacks
        "buffer_overflow": "U2R",
        "loadmodule": "U2R",
        "perl": "U2R",
        "rootkit": "U2R",
        "xterm": "U2R",
        "ps": "U2R",
        "sqlattack": "U2R",
    }


# ---------------------------------------------------------------------------
# 3. Sklearn ColumnTransformer (unfitted)
# ---------------------------------------------------------------------------

# Columns that receive categorical encoding
CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

# Columns excluded from the feature set (target + metadata)
NON_FEATURE_COLS = ["attack_type", "category", "difficulty_level"]


def build_preprocessor() -> ColumnTransformer:
    """Build an *unfitted* ColumnTransformer for NSL-KDD features.

    - OneHotEncoder (handle_unknown='ignore') for the 3 categorical columns.
    - StandardScaler for all remaining numeric feature columns.

    Returns
    -------
    sklearn.compose.ColumnTransformer
        Ready to be fitted on training data.
    """
    # Derive numeric columns from the full column list, excluding categoricals
    # and non-feature columns.
    all_columns = load_column_names()
    numeric_cols = [
        c for c in all_columns
        if c not in CATEGORICAL_COLS and c not in NON_FEATURE_COLS
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_COLS,
            ),
            (
                "num",
                StandardScaler(),
                numeric_cols,
            ),
        ],
        remainder="drop",
    )
    return preprocessor


# ---------------------------------------------------------------------------
# 4. DataFrame preparation (raw → X, y)
# ---------------------------------------------------------------------------

def prepare_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Convert a raw NSL-KDD dataframe into (X, y).

    Steps
    -----
    1. Map ``attack_type`` → ``category`` using the canonical mapping.
    2. Raise ``ValueError`` if any attack_type is unmapped (never silently
       drop rows).
    3. Drop ``attack_type`` and ``difficulty_level``.
    4. Return ``(X, y)`` where *X* contains all feature columns and *y* is
       the ``category`` series.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe with the standard 43-column NSL-KDD schema.

    Returns
    -------
    tuple[pd.DataFrame, pd.Series]
        (X, y) ready for fitting / transforming with ``build_preprocessor()``.
    """
    mapping = get_attack_category_map()
    df = df.copy()  # avoid mutating caller's data

    df["category"] = df["attack_type"].map(mapping)

    # Fail loudly on unmapped attack types
    unmapped_mask = df["category"].isna()
    if unmapped_mask.any():
        bad_types = df.loc[unmapped_mask, "attack_type"].unique().tolist()
        raise ValueError(
            f"Unmapped attack_type value(s) found: {bad_types}. "
            "Update get_attack_category_map() to include them."
        )

    df = df.drop(columns=["attack_type", "difficulty_level"])

    y = df["category"]
    X = df.drop(columns=["category"])

    return X, y


# ---------------------------------------------------------------------------
# 5. Persistence helpers (joblib)
# ---------------------------------------------------------------------------

def save_preprocessor(preprocessor: ColumnTransformer, path: str = "preprocessor.pkl") -> None:
    """Serialize a fitted ColumnTransformer to disk."""
    joblib.dump(preprocessor, path)


def load_preprocessor(path: str = "preprocessor.pkl") -> ColumnTransformer:
    """Load a previously saved ColumnTransformer from disk."""
    return joblib.load(path)
