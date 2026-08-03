"""Out-of-core preprocessing for the Network Intrusion Detection System.

This module provides chunk-friendly preprocessing that never requires holding
the full dataset in memory.  It is the OOC counterpart of preprocessing.py:

- Categorical encoding uses hardcoded known value sets (CATEGORY_VALUES)
  instead of fitting a OneHotEncoder on the full file.
- Numeric scaling uses Welford's online algorithm (RunningScaler) to
  accumulate mean/variance across arbitrarily many chunks.
- Attack-type → category mapping is imported from preprocessing.py to
  maintain a single source of truth.
"""

import numpy as np
import pandas as pd

from preprocessing import (
    CATEGORICAL_COLS,
    NON_FEATURE_COLS,
    get_attack_category_map,
)


# ---------------------------------------------------------------------------
# 1. Known fixed category value sets (from NSL-KDD Train+Test)
#    Hardcoded so we never need a full-file scan to learn them.
# ---------------------------------------------------------------------------

CATEGORY_VALUES: dict[str, list[str]] = {
    "protocol_type": [
        "icmp", "tcp", "udp",
    ],
    "service": [
        "IRC", "X11", "Z39_50", "aol", "auth", "bgp", "courier",
        "csnet_ns", "ctf", "daytime", "discard", "domain", "domain_u",
        "echo", "eco_i", "ecr_i", "efs", "exec", "finger", "ftp",
        "ftp_data", "gopher", "harvest", "hostnames", "http", "http_2784",
        "http_443", "http_8001", "imap4", "iso_tsap", "klogin", "kshell",
        "ldap", "link", "login", "mtp", "name", "netbios_dgm",
        "netbios_ns", "netbios_ssn", "netstat", "nnsp", "nntp", "ntp_u",
        "other", "pm_dump", "pop_2", "pop_3", "printer", "private",
        "red_i", "remote_job", "rje", "shell", "smtp", "sql_net", "ssh",
        "sunrpc", "supdup", "systat", "telnet", "tftp_u", "tim_i", "time",
        "urh_i", "urp_i", "uucp", "uucp_path", "vmnet", "whois",
    ],
    "flag": [
        "OTH", "REJ", "RSTO", "RSTOS0", "RSTR",
        "S0", "S1", "S2", "S3", "SF", "SH",
    ],
}

# Pre-compute the full one-hot column list once at import time so every
# call to manual_one_hot_encode produces identically ordered columns.
_OHE_COLUMNS: list[str] = []
for _col, _vals in CATEGORY_VALUES.items():
    _OHE_COLUMNS.extend(f"{_col}_{v}" for v in _vals)
    _OHE_COLUMNS.append(f"{_col}_unknown")


# ---------------------------------------------------------------------------
# 2. Manual one-hot encoding
# ---------------------------------------------------------------------------

