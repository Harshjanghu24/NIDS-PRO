# %% Cell 1 — Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# %% Cell 2 — Load NSL-KDD Dataset
# Standard 41 feature names for the NSL-KDD dataset
column_names = [
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

# Load training and test sets (no header row in source files)
df_train = pd.read_csv("NSL_Dataset/Train.txt", names=column_names, header=None)
df_test = pd.read_csv("NSL_Dataset/Test.txt", names=column_names, header=None)

print(f"Training set shape: {df_train.shape}")
print(f"Test set shape:     {df_test.shape}")

# Combine for full EDA view
df = pd.concat([df_train, df_test], ignore_index=True)
print(f"Combined shape:     {df.shape}")
df.head()

# %% Cell 3 — Attack-Type to Category Mapping
attack_category_map = {
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

df["category"] = df["attack_type"].map(attack_category_map)

# Check for any unmapped attack types
unmapped = df[df["category"].isna()]["attack_type"].unique()
if len(unmapped) > 0:
    print(f"⚠ Unmapped attack types: {unmapped}")
else:
    print("✓ All attack types mapped successfully.")

df[["attack_type", "category"]].drop_duplicates().sort_values("category")

# %% Cell 4 — Class Distribution (Imbalance Check)
category_counts = df["category"].value_counts()
print(category_counts)

plt.figure(figsize=(8, 5))
sns.barplot(x=category_counts.index, y=category_counts.values, palette="viridis")
plt.title("Class Distribution (Attack Categories)")
plt.xlabel("Category")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig("results/class_distribution.png", dpi=150)
plt.show()
print("Saved → results/class_distribution.png")

# %% Cell 5 — Data Info & Categorical Column Inspection
df.info()

print("\n--- Categorical Columns ---")
categorical_cols = ["protocol_type", "service", "flag"]
for col in categorical_cols:
    print(f"\n{col} — {df[col].nunique()} unique values:")
    print(df[col].value_counts())

# %% Cell 6 — Correlation Matrix of Numeric Features
numeric_df = df.select_dtypes(include=[np.number])
corr_matrix = numeric_df.corr()

corr_matrix.to_csv("results/corrm.csv")
print(f"Correlation matrix shape: {corr_matrix.shape}")
print("Saved → results/corrm.csv")

corr_matrix.head()

# %%
