import pandas as pd
import numpy as np
import os

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe_v2.csv")
OUTPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe_v2_thresholds.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "threshold_optimization_log.txt")

SCORE_COL = "d_idoe_v2"
REFERENCE_COL = "state_rate_reference"


def classify_custom(score, t1, t2, t3):
    if pd.isna(score):
        return "Undefined"
    if score < t1:
        return "Critical"
    if score < t2:
        return "Degraded"
    if score < t3:
        return "Stable"
    return "Optimal"


def metrics(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }


df = pd.read_csv(INPUT_DATASET, low_memory=False)

df[SCORE_COL] = pd.to_numeric(df[SCORE_COL], errors="coerce")
df["dl_rate_mbps"] = pd.to_numeric(df["dl_rate_mbps"], errors="coerce")

df_eval = df.dropna(subset=[SCORE_COL, REFERENCE_COL, "dl_rate_mbps"]).copy()
df_eval = df_eval[df_eval[REFERENCE_COL] != "Undefined"].copy()

y_true = df_eval[REFERENCE_COL].astype(str)

# Percentiles base
q25 = df_eval[SCORE_COL].quantile(0.25)
q50 = df_eval[SCORE_COL].quantile(0.50)
q75 = df_eval[SCORE_COL].quantile(0.75)

df_eval["state_percentile_thresholds"] = df_eval[SCORE_COL].apply(
    lambda x: classify_custom(x, q25, q50, q75)
)

metrics_percentile = metrics(y_true, df_eval["state_percentile_thresholds"])

# Búsqueda rápida con combinaciones pequeñas
percentile_sets = [
    (0.10, 0.40, 0.75),
    (0.15, 0.45, 0.80),
    (0.20, 0.50, 0.85),
    (0.25, 0.50, 0.75),
    (0.30, 0.60, 0.90),
    (0.35, 0.65, 0.90),
]

best = {"f1": -1}

for p1, p2, p3 in percentile_sets:
    t1 = df_eval[SCORE_COL].quantile(p1)
    t2 = df_eval[SCORE_COL].quantile(p2)
    t3 = df_eval[SCORE_COL].quantile(p3)

    y_pred = df_eval[SCORE_COL].apply(lambda x: classify_custom(x, t1, t2, t3))
    m = metrics(y_true, y_pred)

    if m["f1"] > best["f1"]:
        best = {
            "p": (p1, p2, p3),
            "t": (t1, t2, t3),
            "metrics": m,
            "f1": m["f1"],
            "y_pred": y_pred
        }

df_eval["state_optimized_thresholds"] = best["y_pred"]

# Unir al dataset original por índice
df_out = df.copy()
df_out["state_percentile_thresholds"] = np.nan
df_out["state_optimized_thresholds"] = np.nan

df_out.loc[df_eval.index, "state_percentile_thresholds"] = df_eval["state_percentile_thresholds"]
df_out.loc[df_eval.index, "state_optimized_thresholds"] = df_eval["state_optimized_thresholds"]

df_out.to_csv(OUTPUT_DATASET, index=False)

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("OPTIMIZACIÓN RÁPIDA DE UMBRALES D-IDOE V2\n")
    f.write("========================================\n\n")

    f.write(f"Registros evaluados: {len(df_eval)}\n\n")

    f.write("PERCENTILES BASE\n")
    f.write("================\n")
    f.write(f"q25={q25:.4f}, q50={q50:.4f}, q75={q75:.4f}\n")
    f.write(str(metrics_percentile))
    f.write("\n\n")

    f.write("MEJOR CONFIGURACIÓN\n")
    f.write("===================\n")
    f.write(f"Percentiles: {best['p']}\n")
    f.write(f"Umbrales: t1={best['t'][0]:.4f}, t2={best['t'][1]:.4f}, t3={best['t'][2]:.4f}\n")
    f.write(str(best["metrics"]))
    f.write("\n\n")

    f.write("DISTRIBUCIÓN OPTIMIZADA\n")
    f.write("=======================\n")
    f.write(str(df_eval["state_optimized_thresholds"].value_counts()))
    f.write("\n\n")

    f.write("REPORTE DE CLASIFICACIÓN OPTIMIZADA\n")
    f.write("===================================\n")
    f.write(classification_report(y_true, df_eval["state_optimized_thresholds"], zero_division=0))

print("\n=================================")
print("OPTIMIZACIÓN RÁPIDA COMPLETADA")
print("=================================")
print(f"Archivo: {OUTPUT_DATASET}")
print(f"Log: {OUTPUT_LOG}")
print(f"F1 percentil base: {metrics_percentile['f1']:.4f}")
print(f"F1 optimizado: {best['metrics']['f1']:.4f}")
print(f"Mejores percentiles: {best['p']}")
print(f"Umbrales: {best['t']}")