def manual_one_hot_encode(chunk: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode protocol_type, service, flag using known value sets.

    Values not present in CATEGORY_VALUES are mapped to an ``<col>_unknown``
    bucket (all-zeros for known categories, 1 for unknown) — the encoder
    never crashes on unseen values.

    Parameters
    ----------
    chunk : pd.DataFrame
        A chunk of raw NSL-KDD data that includes the three categorical
        columns.

    Returns
    -------
    pd.DataFrame
        The chunk with categorical columns replaced by 0/1 indicator
        columns, in a fixed order determined by CATEGORY_VALUES.
    """
    encoded_parts: list[pd.DataFrame] = []

    for col, known_vals in CATEGORY_VALUES.items():
        # Build a zero-filled frame for all indicator columns + unknown
        col_names = [f"{col}_{v}" for v in known_vals] + [f"{col}_unknown"]
        ohe = pd.DataFrame(0, index=chunk.index, columns=col_names)

        for val in known_vals:
            mask = chunk[col] == val
            ohe.loc[mask, f"{col}_{val}"] = 1

        # Anything not matched by any known value is "unknown"
        known_mask = chunk[col].isin(known_vals)
        ohe.loc[~known_mask, f"{col}_unknown"] = 1

        encoded_parts.append(ohe)

    # Drop original categorical columns and concat encoded columns
    result = chunk.drop(columns=list(CATEGORY_VALUES.keys()))
    result = pd.concat([result] + encoded_parts, axis=1)
    return result


# ---------------------------------------------------------------------------
# 3. Welford's online running scaler
# ---------------------------------------------------------------------------

class RunningScaler:
    """Online mean/variance scaler using Welford's algorithm.

    Accumulates running statistics across arbitrarily many chunks so that
    memory usage stays constant regardless of total dataset size.

    Usage
    -----
    >>> scaler = RunningScaler()
    >>> for chunk in pd.read_csv("big.csv", chunksize=10_000):
    ...     scaler.update(chunk[numeric_cols])
    >>> # scaler is now "fitted"
    >>> for chunk in pd.read_csv("big.csv", chunksize=10_000):
    ...     scaled = scaler.transform(chunk[numeric_cols])
    """

    def __init__(self) -> None:
        self.n: int = 0
        self.mean: np.ndarray | None = None
        self.M2: np.ndarray | None = None  # sum of squared diffs from mean
        self.columns: list[str] | None = None

    # ---- fitting ---------------------------------------------------------

    def update(self, chunk: pd.DataFrame) -> None:
        """Incorporate a new chunk of numeric data into the running stats using
        vectorized batch Welford's algorithm for high performance."""
        values = chunk.values.astype(np.float64)
        chunk_n = values.shape[0]
        if chunk_n == 0:
            return

        if self.mean is None:
            # First chunk — initialise accumulators
            self.columns = list(chunk.columns)
            self.mean = np.zeros(values.shape[1], dtype=np.float64)
            self.M2 = np.zeros(values.shape[1], dtype=np.float64)

        chunk_mean = np.mean(values, axis=0)
        chunk_M2 = np.sum((values - chunk_mean) ** 2, axis=0)

        if self.n == 0:
            self.n = chunk_n
            self.mean = chunk_mean
            self.M2 = chunk_M2
        else:
            new_n = self.n + chunk_n
            delta = chunk_mean - self.mean
            self.mean = self.mean + delta * (chunk_n / new_n)
            self.M2 = self.M2 + chunk_M2 + (delta ** 2) * (self.n * chunk_n / new_n)
            self.n = new_n

    @property
    def variance(self) -> np.ndarray:
        """Population variance computed so far."""
        if self.n < 2:
            return np.zeros_like(self.mean)
        return self.M2 / self.n

    @property
    def std(self) -> np.ndarray:
        """Population standard deviation (floored to avoid /0)."""
        return np.sqrt(np.maximum(self.variance, 1e-12))

    # ---- transforming ----------------------------------------------------

    def transform(self, chunk: pd.DataFrame) -> np.ndarray:
        """Standardise a chunk using the accumulated mean and std.

        Parameters
        ----------
        chunk : pd.DataFrame
            Must contain the same columns (in order) that were seen during
            ``update()`` calls.

        Returns
        -------
        np.ndarray
            Z-score scaled values.
        """
        if self.mean is None:
            raise RuntimeError("RunningScaler has not been fitted yet — "
                               "call .update() on at least one chunk first.")
        return (chunk.values.astype(np.float64) - self.mean) / self.std


# ---------------------------------------------------------------------------
# 4. Attack-type → category mapping
# ---------------------------------------------------------------------------
# Imported from preprocessing.py (single source of truth).
# get_attack_category_map is re-exported so train_model_ooc.py can import it
# from this module without changing its existing import line.


# ---------------------------------------------------------------------------
# 5. Chunk preparation (one-hot + scale → numpy arrays)
# ---------------------------------------------------------------------------

# Columns excluded from the feature set
_NON_FEATURE_COLS = set(NON_FEATURE_COLS)

# Categorical columns handled by one-hot encoding
_CATEGORICAL_COLS = set(CATEGORICAL_COLS)


def _numeric_columns(chunk: pd.DataFrame) -> list[str]:
    """Return the list of numeric feature column names in *chunk*."""
    return [
        c for c in chunk.columns
        if c not in _NON_FEATURE_COLS and c not in _CATEGORICAL_COLS
    ]


def prepare_chunk(
    chunk: pd.DataFrame,
    scaler: RunningScaler,
    fitted: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert a raw chunk into (X, y) numpy arrays.

    Parameters
    ----------
    chunk : pd.DataFrame
        Raw NSL-KDD rows (43 columns).
    scaler : RunningScaler
        A RunningScaler instance.  If *fitted* is True, ``.transform()`` is
        called; otherwise only ``.update()`` is called (no X is returned in
        that case — but we still return a dummy so the signature is stable).
    fitted : bool
        When True (default), apply the scaler transform and return usable
        (X, y).  When False, only update scaler stats and return dummy arrays.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (X, y) ready for ``SGDClassifier.partial_fit()``.
    """
    mapping = get_attack_category_map()
    chunk = chunk.copy()

    # Map attack_type → category
    chunk["category"] = chunk["attack_type"].map(mapping)
    unmapped = chunk["category"].isna()
    if unmapped.any():
        bad = chunk.loc[unmapped, "attack_type"].unique().tolist()
        raise ValueError(
            f"Unmapped attack_type value(s): {bad}. "
            "Update get_attack_category_map() to include them."
        )

    y = chunk["category"].values

    # Identify numeric columns *before* one-hot encoding
    num_cols = _numeric_columns(chunk)

    if not fitted:
        # Pass 1: only accumulate scaler statistics
        scaler.update(chunk[num_cols])
        return np.empty(0), y

    # --- fitted path (Pass 2 / evaluation) --------------------------------

    # One-hot encode categoricals
    chunk_encoded = manual_one_hot_encode(chunk)

    # Scale numeric columns
    numeric_scaled = scaler.transform(chunk[num_cols])

    # Grab the one-hot columns (they are appended at the end by
    # manual_one_hot_encode)
    ohe_values = chunk_encoded[_OHE_COLUMNS].values.astype(np.float64)

    # Final feature matrix: [scaled_numeric | one_hot]
    X = np.hstack([numeric_scaled, ohe_values])

    return X, y
