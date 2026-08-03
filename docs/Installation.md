# Installation & Environment Setup Guide

This guide provides comprehensive instructions for installing and running the Network Intrusion Detection System across various operating systems.

---

## System Requirements

- **Operating System**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: Version 3.12 (recommended) or 3.10+
- **RAM**: Minimum 4 GB (8 GB recommended for training)
- **Disk Space**: 500 MB for repository & dependencies; 50 MB for datasets

---

## 1. Repository Setup

Clone the repository to your local machine:
```bash
git clone https://github.com/Harshjanghu24/Network-Intrusion-Detection-System.git
cd Network-Intrusion-Detection-System
```

---

## 2. Virtual Environment Configuration

Setting up a virtual environment isolates project dependencies from system-wide Python packages.

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

### Linux / macOS (Bash/Zsh)
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Dependency Installation

### Production Web Dependencies
Install packages needed to run the Flask application and trained models:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Installed core dependencies:
- `Flask==3.1.0`
- `scikit-learn==1.9.0`
- `xgboost==3.3.0`
- `pandas>=2.2.0`
- `numpy>=2.0.0`
- `joblib>=1.4.0`
- `gunicorn>=23.0.0`

### Development & Visual Plotting Dependencies (Optional)
If you intend to run `eda.py` or re-generate exploratory analysis plots:
```bash
pip install -r requirements-dev.txt
```

---

## 4. Verification

Verify that the installation was successful by running the Python test command:
```bash
python -c "import flask, sklearn, xgboost, pandas; print('All core libraries imported successfully!')"
```
