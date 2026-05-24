#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine
import os

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_predictivo.csv"
DB_URL="postgresql://carlos:1234@localhost:5432/epmp_noc"

if not os.path.exists(FILE):
    print("No existe dataset_predictivo.csv")
    exit()

df=pd.read_csv(FILE)
engine=create_engine(DB_URL)
df.to_sql("metricas_predictivas", engine, if_exists="replace", index=False)

print("Datos predictivos insertados en PostgreSQL")
