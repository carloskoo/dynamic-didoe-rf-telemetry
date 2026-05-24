import pandas as pd
import numpy as np
import os

# ============================================================
# 03_dynamic_idoe.py
# Calcula IDOE base y Dynamic IDOE sin usar throughput
# ============================================================

# =========================
# CONFIGURACIÓN
# =========================
BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_temporal_features.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "dynamic_idoe_log.txt")

# Ventana principal del modelo dinámico
MAIN_WINDOW = "15m"

# =========================
# FUNCIONES AUXILIARES
# =========================

def minmax(series):
    """
    Normalización Min-Max segura.
    """
    series = pd.to_numeric(series, errors="coerce")
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(np.nan, index=series.index)

    return (series - min_val) / (max_val - min_val)


def inverse_minmax(series):
    """
    Normalización inversa.
    Valores bajos de volatilidad/rango son mejores.
    """
    norm = minmax(series)
    return 1 - norm


def classify_state(score):
    """
    Clasificación operativa del enlace.
    """
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


# =========================
# CARGA DE DATOS
# =========================
if not os.path.exists(INPUT_DATASET):
    print(f"No existe el archivo de entrada: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET)

if "timestamp" not in df.columns:
    print("El dataset no contiene la columna timestamp.")
    raise SystemExit(1)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# =========================
# VALIDACIÓN DE COLUMNAS
# =========================
required_cols = [
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs",
    "dl_rate_mbps",
    f"dl_snr_db_std_{MAIN_WINDOW}",
    f"dl_rssi_dbm_std_{MAIN_WINDOW}",
    f"dl_mcs_std_{MAIN_WINDOW}",
    f"dl_snr_db_slope_{MAIN_WINDOW}",
    f"dl_mcs_slope_{MAIN_WINDOW}",
    f"mcs_stability_{MAIN_WINDOW}"
]

missing = [c for c in required_cols if c not in df.columns]

if missing:
    print("Faltan columnas necesarias:")
    for c in missing:
        print(" -", c)
    raise SystemExit(1)

# Convertir numéricos
for col in required_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================
# NORMALIZACIÓN DE MÉTRICAS RF BASE
# =========================

# RSSI: como es negativo, valores menos negativos son mejores.
# Min-Max funciona directamente porque -70 > -80.
df["snr_norm"] = minmax(df["dl_snr_db"])
df["rssi_norm"] = minmax(df["dl_rssi_dbm"])
df["mcs_norm"] = minmax(df["dl_mcs"])

# Throughput solo para validación, NO entra al índice.
df["rate_norm_validation"] = minmax(df["dl_rate_mbps"])

# =========================
# IDOE BASE
# Sin throughput. Línea base interpretable.
# =========================
df["idoe_base"] = (
    0.40 * df["snr_norm"] +
    0.40 * df["mcs_norm"] +
    0.20 * df["rssi_norm"]
)

# =========================
# COMPONENTES TEMPORALES
# =========================

snr_std_col = f"dl_snr_db_std_{MAIN_WINDOW}"
rssi_std_col = f"dl_rssi_dbm_std_{MAIN_WINDOW}"
mcs_std_col = f"dl_mcs_std_{MAIN_WINDOW}"
snr_slope_col = f"dl_snr_db_slope_{MAIN_WINDOW}"
mcs_slope_col = f"dl_mcs_slope_{MAIN_WINDOW}"
mcs_stability_col = f"mcs_stability_{MAIN_WINDOW}"

# Estabilidad por baja volatilidad
df["snr_stability_score"] = inverse_minmax(df[snr_std_col])
df["rssi_stability_score"] = inverse_minmax(df[rssi_std_col])
df["mcs_stability_score"] = df[mcs_stability_col]

# Penalización por variabilidad del MCS
df["mcs_volatility_score"] = inverse_minmax(df[mcs_std_col])

# Tendencia positiva o estable del SNR
# Si la pendiente es negativa, penaliza.
snr_slope = df[snr_slope_col]
df["snr_trend_score"] = minmax(snr_slope)

# Tendencia del MCS
mcs_slope = df[mcs_slope_col]
df["mcs_trend_score"] = minmax(mcs_slope)

# Componente de estabilidad temporal integrado
df["temporal_stability_score"] = (
    0.30 * df["snr_stability_score"] +
    0.20 * df["rssi_stability_score"] +
    0.25 * df["mcs_stability_score"] +
    0.15 * df["mcs_volatility_score"] +
    0.05 * df["snr_trend_score"] +
    0.05 * df["mcs_trend_score"]
)

# =========================
# DYNAMIC IDOE
# Modelo principal
# =========================

# Componente RF instantáneo
df["rf_quality_score"] = (
    0.45 * df["snr_norm"] +
    0.40 * df["mcs_norm"] +
    0.15 * df["rssi_norm"]
)

# Dynamic IDOE:
# 70% calidad RF actual + 30% estabilidad temporal
df["d_idoe"] = (
    0.70 * df["rf_quality_score"] +
    0.30 * df["temporal_stability_score"]
)

# Limitar al rango [0,1]
df["idoe_base"] = df["idoe_base"].clip(0, 1)
df["d_idoe"] = df["d_idoe"].clip(0, 1)

# =========================
# CLASIFICACIÓN OPERACIONAL
# =========================
df["state_idoe_base"] = df["idoe_base"].apply(classify_state)
df["state_d_idoe"] = df["d_idoe"].apply(classify_state)

# Estado de referencia basado en throughput.
# Solo para validación, NO para cálculo del índice.
df["state_rate_reference"] = df["rate_norm_validation"].apply(classify_state)

# =========================
# COLUMNAS DE SALIDA
# =========================
output_cols = [
    "timestamp",
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs",
    "dl_rate_mbps",

    "snr_norm",
    "rssi_norm",
    "mcs_norm",
    "rate_norm_validation",

    "idoe_base",
    "rf_quality_score",
    "temporal_stability_score",
    "d_idoe",

    "state_idoe_base",
    "state_d_idoe",
    "state_rate_reference",

    "snr_stability_score",
    "rssi_stability_score",
    "mcs_stability_score",
    "mcs_volatility_score",
    "snr_trend_score",
    "mcs_trend_score",

    snr_std_col,
    rssi_std_col,
    mcs_std_col,
    snr_slope_col,
    mcs_slope_col,
    mcs_stability_col
]

# Mantener también columnas de origen si existen
optional_cols = [
    "source_file",
    "source_type",
    "note"
]

for col in optional_cols:
    if col in df.columns:
        output_cols.append(col)

df_out = df[[c for c in output_cols if c in df.columns]].copy()

# Eliminar filas sin índice por falta de ventana inicial
df_out = df_out.dropna(subset=["idoe_base", "d_idoe", "dl_rate_mbps"])

# =========================
# MÉTRICAS DE VALIDACIÓN BÁSICA
# =========================

corr_base = df_out["idoe_base"].corr(df_out["dl_rate_mbps"])
corr_dynamic = df_out["d_idoe"].corr(df_out["dl_rate_mbps"])

corr_base_rate_norm = df_out["idoe_base"].corr(df_out["rate_norm_validation"])
corr_dynamic_rate_norm = df_out["d_idoe"].corr(df_out["rate_norm_validation"])

state_counts = df_out["state_d_idoe"].value_counts()
state_percent = df_out["state_d_idoe"].value_counts(normalize=True) * 100

# =========================
# EXPORTACIÓN
# =========================
df_out.to_csv(OUTPUT_DATASET, index=False)

# =========================
# LOG
# =========================
with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("RESUMEN DYNAMIC IDOE\n")
    f.write("====================\n\n")

    f.write(f"Archivo de entrada: {INPUT_DATASET}\n")
    f.write(f"Archivo generado: {OUTPUT_DATASET}\n")
    f.write(f"Ventana principal: {MAIN_WINDOW}\n")
    f.write(f"Filas finales: {len(df_out)}\n\n")

    f.write("MODELOS GENERADOS\n")
    f.write("=================\n")
    f.write("1. idoe_base: SNR + MCS + RSSI, sin throughput.\n")
    f.write("2. d_idoe: RF quality + temporal stability, sin throughput.\n")
    f.write("3. state_rate_reference: referencia basada en throughput para validación.\n\n")

    f.write("CORRELACIÓN CON THROUGHPUT\n")
    f.write("==========================\n")
    f.write(f"idoe_base vs dl_rate_mbps: {corr_base:.4f}\n")
    f.write(f"d_idoe vs dl_rate_mbps: {corr_dynamic:.4f}\n")
    f.write(f"idoe_base vs rate_norm_validation: {corr_base_rate_norm:.4f}\n")
    f.write(f"d_idoe vs rate_norm_validation: {corr_dynamic_rate_norm:.4f}\n\n")

    f.write("DISTRIBUCIÓN DE ESTADOS D-IDOE\n")
    f.write("==============================\n")
    for state in state_counts.index:
        f.write(f"{state}: {state_counts[state]} registros ({state_percent[state]:.2f}%)\n")

    f.write("\nPESOS UTILIZADOS\n")
    f.write("================\n")
    f.write("IDOE base = 0.40*SNR + 0.40*MCS + 0.20*RSSI\n")
    f.write("RF quality = 0.45*SNR + 0.40*MCS + 0.15*RSSI\n")
    f.write("Temporal stability = 0.30*SNR stability + 0.20*RSSI stability + 0.25*MCS stability + 0.15*MCS volatility + 0.05*SNR trend + 0.05*MCS trend\n")
    f.write("D-IDOE = 0.70*RF quality + 0.30*Temporal stability\n")

print("\n=================================")
print("DYNAMIC IDOE GENERADO")
print("=================================")
print(f"Archivo: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print(f"Filas finales: {len(df_out)}")
print(f"Correlación IDOE base vs throughput: {corr_base:.4f}")
print(f"Correlación D-IDOE vs throughput: {corr_dynamic:.4f}")
print("\nDistribución de estados D-IDOE:")
print(state_counts)