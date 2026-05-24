import pandas as pd
import os
import re

# ============================================================
# 12_generate_ieee_tables.py
# IEEE-ready tables for Dynamic IDOE research
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

TABLES_DIR = os.path.join(OUTPUT_DIR, "tables")
os.makedirs(TABLES_DIR, exist_ok=True)

DATASET_MASTER_LOG = os.path.join(OUTPUT_DIR, "dataset_master_log.txt")
DYNAMIC_IDOE_LOG = os.path.join(OUTPUT_DIR, "dynamic_idoe_log.txt")
DYNAMIC_IDOE_V2_LOG = os.path.join(OUTPUT_DIR, "dynamic_idoe_v2_log.txt")
THRESHOLD_LOG = os.path.join(OUTPUT_DIR, "threshold_optimization_log.txt")
OP_REF_LOG = os.path.join(OUTPUT_DIR, "operational_reference_thresholds_log.txt")
VALIDATION_LOG = os.path.join(OUTPUT_DIR, "validate_operational_reference_log.txt")

FEATURE_IMPORTANCE = os.path.join(OUTPUT_DIR, "ml_feature_importance.csv")
DATASET_FINAL = os.path.join(OUTPUT_DIR, "dataset_operational_reference_adaptive.csv")


def read_text(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_float(pattern, text, default=None):
    match = re.search(pattern, text)
    if match:
        return float(match.group(1))
    return default


def extract_int(pattern, text, default=None):
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    return default


# ============================================================
# LOAD LOGS
# ============================================================

master_log = read_text(DATASET_MASTER_LOG)
dynamic_log = read_text(DYNAMIC_IDOE_LOG)
v2_log = read_text(DYNAMIC_IDOE_V2_LOG)
threshold_log = read_text(THRESHOLD_LOG)
op_ref_log = read_text(OP_REF_LOG)
validation_log = read_text(VALIDATION_LOG)

# ============================================================
# TABLE I - DATASET SUMMARY
# ============================================================

table_dataset = pd.DataFrame([
    {
        "Metric": "Processed CSV files",
        "Value": extract_int(r"Archivos procesados:\s+(\d+)", master_log)
    },
    {
        "Metric": "Rows before consolidation",
        "Value": extract_int(r"Filas antes de consolidar:\s+(\d+)", master_log)
    },
    {
        "Metric": "Final rows",
        "Value": extract_int(r"Filas finales:\s+(\d+)", master_log)
    },
    {
        "Metric": "Valid records",
        "Value": extract_int(r"Registros válidos:\s+(\d+)", master_log)
    },
    {
        "Metric": "Invalid records",
        "Value": extract_int(r"Registros inválidos:\s+(\d+)", master_log)
    },
    {
        "Metric": "Temporal gaps > 180 s",
        "Value": extract_int(r"Gaps mayores a 180 segundos:\s+(\d+)", master_log)
    },
    {
        "Metric": "Maximum gap (s)",
        "Value": extract_float(r"Gap máximo detectado \(segundos\):\s+([0-9.]+)", master_log)
    }
])

table_dataset.to_csv(
    os.path.join(TABLES_DIR, "table_01_dataset_summary.csv"),
    index=False
)

# ============================================================
# TABLE II - IDOE MODEL COMPARISON
# ============================================================

table_model = pd.DataFrame([
    {
        "Model": "IDOE Base",
        "Description": "Instantaneous RF score based on SNR, MCS, and RSSI",
        "Uses Temporal Features": "No",
        "Uses Throughput in Index": "No",
        "Correlation with Throughput": extract_float(
            r"idoe_base vs dl_rate_mbps:\s+([0-9.\-]+)",
            dynamic_log
        )
    },
    {
        "Model": "D-IDOE V1",
        "Description": "Dynamic operational index using RF quality and temporal stability",
        "Uses Temporal Features": "Yes",
        "Uses Throughput in Index": "No",
        "Correlation with Throughput": extract_float(
            r"d_idoe vs dl_rate_mbps:\s+([0-9.\-]+)",
            dynamic_log
        )
    },
    {
        "Model": "D-IDOE V2",
        "Description": "ML-informed dynamic index emphasizing MCS and temporal stability",
        "Uses Temporal Features": "Yes",
        "Uses Throughput in Index": "No",
        "Correlation with Throughput": extract_float(
            r"D-IDOE V2 vs dl_rate_mbps:\s+([0-9.\-]+)",
            v2_log
        )
    }
])

table_model.to_csv(
    os.path.join(TABLES_DIR, "table_02_model_comparison.csv"),
    index=False
)

# ============================================================
# TABLE III - THRESHOLD OPTIMIZATION
# ============================================================

table_thresholds = pd.DataFrame([
    {
        "Threshold Strategy": "Percentile Base",
        "t1 Critical/Degraded": extract_float(r"q25=([0-9.]+)", threshold_log),
        "t2 Degraded/Stable": extract_float(r"q50=([0-9.]+)", threshold_log),
        "t3 Stable/Optimal": extract_float(r"q75=([0-9.]+)", threshold_log),
        "F1-score": extract_float(r"PERCENTILES BASE[\s\S]*?'f1':\s+([0-9.]+)", threshold_log)
    },
    {
        "Threshold Strategy": "Optimized",
        "t1 Critical/Degraded": extract_float(r"t1=([0-9.]+)", threshold_log),
        "t2 Degraded/Stable": extract_float(r"t2=([0-9.]+)", threshold_log),
        "t3 Stable/Optimal": extract_float(r"t3=([0-9.]+)", threshold_log),
        "F1-score": extract_float(r"MEJOR CONFIGURACIÓN[\s\S]*?'f1':\s+([0-9.]+)", threshold_log)
    }
])

table_thresholds.to_csv(
    os.path.join(TABLES_DIR, "table_03_threshold_optimization.csv"),
    index=False
)

# ============================================================
# TABLE IV - FINAL VALIDATION METRICS
# ============================================================

table_validation = pd.DataFrame([
    {
        "Validation Target": "Throughput-only reference",
        "Model": "Optimized D-IDOE",
        "Accuracy": extract_float(r"accuracy':\s+([0-9.]+)", threshold_log),
        "Precision": extract_float(r"precision':\s+([0-9.]+)", threshold_log),
        "Recall": extract_float(r"recall':\s+([0-9.]+)", threshold_log),
        "F1-score": extract_float(r"f1':\s+([0-9.]+)", threshold_log)
    },
    {
        "Validation Target": "Adaptive composite operational reference",
        "Model": "Optimized D-IDOE",
        "Accuracy": extract_float(r"Accuracy:\s+([0-9.]+)", validation_log),
        "Precision": extract_float(r"Precision:\s+([0-9.]+)", validation_log),
        "Recall": extract_float(r"Recall:\s+([0-9.]+)", validation_log),
        "F1-score": extract_float(r"F1-score:\s+([0-9.]+)", validation_log)
    }
])

table_validation.to_csv(
    os.path.join(TABLES_DIR, "table_04_validation_metrics.csv"),
    index=False
)

# ============================================================
# TABLE V - ADAPTIVE OPERATIONAL REFERENCE THRESHOLDS
# ============================================================

table_op_thresholds = pd.DataFrame([
    {
        "Boundary": "Critical / Degraded",
        "Threshold": extract_float(r"q25 Critical/Degraded:\s+([0-9.]+)", op_ref_log)
    },
    {
        "Boundary": "Degraded / Stable",
        "Threshold": extract_float(r"q50 Degraded/Stable:\s+([0-9.]+)", op_ref_log)
    },
    {
        "Boundary": "Stable / Optimal",
        "Threshold": extract_float(r"q75 Stable/Optimal:\s+([0-9.]+)", op_ref_log)
    }
])

table_op_thresholds.to_csv(
    os.path.join(TABLES_DIR, "table_05_operational_reference_thresholds.csv"),
    index=False
)

# ============================================================
# TABLE VI - STATE DISTRIBUTION
# ============================================================

if os.path.exists(DATASET_FINAL):
    df = pd.read_csv(DATASET_FINAL, low_memory=False)

    state_ref = (
        df["state_operational_reference_adaptive"]
        .value_counts()
        .rename_axis("Operational State")
        .reset_index(name="Composite Reference Records")
    )

    state_pred = (
        df["state_optimized_thresholds"]
        .value_counts()
        .rename_axis("Operational State")
        .reset_index(name="Optimized D-IDOE Records")
    )

    table_states = state_ref.merge(
        state_pred,
        on="Operational State",
        how="outer"
    ).fillna(0)

    total_ref = table_states["Composite Reference Records"].sum()
    total_pred = table_states["Optimized D-IDOE Records"].sum()

    table_states["Composite Reference (%)"] = (
        table_states["Composite Reference Records"] / total_ref * 100
    ).round(2)

    table_states["Optimized D-IDOE (%)"] = (
        table_states["Optimized D-IDOE Records"] / total_pred * 100
    ).round(2)

    table_states.to_csv(
        os.path.join(TABLES_DIR, "table_06_state_distribution.csv"),
        index=False
    )

# ============================================================
# TABLE VII - TOP FEATURE IMPORTANCE
# ============================================================

if os.path.exists(FEATURE_IMPORTANCE):
    importance = pd.read_csv(FEATURE_IMPORTANCE)

    importance.head(12).to_csv(
        os.path.join(TABLES_DIR, "table_07_top_feature_importance.csv"),
        index=False
    )

# ============================================================
# TABLE VIII - COMPOSITE REFERENCE COMPONENTS
# ============================================================

table_components = pd.DataFrame([
    {
        "Component": "15-minute mean throughput",
        "Weight": 0.30,
        "Purpose": "Sustained performance"
    },
    {
        "Component": "MCS",
        "Weight": 0.30,
        "Purpose": "Spectral efficiency and adaptive modulation state"
    },
    {
        "Component": "SNR",
        "Weight": 0.15,
        "Purpose": "RF channel quality"
    },
    {
        "Component": "MCS stability",
        "Weight": 0.10,
        "Purpose": "Operational modulation stability"
    },
    {
        "Component": "SNR stability",
        "Weight": 0.10,
        "Purpose": "Temporal channel stability"
    },
    {
        "Component": "Inverse MCS volatility",
        "Weight": 0.03,
        "Purpose": "Penalty for modulation instability"
    },
    {
        "Component": "Inverse SNR volatility",
        "Weight": 0.02,
        "Purpose": "Penalty for RF channel variability"
    }
])

table_components.to_csv(
    os.path.join(TABLES_DIR, "table_08_composite_reference_components.csv"),
    index=False
)

# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(TABLES_DIR, "tables_summary.txt")

with open(summary_path, "w", encoding="utf-8") as f:
    f.write("IEEE-READY TABLES GENERATED\n")
    f.write("===========================\n\n")

    for filename in sorted(os.listdir(TABLES_DIR)):
        f.write(filename + "\n")

print("\n=================================")
print("IEEE TABLES GENERATED")
print("=================================")
print(f"Directory: {TABLES_DIR}")

for filename in sorted(os.listdir(TABLES_DIR)):
    print("-", filename)