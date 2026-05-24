import pandas as pd
import numpy as np
import os

# ============================================================
# 08_operational_reference.py
# Composite Operational Reference
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_dynamic_idoe_v2_thresholds.csv"
)

OUTPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_operational_reference.csv"
)

OUTPUT_LOG = os.path.join(
    OUTPUT_DIR,
    "operational_reference_log.txt"
)

# ============================================================
# HELPERS
# ============================================================

def minmax(series):
    series = pd.to_numeric(series, errors="coerce")

    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val):
        return pd.Series(np.nan, index=series.index)

    if max_val == min_val:
        return pd.Series(0.5, index=series.index)

    return (series - min_val) / (max_val - min_val)


def inverse_minmax(series):
    return 1 - minmax(series)


def classify_operational(score):

    if pd.isna(score):
        return "Undefined"

    if score >= 0.75:
        return "Optimal"

    elif score >= 0.55:
        return "Stable"

    elif score >= 0.35:
        return "Degraded"

    else:
        return "Critical"


# ============================================================
# LOAD DATA
# ============================================================

if not os.path.exists(INPUT_DATASET):
    print(f"No existe: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET, low_memory=False)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

df = df.dropna(subset=["timestamp"])

df = df.sort_values("timestamp").reset_index(drop=True)

# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_cols = [
    "dl_rate_mbps",
    "dl_mcs",
    "dl_snr_db",
    "mcs_stability_score",
    "snr_stability_score",
    "mcs_volatility_score",
    "dl_snr_db_std_15m"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ============================================================
# ROLLING THROUGHPUT
# ============================================================

df = df.set_index("timestamp")

df["dl_rate_mean_15m"] = (
    df["dl_rate_mbps"]
    .rolling("15min")
    .mean()
)

df = df.reset_index()

# ============================================================
# MCS RANGES
# ============================================================

def classify_mcs(mcs):

    if pd.isna(mcs):
        return "Undefined"

    if mcs >= 104:
        return "High MCS"

    elif mcs >= 100:
        return "Medium MCS"

    else:
        return "Low MCS"


df["mcs_range"] = df["dl_mcs"].apply(classify_mcs)

# ============================================================
# NORMALIZATION
# ============================================================

df["rate15_norm"] = minmax(df["dl_rate_mean_15m"])

df["mcs_norm_v2"] = minmax(df["dl_mcs"])

df["snr_norm_v2"] = minmax(df["dl_snr_db"])

df["mcs_stability_norm"] = minmax(df["mcs_stability_score"])

df["snr_stability_norm"] = minmax(df["snr_stability_score"])

df["mcs_volatility_inverse"] = inverse_minmax(
    df["mcs_volatility_score"]
)

df["snr_volatility_inverse"] = inverse_minmax(
    df["dl_snr_db_std_15m"]
)

# ============================================================
# COMPOSITE OPERATIONAL SCORE
# ============================================================

df["operational_reference_score"] = (

    0.30 * df["rate15_norm"] +

    0.30 * df["mcs_norm_v2"] +

    0.15 * df["snr_norm_v2"] +

    0.10 * df["mcs_stability_norm"] +

    0.10 * df["snr_stability_norm"] +

    0.03 * df["mcs_volatility_inverse"] +

    0.02 * df["snr_volatility_inverse"]

)

df["operational_reference_score"] = (
    df["operational_reference_score"]
    .clip(0, 1)
)

# ============================================================
# FINAL OPERATIONAL STATE
# ============================================================

df["state_operational_reference"] = (
    df["operational_reference_score"]
    .apply(classify_operational)
)

# ============================================================
# DISTRIBUTION
# ============================================================

distribution = (
    df["state_operational_reference"]
    .value_counts(dropna=False)
)

distribution_pct = (
    df["state_operational_reference"]
    .value_counts(normalize=True, dropna=False)
    * 100
)

# ============================================================
# EXPORT
# ============================================================

df.to_csv(OUTPUT_DATASET, index=False)

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:

    f.write("COMPOSITE OPERATIONAL REFERENCE\n")
    f.write("================================\n\n")

    f.write(f"Input dataset: {INPUT_DATASET}\n")
    f.write(f"Output dataset: {OUTPUT_DATASET}\n\n")

    f.write(f"Rows: {len(df)}\n\n")

    f.write("COMPOSITE SCORE COMPONENTS\n")
    f.write("==========================\n")

    f.write("30% -> 15-minute throughput\n")
    f.write("30% -> MCS\n")
    f.write("15% -> SNR\n")
    f.write("10% -> MCS stability\n")
    f.write("10% -> SNR stability\n")
    f.write("03% -> MCS volatility inverse\n")
    f.write("02% -> SNR volatility inverse\n\n")

    f.write("STATE DISTRIBUTION\n")
    f.write("==================\n")

    for state in distribution.index:

        f.write(
            f"{state}: "
            f"{distribution[state]} "
            f"({distribution_pct[state]:.2f}%)\n"
        )

print("\n=================================")
print("COMPOSITE OPERATIONAL REFERENCE GENERATED")
print("=================================")
print(f"Dataset: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")

print("\nOperational state distribution:\n")

print(distribution)