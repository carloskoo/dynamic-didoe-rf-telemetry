import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

# ============================================================
# 11_generate_final_figures.py
# Final IEEE-style figures for operational reference validation
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_operational_reference_adaptive.csv"
)

INPUT_CM = os.path.join(
    OUTPUT_DIR,
    "confusion_matrix_operational_reference.csv"
)

FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures_final")
os.makedirs(FIGURES_DIR, exist_ok=True)

REFERENCE_COL = "state_operational_reference_adaptive"
PREDICTION_COL = "state_optimized_thresholds"

STATE_ORDER = ["Critical", "Degraded", "Stable", "Optimal"]

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_DATASET, low_memory=False)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

numeric_cols = [
    "d_idoe_v2",
    "operational_reference_score",
    "dl_rate_mbps",
    "dl_rate_mean_15m",
    "dl_mcs",
    "dl_snr_db"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["timestamp", REFERENCE_COL, PREDICTION_COL])

# ============================================================
# STYLE
# ============================================================

plt.rcParams["figure.figsize"] = (11, 6)
plt.rcParams["font.size"] = 11

# ============================================================
# FIGURE 1: Confusion Matrix
# ============================================================

y_true = df[REFERENCE_COL].astype(str)
y_pred = df[PREDICTION_COL].astype(str)

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=STATE_ORDER
)

fig = plt.figure(figsize=(7, 6))

plt.imshow(cm, interpolation="nearest")
plt.title("Confusion Matrix: Optimized D-IDOE vs Composite Reference")
plt.xlabel("Predicted Operational State")
plt.ylabel("Reference Operational State")

plt.xticks(
    np.arange(len(STATE_ORDER)),
    STATE_ORDER,
    rotation=45,
    ha="right"
)

plt.yticks(
    np.arange(len(STATE_ORDER)),
    STATE_ORDER
)

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(
            j,
            i,
            str(cm[i, j]),
            ha="center",
            va="center"
        )

plt.colorbar(label="Number of Records")
plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig09_confusion_matrix_operational_reference.png"),
    dpi=300
)

plt.close()

# ============================================================
# FIGURE 2: Operational Reference Score Distribution
# ============================================================

fig = plt.figure()

plt.hist(
    df["operational_reference_score"].dropna(),
    bins=60
)

plt.title("Distribution of Composite Operational Reference Score")
plt.xlabel("Composite Operational Reference Score")
plt.ylabel("Frequency")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig10_operational_reference_score_distribution.png"),
    dpi=300
)

plt.close()

# ============================================================
# FIGURE 3: Reference vs Optimized D-IDOE State Distribution
# ============================================================

ref_counts = (
    df[REFERENCE_COL]
    .value_counts()
    .reindex(STATE_ORDER)
    .fillna(0)
)

pred_counts = (
    df[PREDICTION_COL]
    .value_counts()
    .reindex(STATE_ORDER)
    .fillna(0)
)

x = np.arange(len(STATE_ORDER))
width = 0.35

fig = plt.figure(figsize=(10, 6))

plt.bar(
    x - width / 2,
    ref_counts.values,
    width,
    label="Composite Reference"
)

plt.bar(
    x + width / 2,
    pred_counts.values,
    width,
    label="Optimized D-IDOE"
)

plt.title("Operational State Distribution: Reference vs Optimized D-IDOE")
plt.xlabel("Operational State")
plt.ylabel("Number of Records")
plt.xticks(x, STATE_ORDER)
plt.legend()

plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig11_reference_vs_d_idoe_states.png"),
    dpi=300
)

plt.close()

# ============================================================
# FIGURE 4: D-IDOE V2 by Composite Reference State
# ============================================================

box_data = []

for state in STATE_ORDER:
    values = df.loc[
        df[REFERENCE_COL] == state,
        "d_idoe_v2"
    ].dropna()

    box_data.append(values)

fig = plt.figure(figsize=(9, 6))

plt.boxplot(
    box_data,
    tick_labels=STATE_ORDER
)

plt.title("Dynamic IDOE V2 by Composite Operational Reference State")
plt.xlabel("Reference Operational State")
plt.ylabel("D-IDOE V2 Score")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig12_d_idoe_by_reference_state.png"),
    dpi=300
)

plt.close()

# ============================================================
# FIGURE 5: 15-min Throughput by Reference State
# ============================================================

if "dl_rate_mean_15m" in df.columns:

    box_data = []

    for state in STATE_ORDER:
        values = df.loc[
            df[REFERENCE_COL] == state,
            "dl_rate_mean_15m"
        ].dropna()

        box_data.append(values)

    fig = plt.figure(figsize=(9, 6))

    plt.boxplot(
        box_data,
        tick_labels=STATE_ORDER
    )

    plt.title("15-Minute Mean Throughput by Composite Operational State")
    plt.xlabel("Reference Operational State")
    plt.ylabel("15-Minute Mean Downlink Throughput (Mbps)")
    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        os.path.join(FIGURES_DIR, "fig13_throughput15_by_reference_state.png"),
        dpi=300
    )

    plt.close()

# ============================================================
# FIGURE 6: Temporal Evolution with Reference State
# ============================================================

sample = df.iloc[::30].copy()

fig = plt.figure(figsize=(12, 6))

plt.plot(
    sample["timestamp"],
    sample["d_idoe_v2"],
    linewidth=0.8,
    label="D-IDOE V2"
)

plt.plot(
    sample["timestamp"],
    sample["operational_reference_score"],
    linewidth=0.8,
    label="Composite Reference Score"
)

plt.title("Temporal Evolution of D-IDOE V2 and Composite Reference Score")
plt.xlabel("Time")
plt.ylabel("Score")
plt.legend()
plt.grid(True)

plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig14_temporal_d_idoe_vs_reference.png"),
    dpi=300
)

plt.close()

# ============================================================
# FIGURE 7: MCS by Reference State
# ============================================================

box_data = []

for state in STATE_ORDER:
    values = df.loc[
        df[REFERENCE_COL] == state,
        "dl_mcs"
    ].dropna()

    box_data.append(values)

fig = plt.figure(figsize=(9, 6))

plt.boxplot(
    box_data,
    tick_labels=STATE_ORDER
)

plt.title("MCS Distribution by Composite Operational State")
plt.xlabel("Reference Operational State")
plt.ylabel("Downlink MCS")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    os.path.join(FIGURES_DIR, "fig15_mcs_by_reference_state.png"),
    dpi=300
)

plt.close()

# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(FIGURES_DIR, "final_figures_summary.txt")

with open(summary_path, "w", encoding="utf-8") as f:
    f.write("FINAL FIGURES GENERATED\n")
    f.write("=======================\n\n")
    for filename in sorted(os.listdir(FIGURES_DIR)):
        f.write(filename + "\n")

print("\n=================================")
print("FINAL FIGURES GENERATED")
print("=================================")
print(f"Directory: {FIGURES_DIR}")

for filename in sorted(os.listdir(FIGURES_DIR)):
    print("-", filename)