#!/usr/bin/env python3
import os
import glob
import re
import pandas as pd
import numpy as np

BASE="/home/carlos/epmp_monitor"
DATA=f"{BASE}/data"
OUT=f"{BASE}/reportes"
os.makedirs(OUT, exist_ok=True)

COLS=[
    "ts","role","ip","peer_ip",
    "dl_mcs","ul_mcs",
    "dl_snr_db","ul_snr_db",
    "dl_rssi_dbm","ul_rssi_dbm",
    "dl_rate","note"
]

files=sorted(glob.glob(f"{DATA}/agg_ap_*.csv"))

if not files:
    print("No hay CSV agg_ap_*.csv")
    raise SystemExit(0)

frames=[]

for f in files:
    print("Leyendo:", os.path.basename(f))
    rows=[]
    with open(f, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line=line.strip()
            if not line:
                continue
            if line.startswith("ts,role,"):
                continue

            parts=line.split(",")

            if len(parts) < 12:
                # Línea incompleta: empty_show_sta / parse_failed
                continue

            if len(parts) > 12:
                parts=parts[:12]

            rows.append(parts)

    if rows:
        df=pd.DataFrame(rows, columns=COLS)
        df["source_file"]=os.path.basename(f)
        frames.append(df)

if not frames:
    print("No hay filas válidas")
    raise SystemExit(0)

df=pd.concat(frames, ignore_index=True)

df["ts"]=pd.to_datetime(df["ts"], errors="coerce")

def clean_num(x):
    if pd.isna(x):
        return np.nan
    s=str(x).strip()
    s=s.replace("Mbps","").replace("mbps","")
    s=s.replace("M","").replace("m","")
    s=s.replace("dBm","").replace("dbm","")
    s=s.replace("dB","").replace("db","")
    m=re.search(r"-?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else np.nan

for c in ["dl_mcs","ul_mcs","dl_snr_db","ul_snr_db","dl_rssi_dbm","ul_rssi_dbm","dl_rate"]:
    df[c]=df[c].apply(clean_num)

# Si algún AP entrega 0 en DL pero sí valor en UL, usamos el valor útil.
df["snr_real_db"]=df["dl_snr_db"]
df.loc[(df["snr_real_db"].isna()) | (df["snr_real_db"] == 0), "snr_real_db"] = df["ul_snr_db"]

df["rssi_real_dbm"]=df["dl_rssi_dbm"]
df.loc[(df["rssi_real_dbm"].isna()) | (df["rssi_real_dbm"] == 0), "rssi_real_dbm"] = df["ul_rssi_dbm"]

# Normalizar RSSI si viene positivo por algún firmware.
df.loc[df["rssi_real_dbm"] > 0, "rssi_real_dbm"] = -1 * df.loc[df["rssi_real_dbm"] > 0, "rssi_real_dbm"]

# Compatibilidad con dashboard/scripts existentes.
df["dl_snr_db"]=df["snr_real_db"]
df["dl_rssi_dbm"]=df["rssi_real_dbm"]

df=df.dropna(subset=["ts"])
df=df[df[["dl_snr_db","dl_rssi_dbm","dl_rate"]].notna().any(axis=1)]
df=df.sort_values("ts").reset_index(drop=True)

if df.empty:
    print("No hay datos útiles")
    raise SystemExit(0)

df["dl_snr_db"]=df["dl_snr_db"].interpolate(limit_direction="both")
df["dl_rssi_dbm"]=df["dl_rssi_dbm"].interpolate(limit_direction="both")
df["dl_rate"]=df["dl_rate"].interpolate(limit_direction="both")

df["snr_diff"]=df["dl_snr_db"].diff()
df["rssi_diff"]=df["dl_rssi_dbm"].diff()
df["rate_diff"]=df["dl_rate"].diff()
df["snr_avg"]=df["dl_snr_db"].rolling(5, min_periods=1).mean()
df["rate_avg"]=df["dl_rate"].rolling(5, min_periods=1).mean()
df["snr_std"]=df["dl_snr_db"].rolling(10, min_periods=2).std().fillna(0)

def evento(row):
    if row["dl_snr_db"] < 12:
        return "CRITICO_SNR"
    if row["dl_rssi_dbm"] < -85:
        return "CRITICO_RSSI"
    if row["dl_rate"] < 10:
        return "CAIDA_RATE"
    if pd.notna(row["snr_diff"]) and abs(row["snr_diff"]) > 5:
        return "INTERFERENCIA"
    if pd.notna(row["snr_std"]) and row["snr_std"] > 4:
        return "INESTABLE"
    return "NORMAL"

df["evento"]=df.apply(evento, axis=1)

df["riesgo"]=0
df.loc[df["snr_avg"] < 15, "riesgo"] += 2
df.loc[df["rate_avg"] < 20, "riesgo"] += 2
df.loc[df["snr_std"] > 3, "riesgo"] += 1
df.loc[df["dl_rssi_dbm"] < -85, "riesgo"] += 1

df["riesgo_nivel"]=pd.cut(
    df["riesgo"],
    bins=[-1,1,3,99],
    labels=["BAJO","MEDIO","ALTO"]
)

out=f"{OUT}/dataset_avanzado.csv"
df.to_csv(out, index=False)

print("MODELO AVANZADO OK:", out)
print("Filas útiles:", len(df))
print(df[["ts","dl_snr_db","ul_snr_db","dl_rssi_dbm","ul_rssi_dbm","dl_rate","evento","riesgo_nivel"]].tail(10))
