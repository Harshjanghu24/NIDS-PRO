# %% Cell 1 — Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from preprocessing import load_column_names, get_attack_category_map

# %% Cell 2 — Load NSL-KDD Dataset
# Standard 41 feature names for the NSL-KDD dataset
column_names = load_column_names()

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
attack_category_map = get_attack_category_map()

df["category"] = df["attack_type"].map(attack_category_map)

# Check for any unmapped attack types
unmapped = df[df["category"].isna()]["attack_type"].unique()
if len(unmapped) > 0:
    print(f"[!] Unmapped attack types: {unmapped}")
else:
    print("[OK] All attack types mapped successfully.")

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
