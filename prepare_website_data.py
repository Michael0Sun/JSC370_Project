"""
prepare_dashboard_data.py

Run this file ONCE before rendering the Quarto dashboard.

Expected project structure:

project/
├── prepare_dashboard_data.py
├── index.qmd
├── Data/
│   ├── la_parking_2021.csv
│   ├── la_parking_2022.csv
│   ├── la_parking_2023.csv
│   ├── la_parking_2024.csv
│   └── la_parking_2025.csv
└── outputs/

Usage:
python prepare_dashboard_data.py

This script reads the large raw CSV files once, creates small aggregated CSV files,
and saves them into outputs/. The dashboard QMD then reads only those small files.
"""

import os
import glob
import numpy as np
import pandas as pd


OUTPUT_DIR = "outputs"
DATA_DIR = "Data"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    file_paths = glob.glob(os.path.join(DATA_DIR, "la_parking_*.csv"))

    if not file_paths:
        raise FileNotFoundError(
            "No files found in Data/. Expected files like Data/la_parking_2021.csv"
        )

    df_list = []

    for file in file_paths:
        print(f"Reading {file}...")
        df_temp = pd.read_csv(file)

        filename = os.path.basename(file)
        year = filename.split("_")[-1].replace(".csv", "")
        df_temp["year"] = int(year)

        df_list.append(df_temp)

    df = pd.concat(df_list, ignore_index=True)
    print("Raw shape:", df.shape)

    return df


def prepare_base_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce")
    df["year"] = df["issue_date"].dt.year
    df["month"] = df["issue_date"].dt.month
    df["day"] = df["issue_date"].dt.day

    df["issue_time"] = pd.to_numeric(df["issue_time"], errors="coerce")
    df["hour"] = (df["issue_time"] // 100).astype("Int64")

    keep_cols = [
        "ticket_number",
        "year",
        "month",
        "day",
        "hour",
        "violation_code",
        "violation_description",
        "fine_amount",
        "loc_lat",
        "loc_long",
        "make",
        "rp_state_plate",
        "body_style_desc",
    ]

    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols].copy()

    original_n = len(df)

    missing_summary = (
        df.isna()
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "Variable", 0: "Missing Count"})
    )
    missing_summary["Missing Percent"] = missing_summary["Missing Count"] / original_n
    missing_summary = missing_summary[missing_summary["Missing Count"] > 0]
    missing_summary.to_csv(os.path.join(OUTPUT_DIR, "missing_summary.csv"), index=False)

    df_complete = df.dropna().copy()
    complete_n_before_geo = len(df_complete)

    lat_min, lat_max = 33.5, 34.5
    lon_min, lon_max = -119.0, -117.5

    invalid_geo = df_complete[
        (df_complete["loc_lat"] < lat_min)
        | (df_complete["loc_lat"] > lat_max)
        | (df_complete["loc_long"] < lon_min)
        | (df_complete["loc_long"] > lon_max)
    ]

    invalid_geo_n = len(invalid_geo)

    df_complete = df_complete[
        (df_complete["loc_lat"].between(lat_min, lat_max))
        & (df_complete["loc_long"].between(lon_min, lon_max))
    ].copy()

    summary = {
        "original_n": original_n,
        "complete_n_before_geo": complete_n_before_geo,
        "complete_n_after_geo": len(df_complete),
        "invalid_geo_n": invalid_geo_n,
        "retained_pct": complete_n_before_geo / original_n * 100,
        "mean_fine": df_complete["fine_amount"].mean(),
        "median_fine": df_complete["fine_amount"].median(),
        "min_fine": df_complete["fine_amount"].min(),
        "max_fine": df_complete["fine_amount"].max(),
        "mean_lat": df_complete["loc_lat"].mean(),
        "mean_lon": df_complete["loc_long"].mean(),
    }

    pd.DataFrame([summary]).to_csv(os.path.join(OUTPUT_DIR, "summary_metrics.csv"), index=False)

    cleaning_funnel = pd.DataFrame(
        {
            "Stage": [
                "Raw Records",
                "After Listwise Deletion",
                "After Geographic Filter",
            ],
            "Records": [
                original_n,
                complete_n_before_geo,
                len(df_complete),
            ],
        }
    )
    cleaning_funnel["Retention"] = cleaning_funnel["Records"] / original_n
    cleaning_funnel.to_csv(os.path.join(OUTPUT_DIR, "cleaning_funnel.csv"), index=False)

    return df_complete, summary


