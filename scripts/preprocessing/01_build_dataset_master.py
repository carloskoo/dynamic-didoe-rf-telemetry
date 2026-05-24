import pandas as pd
from glob import glob
import os
import re

# ============================================================
# 01_build_dataset_master.py
# Construye el dataset maestro desde archivos CSV diarios ePMP
# ============================================================

# =========================
# CONFIGURACIÓN
# =========================
BASE_DIR = r"C:\registros"

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_master.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "dataset_master_log.txt")

# =========================
# FUNCIONES AUXILIARES
# =========================

def parse_rate_to_mbps(value):
    """
    Convierte tasas como '137M', '154M', '1.2G', '800K' a Mbps.
    """
    if pd.isna(value):
        return None

    text = str(value).strip().upper()

    if text in ["", "NAN", "NONE", "-", "--"]:
        return None

    match = re.match(r"([0-9.]+)\s*([KMG]?)", text)

    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2)

    if unit == "G":
        return number * 1000
    elif unit == "K":
        return number / 1000
    else:
        return number


def to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


# =========================
# BUSCAR CSV
# =========================
files = glob(os.path.join(BASE_DIR, "*.csv"))

files = [
    f for f in files
    if not os.path.basename(f).lower().startswith("dataset_")
]

if not files:
    print("No se encontraron archivos CSV.")
    raise SystemExit(1)

dfs = []
log_lines = []

print(f"Archivos CSV encontrados: {len(files)}")

# =========================
# PROCESAMIENTO
# =========================
for f in files:
    filename = os.path.basename(f)

    try:
        df_raw = pd.read_csv(f)
        columns = list(df_raw.columns)

        # =========================
        # FORMATO AGG / LIMPIO
        # =========================
        if "dl_mcs" in columns and "dl_snr_db" in columns:
            df = df_raw.copy()

            if "role" in columns:
                df = df[df["role"].astype(str).str.upper() == "AP"].copy()

            needed_cols = [
                "ts",
                "dl_mcs",
                "ul_mcs",
                "dl_snr_db",
                "ul_snr_db",
                "dl_rssi_dbm",
                "ul_rssi_dbm",
                "dl_rate",
                "note"
            ]

            df = df[[c for c in needed_cols if c in df.columns]].copy()
            source_type = "AGG"

        # =========================
        # FORMATO LOCAL / CRUDO
        # =========================
        elif "mcs_dl" in columns and "snr_dl" in columns:
            df = pd.DataFrame()

            df["ts"] = df_raw["ts"] if "ts" in columns else None
            df["dl_mcs"] = df_raw["mcs_dl"] if "mcs_dl" in columns else None
            df["ul_mcs"] = df_raw["mcs_ul"] if "mcs_ul" in columns else None
            df["dl_snr_db"] = df_raw["snr_dl"] if "snr_dl" in columns else None
            df["ul_snr_db"] = df_raw["snr_ul"] if "snr_ul" in columns else None
            df["dl_rssi_dbm"] = df_raw["sta_dl_rssi"] if "sta_dl_rssi" in columns else None
            df["ul_rssi_dbm"] = df_raw["sta_ul_rssi"] if "sta_ul_rssi" in columns else None
            df["dl_rate"] = df_raw["dl_rate"] if "dl_rate" in columns else None
            df["note"] = "converted_from_local"

            source_type = "LOCAL"

        else:
            log_lines.append(f"{filename} -> OMITIDO: formato no reconocido: {columns}")
            continue

        rows_before = len(df)

        # =========================
        # NORMALIZACIÓN DE CAMPOS
        # =========================
        df["timestamp"] = pd.to_datetime(df["ts"], errors="coerce")

        df["dl_mcs"] = to_numeric(df["dl_mcs"])
        df["ul_mcs"] = to_numeric(df["ul_mcs"]) if "ul_mcs" in df.columns else None

        df["dl_snr_db"] = to_numeric(df["dl_snr_db"])
        df["ul_snr_db"] = to_numeric(df["ul_snr_db"]) if "ul_snr_db" in df.columns else None

        df["dl_rssi_dbm"] = to_numeric(df["dl_rssi_dbm"])
        df["ul_rssi_dbm"] = to_numeric(df["ul_rssi_dbm"]) if "ul_rssi_dbm" in df.columns else None

        df["dl_rate_raw"] = df["dl_rate"].astype(str).str.strip()
        df["dl_rate_mbps"] = df["dl_rate_raw"].apply(parse_rate_to_mbps)

        df["source_file"] = filename
        df["source_type"] = source_type

        if "note" not in df.columns:
            df["note"] = ""

        # =========================
        # MARCA DE VALIDEZ
        # =========================
        df["valid_record"] = True

        required = [
            "timestamp",
            "dl_mcs",
            "dl_snr_db",
            "dl_rssi_dbm",
            "dl_rate_mbps"
        ]

        for col in required:
            df.loc[df[col].isna(), "valid_record"] = False

        # Valores anómalos típicos de pérdida/captura errónea
        df.loc[df["dl_snr_db"] <= 0, "valid_record"] = False
        df.loc[df["dl_rssi_dbm"] >= 0, "valid_record"] = False
        df.loc[df["dl_rate_mbps"] <= 0, "valid_record"] = False

        # Mantener solo columnas finales
        final_cols = [
            "timestamp",
            "dl_mcs",
            "ul_mcs",
            "dl_snr_db",
            "ul_snr_db",
            "dl_rssi_dbm",
            "ul_rssi_dbm",
            "dl_rate_raw",
            "dl_rate_mbps",
            "valid_record",
            "note",
            "source_file",
            "source_type"
        ]

        df = df[[c for c in final_cols if c in df.columns]].copy()

        rows_after = len(df)
        valid_count = int(df["valid_record"].sum())
        invalid_count = rows_after - valid_count

        dfs.append(df)

        log_lines.append(
            f"{filename} ({source_type}) -> OK: "
            f"{rows_before} filas | válidas: {valid_count} | inválidas: {invalid_count}"
        )

    except Exception as e:
        log_lines.append(f"{filename} -> ERROR: {e}")

