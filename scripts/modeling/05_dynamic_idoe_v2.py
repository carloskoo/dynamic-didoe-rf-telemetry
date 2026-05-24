import pandas as pd
import numpy as np
import os

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix

# ============================================================
# 05_dynamic_idoe_v2.py
# Recalcula D-IDOE V2 usando evidencia de importancia ML
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe_v2.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "dynamic_idoe_v2_log.txt")

MAIN_WINDOW = "15m"


def minmax(series):
    series = pd.to_numeric(series, errors="coerce")
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(np.nan, index=series.index)

    return (series - min_val) / (max_val - min_val)


def inverse_minmax(series):
    return 1 - minmax(series)


def classify_state(score):
    if pd.isna(score):
        return "Undefined"
    elif score >= 0.80:
        return "Optimal"
    elif score >= 0.60:
        return "Stable"
    elif score >= 0.40:
        return "Degraded"
    else:
        return "Critical"


if not os.path.exists(INPUT_DATASET):
    print(f"No existe el archivo: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET, low_memory=False)

if "timestamp" not in df.columns:
    print("No existe columna timestamp.")
    raise SystemExit(1)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

required_cols = [
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs",
    "dl_rate_mbps",

    "snr_norm",
    "rssi_norm",
    "mcs_norm",
    "idoe_base",
    "d_idoe",
    "rate_norm_validation",
    "state_rate_reference",

    "snr_stability_score",
    "rssi_stability_score",
    "mcs_stability_score",
    "mcs_volatility_score",
    "snr_trend_score",
    "mcs_trend_score",

    f"dl_mcs_std_{MAIN_WINDOW}",
    f"mcs_stability_{MAIN_WINDOW}"
]

missing = [c for c in required_cols if c not in df.columns]

if missing:
    print("Faltan columnas necesarias:")
    for c in missing:
        print(" -", c)
    raise SystemExit(1)

for col in required_cols:
    if col != "state_rate_reference":
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ============================================================
# COMPONENTE RF V2
# Evidencia ML: MCS domina el comportamiento operacional
# ============================================================

df["rf_quality_score_v2"] = (
    0.55 * df["mcs_norm"] +
    0.25 * df["snr_norm"] +
    0.20 * df["rssi_norm"]
)

# ============================================================
# COMPONENTE TEMPORAL V2
# Mayor peso a estabilidad/volatilidad de MCS
# ============================================================

df["temporal_stability_score_v2"] = (
    0.40 * df["mcs_stability_score"] +
    0.25 * df["mcs_volatility_score"] +
    0.15 * df["snr_stability_score"] +
    0.10 * df["rssi_stability_score"] +
    0.05 * df["mcs_trend_score"] +
    0.05 * df["snr_trend_score"]
)

# ============================================================
# D-IDOE V2
# 75 % calidad RF + 25 % estabilidad temporal
# ============================================================

df["d_idoe_v2"] = (
    0.75 * df["rf_quality_score_v2"] +
    0.25 * df["temporal_stability_score_v2"]
)

df["d_idoe_v2"] = df["d_idoe_v2"].clip(0, 1)

df["state_d_idoe_v2"] = df["d_idoe_v2"].apply(classify_state)

# ============================================================
# MÉTRICAS DE COMPARACIÓN
# ============================================================

df_eval = df.dropna(subset=[
    "idoe_base",
    "d_idoe",
    "d_idoe_v2",
    "dl_rate_mbps",
    "rate_norm_validation",
    "state_rate_reference"
]).copy()

df_eval = df_eval[df_eval["state_rate_reference"] != "Undefined"].copy()

corr_base = df_eval["idoe_base"].corr(df_eval["dl_rate_mbps"])
corr_v1 = df_eval["d_idoe"].corr(df_eval["dl_rate_mbps"])
corr_v2 = df_eval["d_idoe_v2"].corr(df_eval["dl_rate_mbps"])

corr_base_norm = df_eval["idoe_base"].corr(df_eval["rate_norm_validation"])
corr_v1_norm = df_eval["d_idoe"].corr(df_eval["rate_norm_validation"])
corr_v2_norm = df_eval["d_idoe_v2"].corr(df_eval["rate_norm_validation"])

# Comparación de clasificación contra referencia de throughput
y_true = df_eval["state_rate_reference"]
y_pred_v1 = df_eval["state_d_idoe"]
y_pred_v2 = df_eval["state_d_idoe_v2"]

acc_v1 = accuracy_score(y_true, y_pred_v1)
prec_v1 = precision_score(y_true, y_pred_v1, average="weighted", zero_division=0)
rec_v1 = recall_score(y_true, y_pred_v1, average="weighted", zero_division=0)
f1_v1 = f1_score(y_true, y_pred_v1, average="weighted", zero_division=0)

acc_v2 = accuracy_score(y_true, y_pred_v2)
prec_v2 = precision_score(y_true, y_pred_v2, average="weighted", zero_division=0)
rec_v2 = recall_score(y_true, y_pred_v2, average="weighted", zero_division=0)
f1_v2 = f1_score(y_true, y_pred_v2, average="weighted", zero_division=0)

state_counts_v2 = df_eval["state_d_idoe_v2"].value_counts()
state_percent_v2 = df_eval["state_d_idoe_v2"].value_counts(normalize=True) * 100

# ============================================================
# EXPORTACIÓN
# ============================================================

df.to_csv(OUTPUT_DATASET, index=False)

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("RESUMEN DYNAMIC IDOE V2\n")
    f.write("=======================\n\n")

    f.write(f"Archivo de entrada: {INPUT_DATASET}\n")
    f.write(f"Archivo generado: {OUTPUT_DATASET}\n")
    f.write(f"Filas evaluadas: {len(df_eval)}\n\n")

    f.write("JUSTIFICACIÓN V2\n")
    f.write("================\n")
    f.write("El D-IDOE V2 incrementa el peso del MCS y de su estabilidad temporal, ")
    f.write("debido a que la validación ML mostró que las variables asociadas al MCS ")
    f.write("presentan la mayor importancia en la explicación del estado operacional.\n\n")

    f.write("PESOS UTILIZADOS\n")
    f.write("================\n")
    f.write("RF quality V2 = 0.55*MCS + 0.25*SNR + 0.20*RSSI\n")
    f.write("Temporal stability V2 = 0.40*MCS stability + 0.25*MCS volatility + 0.15*SNR stability + 0.10*RSSI stability + 0.05*MCS trend + 0.05*SNR trend\n")
    f.write("D-IDOE V2 = 0.75*RF quality V2 + 0.25*Temporal stability V2\n\n")

    f.write("CORRELACIÓN CON THROUGHPUT\n")
    f.write("==========================\n")
    f.write(f"IDOE base vs dl_rate_mbps: {corr_base:.4f}\n")
    f.write(f"D-IDOE V1 vs dl_rate_mbps: {corr_v1:.4f}\n")
    f.write(f"D-IDOE V2 vs dl_rate_mbps: {corr_v2:.4f}\n\n")

    f.write("CORRELACIÓN CON THROUGHPUT NORMALIZADO\n")
    f.write("======================================\n")
    f.write(f"IDOE base vs rate_norm_validation: {corr_base_norm:.4f}\n")
    f.write(f"D-IDOE V1 vs rate_norm_validation: {corr_v1_norm:.4f}\n")
    f.write(f"D-IDOE V2 vs rate_norm_validation: {corr_v2_norm:.4f}\n\n")

    f.write("CLASIFICACIÓN VS REFERENCIA THROUGHPUT\n")
    f.write("======================================\n")
    f.write(f"D-IDOE V1 Accuracy: {acc_v1:.4f}\n")
    f.write(f"D-IDOE V1 Precision: {prec_v1:.4f}\n")
    f.write(f"D-IDOE V1 Recall: {rec_v1:.4f}\n")
    f.write(f"D-IDOE V1 F1-score: {f1_v1:.4f}\n\n")

    f.write(f"D-IDOE V2 Accuracy: {acc_v2:.4f}\n")
    f.write(f"D-IDOE V2 Precision: {prec_v2:.4f}\n")
    f.write(f"D-IDOE V2 Recall: {rec_v2:.4f}\n")
    f.write(f"D-IDOE V2 F1-score: {f1_v2:.4f}\n\n")

    f.write("DISTRIBUCIÓN DE ESTADOS D-IDOE V2\n")
    f.write("=================================\n")
    for state in state_counts_v2.index:
        f.write(f"{state}: {state_counts_v2[state]} registros ({state_percent_v2[state]:.2f}%)\n")

    f.write("\nREPORTE CLASIFICACIÓN V2\n")
    f.write("========================\n")
    f.write(classification_report(y_true, y_pred_v2, zero_division=0))

    f.write("\nMATRIZ DE CONFUSIÓN V2\n")
    f.write("======================\n")
    labels = sorted(y_true.unique())
    cm = confusion_matrix(y_true, y_pred_v2, labels=labels)
    f.write("Labels: " + str(labels) + "\n")
    f.write(str(cm))

print("\n=================================")
print("DYNAMIC IDOE V2 GENERADO")
print("=================================")
print(f"Archivo: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print(f"Filas evaluadas: {len(df_eval)}")
print("\nCorrelación con throughput:")
print(f"IDOE base: {corr_base:.4f}")
print(f"D-IDOE V1: {corr_v1:.4f}")
print(f"D-IDOE V2: {corr_v2:.4f}")
print("\nClasificación vs referencia:")
print(f"D-IDOE V1 F1-score: {f1_v1:.4f}")
print(f"D-IDOE V2 F1-score: {f1_v2:.4f}")
print("\nDistribución estados V2:")
print(state_counts_v2)