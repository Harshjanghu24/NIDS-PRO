# Troubleshooting & FAQ Guide

This document addresses common issues, error messages, and troubleshooting steps when developing, deploying, or testing the Network Intrusion Detection System.

---

## 1. Common Error Messages & Solutions

### A. `HTTP 400 Bad Request — Missing required columns`
- **Symptom**: The `/predict` API returns JSON stating missing columns e.g. `["protocol_type", "src_bytes"]`.
- **Cause**: Uploaded CSV lacks standard 41 NSL-KDD column names, or columns are named differently (case-sensitive).
- **Solution**: Ensure your CSV file includes the exact header row present in `sample_upload.csv`.

### B. `HTTP 413 Payload Too Large — File too large. Maximum upload size is 5 MB.`
- **Symptom**: File uploads larger than 5 MB are rejected automatically by Flask.
- **Cause**: Werkzeug `MAX_CONTENT_LENGTH` enforcement in `app.py`.
- **Solution**: Split large log files into smaller chunks or use the out-of-core streaming script `train_model_ooc.py` for direct file processing.

### C. `InconsistentVersionWarning: Trying to unpickle estimator OneHotEncoder from version 1.8.0 when using version 1.9.0`
- **Symptom**: Python warning emitted during joblib model loading.
- **Cause**: Models were saved using scikit-learn 1.8.x and loaded in scikit-learn 1.9.x.
- **Solution**: This is a harmless warning; predictions remain valid. To eliminate it, run `python train_model.py` to re-save model artifacts with your current environment's scikit-learn version.

### D. `UnicodeEncodeError: 'charmap' codec can't encode character...`
- **Symptom**: Terminal error on Windows when running Python scripts.
- **Cause**: Windows command prompt defaults to `cp1252` encoding which cannot render UTF-8 checkmarks or unicode arrows.
- **Solution**: Set the environment variable `PYTHONIOENCODING=utf-8` before running scripts, or run inside PowerShell.

---

## 2. Ports & Network Conflicts

### Issue: Port 5000 Already in Use
- **Windows**:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process
  ```
- **Linux / macOS**:
  ```bash
  fuser -k 5000/tcp
  ```

---

## 3. Dataset Path Validation

Verify that raw datasets are properly located before training:
- `NSL_Dataset/Train.txt` (Required for `train_model.py` and `train_model_ooc.py`)
- `NSL_Dataset/Test.txt` (Required for evaluation)

If missing, verify directory structure:
```bash
python -c "import os; print('Train exists:', os.path.exists('NSL_Dataset/Train.txt'))"
```
