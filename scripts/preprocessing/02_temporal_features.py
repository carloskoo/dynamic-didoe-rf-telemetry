import pandas as pd
import numpy as np
import os

# ============================================================
# 02_temporal_features.py
# Genera variables temporales para el Dynamic IDOE
# ============================================================

# =========================
# CONFIGURACIÓN
# =========================
BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_master.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_temporal_features.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "temporal_features_log.txt")

# Ventanas temporales
WINDOWS = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "60m": "60min"
}

# Columnas RF base
RF_COLUMNS = [
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs"
]

TARGET_COLUMN = "dl_rate_mbps"


# =========================
# FUNCIONES AUXILIARES
# =========================

def rolling_slope(values):
    """
    Calcula una pendiente simple mediante regresión lineal
    sobre una ventana móvil.
    """
    y = np.asarray(values, dtype=float)

    if len(y) < 3:
        return np.nan

    if np.isnan(y).any():
        return np.nan

    x = np.arange(len(y))

    try:
        slope = np.polyfit(x, y, 1)[0]
        return slope
    except Exception:
        return np.nan


def minmax(series):
    """
    Normalización Min-Max segura.
    """
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(np.nan, index=series.index)

    return (series - min_val) / (max_val - min_val)


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
df = df.sort_values("timestamp")

# Usar solo registros válidos
if "valid_record" in df.columns:
    df = df[df["valid_record"] == True].copy()

# Convertir columnas numéricas
for col in RF_COLUMNS + [TARGET_COLUMN]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=RF_COLUMNS + [TARGET_COLUMN])

# Eliminar duplicados por timestamp
df = df.drop_duplicates(subset=["timestamp"], keep="first")

# Index temporal para rolling time-based
df = df.set_index("timestamp")
df = df.sort_index()

log_lines = []

log_lines.append("RESUMEN DE FEATURE ENGINEERING TEMPORAL")
log_lines.append("=======================================")
log_lines.append(f"Registros válidos usados: {len(df)}")
log_lines.append(f"Periodo inicial: {df.index.min()}")
log_lines.append(f"Periodo final: {df.index.max()}")
log_lines.append("")

# =========================
# FEATURES TEMPORALES
# =========================

for label, window in WINDOWS.items():
    log_lines.append(f"Generando features para ventana: {label}")

    for col in RF_COLUMNS:
        # Promedio móvil
        df[f"{col}_mean_{label}"] = (
            df[col]
            .rolling(window=window, min_periods=3)
            .mean()
        )

        # Desviación estándar móvil
        df[f"{col}_std_{label}"] = (
            df[col]
            .rolling(window=window, min_periods=3)
            .std()
        )

        # Mínimo móvil
        df[f"{col}_min_{label}"] = (
            df[col]
            .rolling(window=window, min_periods=3)
            .min()
        )

        # Máximo móvil
        df[f"{col}_max_{label}"] = (
            df[col]
            .rolling(window=window, min_periods=3)
            .max()
        )

        # Rango móvil
        df[f"{col}_range_{label}"] = (
            df[f"{col}_max_{label}"] - df[f"{col}_min_{label}"]
        )

        # Pendiente temporal
        # Para evitar que sea demasiado pesado, usamos rolling por número aproximado de muestras
        # Se estima 1 muestra/minuto en la fase actual.
        n_points = {
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "60m": 60
        }[label]

        df[f"{col}_slope_{label}"] = (
            df[col]
            .rolling(window=n_points, min_periods=3)
            .apply(rolling_slope, raw=False)
        )

# =========================
# FEATURES DE CAMBIO INSTANTÁNEO
# =========================
df["snr_delta"] = df["dl_snr_db"].diff()
df["rssi_delta"] = df["dl_rssi_dbm"].diff()
df["mcs_delta"] = df["dl_mcs"].diff()
df["rate_delta"] = df["dl_rate_mbps"].diff()

