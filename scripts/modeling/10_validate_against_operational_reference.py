import pandas as pd
import os

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ============================================================
# 10_validate_against_operational_reference.py
# Validation of optimized D-IDOE against adaptive operational reference
# ============================================================

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

INPUT_DATASET = os.path.join(
    OUTPUT_DIR,
    "dataset_operational_reference_adaptive.csv"
)

OUTPUT_LOG = os.path.join(
    OUTPUT_DIR,
    "validate_operational_reference_log.txt"
)

OUTPUT_CM = os.path.join(
    OUTPUT_DIR,
    "confusion_matrix_operational_reference.csv"
)

# Referencia operacional compuesta
REFERENCE_COL = "state_operational_reference_adaptive"

# Predicción D-IDOE calibrada
PREDICTION_COL = "state_optimized_thresholds"


# ============================================================
# LOAD DATA
# ============================================================

if not os.path.exists(INPUT_DATASET):
    print(f"No existe: {INPUT_DATASET}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_DATASET, low_memory=False)

required_cols = [
    REFERENCE_COL,
    PREDICTION_COL
]

missing = [c for c in required_cols if c not in df.columns]

if missing:
    print("Faltan columnas:")
    for c in missing:
        print(" -", c)
    raise SystemExit(1)

df_eval = df.dropna(subset=required_cols).copy()

df_eval = df_eval[
    (df_eval[REFERENCE_COL] != "Undefined") &
    (df_eval[PREDICTION_COL] != "Undefined")
].copy()

# ============================================================
# TRUE VS PREDICTED
# ============================================================

y_true = df_eval[REFERENCE_COL].astype(str)
y_pred = df_eval[PREDICTION_COL].astype(str)

# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(y_true, y_pred)

precision = precision_score(
    y_true,
    y_pred,
    average="weighted",
    zero_division=0
)

recall = recall_score(
    y_true,
    y_pred,
    average="weighted",
    zero_division=0
)

f1 = f1_score(
    y_true,
    y_pred,
    average="weighted",
    zero_division=0
)

report = classification_report(
    y_true,
    y_pred,
    zero_division=0
)

labels = sorted(
    list(
        set(y_true.unique()).union(
            set(y_pred.unique())
        )
    )
)

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=labels
)

# ============================================================
# EXPORT CONFUSION MATRIX
# ============================================================

cm_df = pd.DataFrame(
    cm,
    index=[f"TRUE_{x}" for x in labels],
    columns=[f"PRED_{x}" for x in labels]
)

cm_df.to_csv(OUTPUT_CM)

# ============================================================
# DISTRIBUTIONS
# ============================================================

true_dist = y_true.value_counts(normalize=True) * 100
pred_dist = y_pred.value_counts(normalize=True) * 100

true_count = y_true.value_counts()
pred_count = y_pred.value_counts()

# ============================================================
# EXPORT LOG
# ============================================================

with open(OUTPUT_LOG, "w", encoding="utf-8") as f:

    f.write("VALIDATION AGAINST ADAPTIVE OPERATIONAL REFERENCE\n")
    f.write("=================================================\n\n")

    f.write(f"Input dataset: {INPUT_DATASET}\n")
    f.write(f"Reference column: {REFERENCE_COL}\n")
    f.write(f"Prediction column: {PREDICTION_COL}\n")
    f.write(f"Rows evaluated: {len(df_eval)}\n\n")

    f.write("GLOBAL METRICS\n")
    f.write("==============\n")
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Precision: {precision:.4f}\n")
    f.write(f"Recall: {recall:.4f}\n")
    f.write(f"F1-score: {f1:.4f}\n\n")

    f.write("REFERENCE DISTRIBUTION\n")
    f.write("======================\n")
    for state in true_count.index:
        f.write(
            f"{state}: {true_count[state]} "
            f"({true_dist[state]:.2f}%)\n"
        )

    f.write("\n")

    f.write("OPTIMIZED D-IDOE DISTRIBUTION\n")
    f.write("=============================\n")
    for state in pred_count.index:
        f.write(
            f"{state}: {pred_count[state]} "
            f"({pred_dist[state]:.2f}%)\n"
        )

    f.write("\n")

    f.write("CLASSIFICATION REPORT\n")
    f.write("=====================\n")
    f.write(report)
    f.write("\n")

    f.write("LABELS\n")
    f.write("======\n")
    f.write(str(labels))
    f.write("\n\n")

    f.write("CONFUSION MATRIX\n")
    f.write("================\n")
    f.write(str(cm))
    f.write("\n")


print("\n=================================")
print("VALIDATION COMPLETED")
print("=================================")

print(f"Log: {OUTPUT_LOG}")
print(f"Confusion Matrix: {OUTPUT_CM}")

print("\nGLOBAL METRICS")
print("==============")

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-score: {f1:.4f}")

print("\nRows evaluated:", len(df_eval))