"""Tests for data preprocessing functions and schema mappings."""

import pandas as pd

from preprocessing import (
    build_preprocessor,
    get_attack_category_map,
    load_column_names,
    prepare_dataframe,
)


def test_load_column_names():
    """Verify load_column_names returns 43 columns."""
    cols = load_column_names()
    assert len(cols) == 43
    assert "duration" in cols
    assert "attack_type" in cols
    assert "difficulty_level" in cols

def test_get_attack_category_map():
    """Verify attack category mapping dictionary covers major attack classes."""
    mapping = get_attack_category_map()
    assert isinstance(mapping, dict)
    assert mapping["normal"] == "Normal"
    assert mapping["neptune"] == "DOS"
    assert mapping["satan"] == "PROBE"
    assert mapping["guess_passwd"] == "R2L"
    assert mapping["buffer_overflow"] == "U2R"

def test_prepare_dataframe():
    """Verify prepare_dataframe splits raw dataframe into feature matrix X and target y."""
    cols = load_column_names()
    # Create 1 sample raw row
    sample_data = [[0] * 41 + ["neptune", 21]]
    df_raw = pd.DataFrame(sample_data, columns=cols)

    X, y = prepare_dataframe(df_raw)
    assert X.shape == (1, 41)
    assert "attack_type" not in X.columns
    assert "difficulty_level" not in X.columns
    assert y.iloc[0] == "DOS"

def test_build_preprocessor():
    """Verify ColumnTransformer build structure."""
    preprocessor = build_preprocessor()
    transformers = [name for name, _, _ in preprocessor.transformers]
    assert "num" in transformers
    assert "cat" in transformers
