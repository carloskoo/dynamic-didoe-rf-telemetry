import pandas as pd
import numpy as np
import os

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ============================================================
# 04_ml_validation.py
# Validación ML del Dynamic IDOE
# ============================================================

# =========================
# CONFIGURACIÓN
# =========================
BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(OUTPUT_DIR, "dataset_dynamic_idoe.csv")

OUTPUT_LOG = os.path.join(OUTPUT_DIR, "ml_validation_log.txt")
OUTPUT_IMPORTANCE = os.path.join(OUTPUT_DIR, "ml_feature_importance.csv")
OUTPUT_PREDICTIONS = os.path.join(OUTPUT_DIR, "dataset_ml_predictions.csv")

TEST_SIZE = 0.30
RANDOM_STATE = 42

# =========================
# CARGA DE DATOS
# =========================
if not os.path.exists(INPUT_DATASET):
    print(f"No existe el archivo: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# =========================
# VARIABLES DE ENTRADA
# =========================
feature_cols = [
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs",

    "snr_norm",
    "rssi_norm",
    "mcs_norm",

    "idoe_base",
    "rf_quality_score",
    "temporal_stability_score",
    "d_idoe",

    "snr_stability_score",
    "rssi_stability_score",
    "mcs_stability_score",
    "mcs_volatility_score",
    "snr_trend_score",
    "mcs_trend_score",

    "dl_snr_db_std_15m",
    "dl_rssi_dbm_std_15m",
    "dl_mcs_std_15m",
    "dl_snr_db_slope_15m",
    "dl_mcs_slope_15m",
    "mcs_stability_15m"
]

target_regression = "dl_rate_mbps"
target_classification = "state_rate_reference"

missing = [c for c in feature_cols + [target_regression, target_classification] if c not in df.columns]

if missing:
    print("Faltan columnas:")
    for c in missing:
        print(" -", c)
    raise SystemExit(1)

# Convertir features a numéricas
for col in feature_cols + [target_regression]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=feature_cols + [target_regression, target_classification])

# Quitar estados indefinidos
df = df[df[target_classification] != "Undefined"].copy()

# =========================
# SPLIT TEMPORAL
# =========================
n = len(df)
split_index = int(n * (1 - TEST_SIZE))

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

X_train = train[feature_cols]
X_test = test[feature_cols]

y_train_reg = train[target_regression]
y_test_reg = test[target_regression]

y_train_cls = train[target_classification]
y_test_cls = test[target_classification]

# =========================
# MODELO DE REGRESIÓN
# =========================
reg_model = RandomForestRegressor(
    n_estimators=300,
    max_depth=None,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=RANDOM_STATE,
    n_jobs=-1
)

reg_model.fit(X_train, y_train_reg)
y_pred_reg = reg_model.predict(X_test)

r2 = r2_score(y_test_reg, y_pred_reg)
mae = mean_absolute_error(y_test_reg, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))

# =========================
# MODELO DE CLASIFICACIÓN
# =========================
cls_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1
)

cls_model.fit(X_train, y_train_cls)
y_pred_cls = cls_model.predict(X_test)

accuracy = accuracy_score(y_test_cls, y_pred_cls)
precision = precision_score(y_test_cls, y_pred_cls, average="weighted", zero_division=0)
recall = recall_score(y_test_cls, y_pred_cls, average="weighted", zero_division=0)
f1 = f1_score(y_test_cls, y_pred_cls, average="weighted", zero_division=0)

report = classification_report(y_test_cls, y_pred_cls, zero_division=0)
cm = confusion_matrix(y_test_cls, y_pred_cls, labels=cls_model.classes_)

# =========================
# IMPORTANCIA DE VARIABLES
# =========================
importance_reg = pd.DataFrame({
    "feature": feature_cols,
    "importance_regression": reg_model.feature_importances_
})

importance_cls = pd.DataFrame({
    "feature": feature_cols,
    "importance_classification": cls_model.feature_importances_
})

importance = importance_reg.merge(importance_cls, on="feature")
importance["importance_mean"] = (
    importance["importance_regression"] + importance["importance_classification"]
) / 2

importance = importance.sort_values("importance_mean", ascending=False)
importance.to_csv(OUTPUT_IMPORTANCE, index=False)

# =========================
# PREDICCIONES
# =========================
predictions = test[[
    "timestamp",
    "dl_snr_db",
    "dl_rssi_dbm",
    "dl_mcs",
    "dl_rate_mbps",
    "idoe_base",
    "d_idoe",
    "state_d_idoe",
    "state_rate_reference"
]].copy()

predictions["predicted_dl_rate_mbps"] = y_pred_reg
predictions["predicted_state"] = y_pred_cls
predictions["absolute_error_mbps"] = (
    predictions["dl_rate_mbps"] - predictions["predicted_dl_rate_mbps"]
).abs()

predictions.to_csv(OUTPUT_PREDICTIONS, index=False)

# =========================
# LOG
# =========================
with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
    f.write("VALIDACIÓN ML DEL DYNAMIC IDOE\n")
    f.write("==============================\n\n")

    f.write(f"Archivo de entrada: {INPUT_DATASET}\n")
    f.write(f"Registros totales usados: {len(df)}\n")
    f.write(f"Entrenamiento: {len(train)} registros\n")
    f.write(f"Prueba temporal: {len(test)} registros\n\n")

    f.write("PERIODO DE ENTRENAMIENTO\n")
    f.write("========================\n")
    f.write(f"{train['timestamp'].min()} -> {train['timestamp'].max()}\n\n")

    f.write("PERIODO DE PRUEBA\n")
    f.write("=================\n")
    f.write(f"{test['timestamp'].min()} -> {test['timestamp'].max()}\n\n")

    f.write("REGRESIÓN: PREDICCIÓN DE DL RATE\n")
    f.write("================================\n")
    f.write(f"R2: {r2:.4f}\n")
    f.write(f"MAE: {mae:.4f} Mbps\n")
    f.write(f"RMSE: {rmse:.4f} Mbps\n\n")

    f.write("CLASIFICACIÓN: ESTADO OPERACIONAL\n")
    f.write("=================================\n")
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision weighted: {precision:.4f}\n")
    f.write(f"Recall weighted: {recall:.4f}\n")
    f.write(f"F1-score weighted: {f1:.4f}\n\n")

    f.write("CLASES DEL MODELO\n")
    f.write("=================\n")
    f.write(str(list(cls_model.classes_)))
    f.write("\n\n")

    f.write("REPORTE DE CLASIFICACIÓN\n")
    f.write("========================\n")
    f.write(report)
    f.write("\n")

    f.write("MATRIZ DE CONFUSIÓN\n")
    f.write("===================\n")
    f.write("Labels: " + str(list(cls_model.classes_)) + "\n")
    f.write(str(cm))
    f.write("\n\n")

    f.write("TOP 15 VARIABLES MÁS IMPORTANTES\n")
    f.write("================================\n")
    f.write(importance.head(15).to_string(index=False))

print("\n=================================")
print("VALIDACIÓN ML COMPLETADA")
print("=================================")
print(f"Log: {OUTPUT_LOG}")
print(f"Importancia de variables: {OUTPUT_IMPORTANCE}")
print(f"Predicciones: {OUTPUT_PREDICTIONS}")
print("\nRegresión:")
print(f"R2: {r2:.4f}")
print(f"MAE: {mae:.4f} Mbps")
print(f"RMSE: {rmse:.4f} Mbps")
print("\nClasificación:")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-score: {f1:.4f}")