df["snr_abs_delta"] = df["snr_delta"].abs()
df["rssi_abs_delta"] = df["rssi_delta"].abs()
df["mcs_abs_delta"] = df["mcs_delta"].abs()
df["rate_abs_delta"] = df["rate_delta"].abs()

# =========================
# MÉTRICAS DE ESTABILIDAD
# =========================

# MCS estable cuando no cambia respecto al registro anterior
df["mcs_unchanged"] = (df["dl_mcs"].diff().fillna(0) == 0).astype(int)

for label, window in WINDOWS.items():
    df[f"mcs_stability_{label}"] = (
        df["mcs_unchanged"]
        .rolling(window=window, min_periods=3)
        .mean()
    )

# Estabilidad RF básica:
# Menor volatilidad de SNR y RSSI implica mayor estabilidad.
# Se genera una versión normalizada invertida de la volatilidad para uso futuro.
for label in WINDOWS.keys():
    snr_std_col = f"dl_snr_db_std_{label}"
    rssi_std_col = f"dl_rssi_dbm_std_{label}"
    mcs_std_col = f"dl_mcs_std_{label}"

    if snr_std_col in df.columns:
        df[f"snr_stability_{label}"] = 1 - minmax(df[snr_std_col])

    if rssi_std_col in df.columns:
        df[f"rssi_stability_{label}"] = 1 - minmax(df[rssi_std_col])

    if mcs_std_col in df.columns:
        df[f"mcs_volatility_inv_{label}"] = 1 - minmax(df[mcs_std_col])

# =========================
# FEATURES TEMPORALES DEL TARGET
# Solo para análisis/validación, NO para construir el índice
# =========================

for label, window in WINDOWS.items():
    df[f"{TARGET_COLUMN}_mean_{label}"] = (
        df[TARGET_COLUMN]
        .rolling(window=window, min_periods=3)
        .mean()
    )

    df[f"{TARGET_COLUMN}_std_{label}"] = (
        df[TARGET_COLUMN]
        .rolling(window=window, min_periods=3)
        .std()
    )

# =========================
# BANDERAS OPERACIONALES BÁSICAS
# =========================

# Estas banderas son preliminares y se pueden ajustar luego con criterio RF.
df["low_snr_flag"] = (df["dl_snr_db"] < 18).astype(int)
df["low_mcs_flag"] = (df["dl_mcs"] < df["dl_mcs"].quantile(0.25)).astype(int)
df["low_rate_flag"] = (df["dl_rate_mbps"] < df["dl_rate_mbps"].quantile(0.25)).astype(int)

for label, window in WINDOWS.items():
    df[f"low_snr_persistence_{label}"] = (
        df["low_snr_flag"]
        .rolling(window=window, min_periods=3)
        .mean()
    )

    df[f"low_mcs_persistence_{label}"] = (
        df["low_mcs_flag"]
        .rolling(window=window, min_periods=3)
        .mean()
    )

    # Esta variable es solo de validación, no debe entrar al IDOE.
    df[f"low_rate_persistence_{label}"] = (
        df["low_rate_flag"]
        .rolling(window=window, min_periods=3)
        .mean()
    )

# =========================
# LIMPIEZA FINAL
# =========================
df = df.reset_index()

# Mantener filas aunque tengan NaN en primeras ventanas.
# El siguiente script podrá decidir si las elimina.
df.to_csv(OUTPUT_DATASET, index=False)

# =========================
# LOG
# =========================
log_lines.append("")
log_lines.append("COLUMNAS GENERADAS")
log_lines.append("==================")
log_lines.extend(list(df.columns))

log_lines.append("")
log_lines.append(f"Filas exportadas: {len(df)}")
log_lines.append(f"Archivo generado: {OUTPUT_DATASET}")

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print("\n=================================")
print("FEATURES TEMPORALES GENERADAS")
print("=================================")
print(f"Archivo: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print(f"Filas exportadas: {len(df)}")
print(f"Columnas finales: {len(df.columns)}")