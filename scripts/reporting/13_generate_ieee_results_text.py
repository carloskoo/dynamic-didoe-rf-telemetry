import pandas as pd
import os

BASE_DIR = r"C:\registros"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TABLES_DIR = os.path.join(OUTPUT_DIR, "tables")

OUTPUT_TEXT = os.path.join(OUTPUT_DIR, "ieee_results_text_draft.txt")

tables = {
    "dataset": os.path.join(TABLES_DIR, "table_01_dataset_summary.csv"),
    "models": os.path.join(TABLES_DIR, "table_02_model_comparison.csv"),
    "thresholds": os.path.join(TABLES_DIR, "table_03_threshold_optimization.csv"),
    "validation": os.path.join(TABLES_DIR, "table_04_validation_metrics.csv"),
    "op_thresholds": os.path.join(TABLES_DIR, "table_05_operational_reference_thresholds.csv"),
    "states": os.path.join(TABLES_DIR, "table_06_state_distribution.csv"),
    "importance": os.path.join(TABLES_DIR, "table_07_top_feature_importance.csv"),
    "components": os.path.join(TABLES_DIR, "table_08_composite_reference_components.csv"),
}

def load_table(key):
    path = tables[key]
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

dataset = load_table("dataset")
models = load_table("models")
thresholds = load_table("thresholds")
validation = load_table("validation")
op_thresholds = load_table("op_thresholds")
states = load_table("states")
importance = load_table("importance")
components = load_table("components")

def get_value(df, metric):
    row = df[df["Metric"] == metric]
    if row.empty:
        return "N/A"
    return row.iloc[0]["Value"]

with open(OUTPUT_TEXT, "w", encoding="utf-8") as f:

    f.write("IEEE RESULTS AND DISCUSSION DRAFT\n")
    f.write("=================================\n\n")

    f.write("A. Dataset Characterization\n")
    f.write("---------------------------\n")

    if dataset is not None:
        f.write(
            f"The proposed methodology was evaluated using a longitudinal RF telemetry dataset composed of "
            f"{get_value(dataset, 'Processed CSV files')} daily CSV files. After consolidation and preprocessing, "
            f"the final dataset contained {get_value(dataset, 'Final rows')} records, of which "
            f"{get_value(dataset, 'Valid records')} were considered valid for analysis. "
            f"A total of {get_value(dataset, 'Invalid records')} records were marked as invalid due to missing, corrupted, "
            f"or physically inconsistent values. The preprocessing stage also identified "
            f"{get_value(dataset, 'Temporal gaps > 180 s')} temporal gaps greater than 180 seconds, reflecting real-world "
            f"operational discontinuities in the monitoring process.\n\n"
        )

    f.write("B. Dynamic IDOE Model Comparison\n")
    f.write("--------------------------------\n")

    if models is not None:
        for _, row in models.iterrows():
            f.write(
                f"The {row['Model']} model achieved a correlation of "
                f"{row['Correlation with Throughput']:.4f} with downlink throughput. "
                f"This model is described as: {row['Description']}.\n"
            )

        f.write(
            "\nThe results show that incorporating temporal features improves the operational representation "
            "of the radio link compared with an instantaneous RF-only index. In particular, D-IDOE V2 achieved "
            "the highest correlation with throughput among the evaluated indices, despite not using throughput "
            "as an input variable.\n\n"
        )

    f.write("C. Threshold Optimization\n")
    f.write("-------------------------\n")

    if thresholds is not None:
        f.write(
            "The operational classification stage was evaluated using percentile-based and optimized thresholding strategies. "
            "The optimized strategy achieved the highest F1-score, indicating that fixed conventional thresholds are not "
            "sufficient to characterize the operational states of a real wireless link with concentrated score distributions.\n\n"
        )

        f.write(thresholds.to_string(index=False))
        f.write("\n\n")

    f.write("D. Validation Against Operational Reference\n")
    f.write("-------------------------------------------\n")

    if validation is not None:
        f.write(
            "The optimized D-IDOE was validated against two reference criteria: a throughput-only reference and an adaptive "
            "composite operational reference. The composite reference integrates 15-minute mean throughput, MCS, SNR, and "
            "temporal stability indicators, providing a more realistic representation of the operational state of the link.\n\n"
        )

        f.write(validation.to_string(index=False))
        f.write("\n\n")

        f.write(
            "The results indicate that the optimized D-IDOE provides a more meaningful characterization when evaluated against "
            "a multivariable operational reference than when compared only with instantaneous throughput. This supports the "
            "hypothesis that radio link degradation is better represented through a combined RF-temporal model rather than "
            "through a single performance metric.\n\n"
        )

    f.write("E. Feature Importance Analysis\n")
    f.write("------------------------------\n")

    if importance is not None:
        top = importance.head(5)

        f.write(
            "The ML-based feature importance analysis showed that the most relevant variables were associated with MCS and "
            "its temporal behavior. This result suggests that adaptive modulation dynamics provide a stronger operational "
            "descriptor of the radio link than isolated RSSI or SNR values.\n\n"
        )

        f.write(top.to_string(index=False))
        f.write("\n\n")

        f.write(
            "This finding is relevant because it demonstrates that the operational behavior of the monitored radio link is "
            "strongly governed by modulation adaptation and temporal stability, rather than by received signal power alone.\n\n"
        )

    f.write("F. Composite Operational Reference\n")
    f.write("----------------------------------\n")

    if components is not None:
        f.write(
            "To avoid relying exclusively on throughput as a ground-truth indicator, a composite operational reference was "
            "defined using multiple RF and temporal indicators. The reference combines sustained throughput, MCS, SNR, "
            "MCS stability, SNR stability, and inverse volatility components.\n\n"
        )

        f.write(components.to_string(index=False))
        f.write("\n\n")

    f.write("G. Interpretation of Operational States\n")
    f.write("---------------------------------------\n")

    if states is not None:
        f.write(
            "The comparison between the adaptive composite reference and the optimized D-IDOE shows that the proposed index "
            "is able to capture a relevant portion of the operational structure of the radio link. Although some confusion "
            "remains between adjacent states, such as Degraded and Stable, this behavior is expected in real RF systems "
            "where operational degradation evolves continuously rather than as sharply separated classes.\n\n"
        )

        f.write(states.to_string(index=False))
        f.write("\n\n")

    f.write("H. Scientific Interpretation\n")
    f.write("----------------------------\n")

    f.write(
        "Overall, the results demonstrate that single-metric evaluation is insufficient to characterize the operational "
        "condition of long-term rural radio links. The weak direct association between D-IDOE and instantaneous throughput "
        "does not invalidate the proposed index; instead, it reveals that throughput alone is an incomplete representation "
        "of link health. By integrating RF quality, MCS dynamics, temporal stability, and adaptive thresholding, the proposed "
        "framework provides a more robust operational characterization of the radio link under real-world conditions.\n\n"
    )

    f.write(
        "The proposed framework should therefore be interpreted as an operational state characterization method rather than "
        "a pure throughput prediction model. This distinction is important because the objective is not to estimate the exact "
        "data rate at each instant, but to identify and classify the operational condition of the radio link using longitudinal "
        "RF telemetry.\n"
    )

print("\n=================================")
print("IEEE RESULTS TEXT GENERATED")
print("=================================")
print(f"File: {OUTPUT_TEXT}")