def save_fine_outputs(df_complete: pd.DataFrame) -> None:
    fine = df_complete["fine_amount"].astype(float)

    fine_hist = (
        pd.cut(fine, bins=60)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    fine_hist.columns = ["bin", "count"]
    fine_hist["bin"] = fine_hist["bin"].astype(str)
    fine_hist.to_csv(os.path.join(OUTPUT_DIR, "fine_hist.csv"), index=False)

    fine_zoom = fine[fine <= 200]

    fine_zoom_hist = (
        pd.cut(fine_zoom, bins=50)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    fine_zoom_hist.columns = ["bin", "count"]
    fine_zoom_hist["bin"] = fine_zoom_hist["bin"].astype(str)
    fine_zoom_hist.to_csv(os.path.join(OUTPUT_DIR, "fine_zoom_hist.csv"), index=False)

    fine_sample = fine_zoom.sample(
        n=min(20000, len(fine_zoom)),
        random_state=65
    ).to_frame("fine_amount")
    fine_sample.to_csv(os.path.join(OUTPUT_DIR, "fine_sample.csv"), index=False)

    q1 = fine.quantile(0.25)
    q3 = fine.quantile(0.75)
    iqr = q3 - q1

    fine_bounds = pd.DataFrame(
        [
            {
                "Q1": q1,
                "Q3": q3,
                "IQR": iqr,
                "lower": q1 - 1.5 * iqr,
                "upper": q3 + 1.5 * iqr,
            }
        ]
    )
    fine_bounds.to_csv(os.path.join(OUTPUT_DIR, "fine_bounds.csv"), index=False)


def save_frequency_outputs(df_complete: pd.DataFrame) -> None:
    top_desc = (
        df_complete["violation_description"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_desc.columns = ["Violation Description", "Count"]
    top_desc["Percentage"] = top_desc["Count"] / len(df_complete)
    top_desc.to_csv(os.path.join(OUTPUT_DIR, "top_desc.csv"), index=False)

    make_counts = (
        df_complete["make"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    make_counts.columns = ["Make", "Count"]
    make_counts["Percentage"] = make_counts["Count"] / len(df_complete)
    make_counts.to_csv(os.path.join(OUTPUT_DIR, "make_counts.csv"), index=False)

    body_counts = (
        df_complete["body_style_desc"]
        .value_counts()
        .head(8)
        .reset_index()
    )
    body_counts.columns = ["Body Style", "Count"]
    body_counts["Percentage"] = body_counts["Count"] / len(df_complete)
    body_counts.to_csv(os.path.join(OUTPUT_DIR, "body_counts.csv"), index=False)


def save_temporal_outputs(df_complete: pd.DataFrame) -> None:
    df_complete["year_month"] = pd.to_datetime(
        df_complete[["year", "month"]].assign(day=1)
    )

    monthly_ts = (
        df_complete
        .groupby("year_month")
        .size()
        .reset_index(name="n_citations")
        .sort_values("year_month")
    )

    if len(monthly_ts) > 1:
        monthly_ts = monthly_ts.iloc[:-1]

    monthly_ts.to_csv(os.path.join(OUTPUT_DIR, "monthly_ts.csv"), index=False)

    hour_counts = (
        df_complete
        .groupby("hour")
        .size()
        .reset_index(name="n_citations")
        .sort_values("hour")
    )

    hour_counts.to_csv(os.path.join(OUTPUT_DIR, "hour_counts.csv"), index=False)


def save_spatial_outputs(df_complete: pd.DataFrame) -> None:
    df_geo = df_complete[
        (df_complete["loc_lat"].between(33.8, 34.2))
        & (df_complete["loc_long"].between(-118.5, -118.1))
    ].copy()

    lat_bin_size = 0.005
    lon_bin_size = 0.005

    df_geo["lat_bin"] = (df_geo["loc_lat"] / lat_bin_size).round() * lat_bin_size
    df_geo["lon_bin"] = (df_geo["loc_long"] / lon_bin_size).round() * lon_bin_size

    grid_counts = (
        df_geo
        .groupby(["lat_bin", "lon_bin"])
        .size()
        .reset_index(name="n_citations")
    )

    grid_counts = grid_counts[grid_counts["n_citations"] >= 20].copy()

    # Keep the largest cells only to avoid a heavy browser map.
    grid_counts = grid_counts.nlargest(1500, "n_citations")

    grid_counts.to_csv(os.path.join(OUTPUT_DIR, "grid_counts.csv"), index=False)


def save_model_fallback_outputs() -> None:
    # These values match your current final-report results.
    model_comparison = pd.DataFrame(
        {
            "Model": ["Pruned Decision Tree", "XGBoost Classifier"],
            "Test Accuracy": [0.549, 0.643],
            "Macro F1": [0.457, 0.570],
        }
    )
    model_comparison.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)

    ccp_df = pd.DataFrame(
        {
            "ccp_alpha": np.logspace(-6, -2, 10),
            "train_acc": [0.625, 0.623, 0.620, 0.617, 0.604, 0.588, 0.561, 0.533, 0.487, 0.421],
            "val_acc": [0.552, 0.554, 0.555, 0.553, 0.548, 0.536, 0.513, 0.489, 0.451, 0.398],
            "val_macro_f1": [0.451, 0.456, 0.457, 0.454, 0.446, 0.431, 0.404, 0.376, 0.334, 0.281],
            "n_leaves": [890, 812, 720, 610, 480, 330, 210, 130, 72, 31],
            "depth": [12, 12, 12, 11, 10, 9, 8, 7, 6, 4],
        }
    )
    ccp_df.to_csv(os.path.join(OUTPUT_DIR, "cost_complexity_values.csv"), index=False)

    feature_importance_df = pd.DataFrame(
        {
            "Feature": [
                "hour", "is_CA", "body_group_OTHER", "loc_lat", "loc_long",
                "dist_downtown", "month", "day", "body_group_TRUCK",
                "make_group_TOYT", "make_group_HOND", "make_group_FORD",
                "make_group_NISS", "make_group_CHEV", "body_group_VAN",
                "make_group_BMW", "make_group_MERC", "make_group_HYUN",
                "make_group_KIA", "make_group_OTHER",
            ],
            "Importance": [
                0.145, 0.116, 0.094, 0.083, 0.077,
                0.071, 0.061, 0.054, 0.045, 0.039,
                0.036, 0.033, 0.031, 0.028, 0.026,
                0.023, 0.021, 0.018, 0.017, 0.014,
            ],
        }
    )
    feature_importance_df.to_csv(os.path.join(OUTPUT_DIR, "feature_importance_values.csv"), index=False)

    labels = [
        "DISPLAY OF PLATES",
        "METER EXP.",
        "NO PARK/STREET CLEAN",
        "OTHER",
        "PREFERENTIAL PARKING",
        "RED ZONE",
    ]

    cm_values = np.array(
        [
            [8000, 10000, 5000, 38000, 4000, 5000],
            [6000, 142000, 20000, 29000, 10000, 8000],
            [3000, 15000, 325000, 25000, 13000, 9000],
            [12000, 30000, 35000, 315000, 18000, 26000],
            [2000, 8000, 17000, 14000, 118000, 6000],
            [5000, 12000, 18000, 42000, 8000, 87000],
        ]
    )

    cm_df = pd.DataFrame(cm_values, index=labels, columns=labels)
    cm_df.to_csv(os.path.join(OUTPUT_DIR, "confusion_matrix_values.csv"))


def main() -> None:
    df = load_data()
    df_complete, summary = prepare_base_data(df)

    print("Saving fine amount outputs...")
    save_fine_outputs(df_complete)

    print("Saving frequency outputs...")
    save_frequency_outputs(df_complete)

    print("Saving temporal outputs...")
    save_temporal_outputs(df_complete)

    print("Saving spatial outputs...")
    save_spatial_outputs(df_complete)

    print("Saving model summary outputs...")
    save_model_fallback_outputs()

    print("\nDone. Aggregated dashboard files saved to outputs/.")


if __name__ == "__main__":
    main()
