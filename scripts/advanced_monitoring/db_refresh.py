#!/usr/bin/env python3
import os
import pandas as pd
from sqlalchemy import create_engine

BASE="/home/carlos/epmp_monitor"
DB_URL="postgresql://carlos:1234@localhost:5432/epmp_noc"
engine=create_engine(DB_URL)

RF=f"{BASE}/reportes/dataset_avanzado.csv"
PRED=f"{BASE}/reportes/dataset_predictivo.csv"
OPER=f"{BASE}/reportes/dataset_operador.csv"

if os.path.exists(RF):
    df=pd.read_csv(RF)
    df["ts"]=pd.to_datetime(df["ts"], errors="coerce")

    for c in ["dl_snr_db","dl_rate","dl_rssi_dbm","ul_rssi_dbm"]:
        if c in df.columns:
            df[c]=pd.to_numeric(df[c], errors="coerce")

    df.to_sql("metricas_rf", engine, if_exists="replace", index=False)
    print("OK DB metricas_rf:", len(df))

if os.path.exists(PRED):
    df=pd.read_csv(PRED)
    df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
    df.to_sql("metricas_predictivas", engine, if_exists="replace", index=False)
    print("OK DB metricas_predictivas:", len(df))

if os.path.exists(OPER):
    df=pd.read_csv(OPER)
    df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
    df.to_sql("metricas_operador", engine, if_exists="replace", index=False)
    print("OK DB metricas_operador:", len(df))
