"""Tests for Out-of-Core online feature scaling and OOC preprocessor."""

import numpy as np
import pandas as pd
from preprocessing_ooc import RunningScaler, manual_one_hot_encode

def test_running_scaler_vectorized_update():
    """Test RunningScaler mean and variance computation across chunks."""
    scaler = RunningScaler()
    chunk1 = pd.DataFrame([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]])
    chunk2 = pd.DataFrame([[5.0, 6.0, 7.0], [7.0, 8.0, 9.0]])

    scaler.update(chunk1)
    scaler.update(chunk2)

    assert scaler.n == 4
    np.testing.assert_allclose(scaler.mean, [4.0, 5.0, 6.0])

def test_running_scaler_transform():
    """Test RunningScaler transform standardization (zero mean, unit variance)."""
    scaler = RunningScaler()
    df = pd.DataFrame([[10.0, 20.0], [20.0, 40.0]])
    scaler.update(df)
    transformed = scaler.transform(df)

    assert transformed.shape == (2, 2)
    np.testing.assert_allclose(transformed.mean(axis=0), [0.0, 0.0], atol=1e-5)

def test_manual_one_hot_encode():
    """Test manual_one_hot_encode for fixed category value sets."""
    cols = ["duration", "protocol_type", "service", "flag", "src_bytes"]
    df = pd.DataFrame([
        [0, "tcp", "http", "SF", 100],
        [0, "udp", "private", "SF", 200]
    ], columns=cols)

    encoded = manual_one_hot_encode(df)
    assert "protocol_type_tcp" in encoded.columns
    assert "service_http" in encoded.columns
    assert "flag_SF" in encoded.columns
    assert encoded.loc[0, "protocol_type_tcp"] == 1
    assert encoded.loc[1, "protocol_type_tcp"] == 0
