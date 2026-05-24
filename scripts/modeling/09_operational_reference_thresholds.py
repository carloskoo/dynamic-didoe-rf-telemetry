import pandas as pd
import numpy as np
import os

# ============================================================
# 09_operational_reference_thresholds.py
# Adaptive thresholds for composite operational reference
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_operational_reference.csv"
)

OUTPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_operational_reference_adaptive.csv"
)

OUTPUT_LOG = os.path.join(
    OUTPUT_DIR,
    "operational_reference_thresholds_log.txt"
)

SCORE_COL = "operational_reference_score"


def classify_adaptive(score, t1, t2, t3):
    if pd.isna(score):
        return "Undefined"

    if score < t1:
        return "Critical"
    elif score < t2:
        return "Degraded"
    elif score < t3:
        return "Stable"
    else:
        return "Optimal"


if not os.path.exists(INPUT_DATASET):
    print(f"No existe: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET, low_memory=False)

df[SCORE_COL] = pd.to_numeric(df[SCORE_COL], errors="coerce")

df_eval = df.dropna(subset=[SCORE_COL]).copy()

# Umbrales adaptativos por percentiles
q25 = df_eval[SCORE_COL].quantile(0.25)
q50 = df_eval[SCORE_COL].quantile(0.50)
q75 = df_eval[SCORE_COL].quantile(0.75)

df["state_operational_reference_adaptive"] = df[SCORE_COL].apply(
    lambda x: classify_adaptive(x, q25, q50, q75)
)

distribution = df["state_operational_reference_adaptive"].value_counts()
distribution_pct = (
    df["state_operational_reference_adaptive"]
    .value_counts(normalize=True)
    * 100
)

# Export
df.to_csv(OUTPUT_DATASET, index=False)

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("ADAPTIVE OPERATIONAL REFERENCE THRESHOLDS\n")
    f.write("=========================================\n\n")

    f.write(f"Input dataset: {INPUT_DATASET}\n")
    f.write(f"Output dataset: {OUTPUT_DATASET}\n")
    f.write(f"Rows: {len(df)}\n\n")

    f.write("ADAPTIVE THRESHOLDS\n")
    f.write("===================\n")
    f.write(f"q25 Critical/Degraded: {q25:.4f}\n")
    f.write(f"q50 Degraded/Stable: {q50:.4f}\n")
    f.write(f"q75 Stable/Optimal: {q75:.4f}\n\n")

    f.write("ADAPTIVE STATE DISTRIBUTION\n")
    f.write("===========================\n")

    for state in distribution.index:
        f.write(
            f"{state}: {distribution[state]} "
            f"({distribution_pct[state]:.2f}%)\n"
        )

print("\n=================================")
print("ADAPTIVE OPERATIONAL REFERENCE GENERATED")
print("=================================")
print(f"Dataset: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print("\nAdaptive thresholds:")
print(f"q25={q25:.4f}, q50={q50:.4f}, q75={q75:.4f}")
print("\nAdaptive state distribution:")
print(distribution)