# =========================
# CONSOLIDACIÓN
# =========================
if not dfs:
    print("No se pudo construir el dataset maestro.")
    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    raise SystemExit(1)

dataset = pd.concat(dfs, ignore_index=True)

rows_before_sort = len(dataset)

dataset = dataset.sort_values("timestamp")

rows_before_dedup = len(dataset)
dataset = dataset.drop_duplicates(
    subset=["timestamp", "dl_mcs", "dl_snr_db", "dl_rssi_dbm", "dl_rate_mbps"],
    keep="first"
)
rows_after_dedup = len(dataset)

# =========================
# ANÁLISIS DE GAPS
# =========================
dataset_valid = dataset[dataset["valid_record"]].copy()
dataset_valid = dataset_valid.sort_values("timestamp")
dataset_valid["delta_seconds"] = dataset_valid["timestamp"].diff().dt.total_seconds()

expected_interval = 60
gap_threshold = expected_interval * 3

num_gaps = int((dataset_valid["delta_seconds"] > gap_threshold).sum())
max_gap = dataset_valid["delta_seconds"].max()

# =========================
# EXPORTACIÓN
# =========================
dataset.to_csv(OUTPUT_DATASET, index=False)

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("RESUMEN DEL DATASET MAESTRO\n")
    f.write("===========================\n\n")
    f.write(f"Archivos procesados: {len(files)}\n")
    f.write(f"Filas antes de consolidar: {rows_before_sort}\n")
    f.write(f"Filas antes de deduplicar: {rows_before_dedup}\n")
    f.write(f"Filas finales: {rows_after_dedup}\n")
    f.write(f"Registros válidos: {int(dataset['valid_record'].sum())}\n")
    f.write(f"Registros inválidos: {int((~dataset['valid_record']).sum())}\n")
    f.write(f"Gaps mayores a {gap_threshold} segundos: {num_gaps}\n")
    f.write(f"Gap máximo detectado (segundos): {max_gap}\n\n")

    f.write("DETALLE POR ARCHIVO\n")
    f.write("===================\n")
    f.write("\n".join(log_lines))

print("\n=================================")
print("DATASET MAESTRO GENERADO")
print("=================================")
print(f"Archivo: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print(f"Filas finales: {rows_after_dedup}")
print(f"Registros válidos: {int(dataset['valid_record'].sum())}")
print(f"Registros inválidos: {int((~dataset['valid_record']).sum())}")
print(f"Gaps detectados: {num_gaps}")