"""
Project 001 - Manufacturing Performance Dashboard
ETL Pipeline: Raw CSV -> Clean CSV -> SQLite

Requirements:
    pandas
    numpy

Run:
    python etl_manufacturing.py

Expected input folder:
    project_001_manufacturing_performance/

The script validates the raw tables, creates derived KPI fields,
writes clean CSV files, creates a clean SQLite database, and
generates ETL validation reports.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "project_001_manufacturing_performance"
OUT = ROOT / "project_001_ETL"
OUT.mkdir(exist_ok=True)

TABLES = [
    "dim_date",
    "dim_machine",
    "dim_product",
    "dim_shift",
    "dim_downtime",
    "fact_production",
    "fact_downtime",
    "fact_maintenance",
]


def load_raw_data():
    if not BASE.exists():
        raise FileNotFoundError(
            f"Raw data folder not found: {BASE}\n"
            "Create a folder named project_001_manufacturing_performance "
            "next to this script and place the 8 raw CSV files inside it."
        )

    missing = [
        name for name in TABLES
        if not (BASE / f"{name}.csv").exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing raw CSV files: " + ", ".join(missing) +
            f"\nExpected folder: {BASE}"
        )

    return {
        name: pd.read_csv(BASE / f"{name}.csv")
        for name in TABLES
    }


def standardize_data(raw):
    clean = {}

    for name, df in raw.items():
        df = df.copy()

        for col in ["Date", "Install_Date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        clean[name] = df

    production = clean["fact_production"]

    for col in [
        "Planned_Time_Min",
        "Run_Time_Min",
        "Total_Units",
        "Good_Units",
        "Scrap_Units",
        "Ideal_Cycle_Time_Sec",
    ]:
        production[col] = pd.to_numeric(production[col], errors="coerce")

    downtime = clean["fact_downtime"]
    downtime["Downtime_Min"] = pd.to_numeric(
        downtime["Downtime_Min"], errors="coerce"
    )

    maintenance = clean["fact_maintenance"]

    for col in ["Repair_Time_Min", "Downtime_Min"]:
        maintenance[col] = pd.to_numeric(
            maintenance[col], errors="coerce"
        )

    return clean


def create_kpi_fields(clean):
    p = clean["fact_production"]

    p["Scrap_Rate"] = np.where(
        p["Total_Units"] > 0,
        p["Scrap_Units"] / p["Total_Units"],
        0,
    )

    p["Availability"] = np.where(
        p["Planned_Time_Min"] > 0,
        p["Run_Time_Min"] / p["Planned_Time_Min"],
        0,
    )

    p["Performance"] = np.where(
        p["Run_Time_Min"] > 0,
        (
            p["Ideal_Cycle_Time_Sec"] * p["Total_Units"]
        ) / (p["Run_Time_Min"] * 60),
        0,
    )

    p["Quality"] = np.where(
        p["Total_Units"] > 0,
        p["Good_Units"] / p["Total_Units"],
        0,
    )

    p["OEE"] = (
        p["Availability"]
        * p["Performance"]
        * p["Quality"]
    )

    clean["fact_production"] = p
    return clean


def validate(clean):
    results = []

    def add(name, issue_count, detail):
        results.append({
            "Check": name,
            "Status": "PASS" if issue_count == 0 else "FAIL",
            "Issue_Count": int(issue_count),
            "Detail": detail,
        })

    p = clean["fact_production"]
    dt = clean["fact_downtime"]
    m = clean["fact_maintenance"]

    add(
        "Critical nulls - production",
        int(
            p[
                [
                    "Date",
                    "Shift_ID",
                    "Machine_ID",
                    "Product_ID",
                    "Planned_Time_Min",
                    "Run_Time_Min",
                    "Total_Units",
                    "Good_Units",
                    "Scrap_Units",
                ]
            ].isna().any(axis=1).sum()
        ),
        "Critical production fields populated",
    )

    add(
        "Critical nulls - downtime",
        int(
            dt[
                ["Date", "Shift_ID", "Machine_ID", "Downtime_Min"]
            ].isna().any(axis=1).sum()
        ),
        "Critical downtime fields populated",
    )

    add(
        "Critical nulls - maintenance",
        int(
            m[
                [
                    "Date",
                    "Machine_ID",
                    "Maintenance_Type",
                    "Repair_Time_Min",
                    "Downtime_Min",
                ]
            ].isna().any(axis=1).sum()
        ),
        "Critical maintenance fields populated",
    )

    add(
        "Good + Scrap = Total",
        int(
            (
                p["Good_Units"] + p["Scrap_Units"]
                != p["Total_Units"]
            ).sum()
        ),
        "Production unit reconciliation",
    )

    add(
        "Run time <= planned time",
        int(
            (p["Run_Time_Min"] > p["Planned_Time_Min"]).sum()
        ),
        "Operating time cannot exceed planned time",
    )

    for metric, low, high in [
        ("Availability", 0, 1),
        ("Quality", 0, 1),
        ("Scrap_Rate", 0, 1),
        ("OEE", 0, 1.1),
    ]:
        add(
            f"{metric} range",
            int(
                (
                    (p[metric] < low)
                    | (p[metric] > high)
                ).sum()
            ),
            f"Expected range {low}-{high}",
        )

    machines = set(clean["dim_machine"]["Machine_ID"])
    products = set(clean["dim_product"]["Product_ID"])
    shifts = set(clean["dim_shift"]["Shift_ID"])

    add(
        "Production -> Machine",
        int((~p["Machine_ID"].isin(machines)).sum()),
        "Referential integrity",
    )

    add(
        "Production -> Product",
        int((~p["Product_ID"].isin(products)).sum()),
        "Referential integrity",
    )

    add(
        "Production -> Shift",
        int((~p["Shift_ID"].isin(shifts)).sum()),
        "Referential integrity",
    )

    add(
        "Downtime -> Machine",
        int((~dt["Machine_ID"].isin(machines)).sum()),
        "Referential integrity",
    )

    daily_dt = (
        dt.groupby(
            ["Date", "Shift_ID", "Machine_ID"],
            as_index=False,
        )["Downtime_Min"]
        .sum()
    )

    add(
        "Downtime <= 240 min per machine/shift/day",
        int((daily_dt["Downtime_Min"] > 240).sum()),
        "Validation threshold",
    )

    for name, df in clean.items():
        add(
            f"Duplicate rows - {name}",
            int(df.duplicated().sum()),
            "No duplicate rows expected",
        )

    return pd.DataFrame(results)


def save_outputs(clean, validation):
    for name, df in clean.items():
        df.to_csv(
            OUT / f"{name}_clean.csv",
            index=False,
        )

    db_path = OUT / "manufacturing_performance_clean.db"

    with sqlite3.connect(db_path) as conn:
        for name, df in clean.items():
            load = df.copy()

            for col in load.columns:
                if pd.api.types.is_datetime64_any_dtype(
                    load[col]
                ):
                    load[col] = load[col].dt.strftime(
                        "%Y-%m-%d"
                    )

            load.to_sql(
                name,
                conn,
                if_exists="replace",
                index=False,
            )

        validation.to_sql(
            "etl_validation",
            conn,
            if_exists="replace",
            index=False,
        )

    validation.to_csv(
        OUT / "ETL_Validation_Detail.csv",
        index=False,
    )

    status = (
        "PASS"
        if not (validation["Status"] == "FAIL").any()
        else "FAIL"
    )

    report = f"""# Project 001 - ETL Validation Report

ETL Status: **{status}**

Process:
Extract -> Standardize -> Validate -> Transform -> Load

Checks:
- Critical nulls
- Duplicate rows
- Production reconciliation
- Run time vs planned time
- KPI ranges
- Referential integrity
- Downtime validation

The dataset is synthetic and intended for portfolio/case-study purposes.
"""

    (OUT / "ETL_Validation_Report.md").write_text(
        report,
        encoding="utf-8",
    )

    return db_path, status


def main():
    print("Project 001 ETL started...")

    raw = load_raw_data()
    clean = standardize_data(raw)
    clean = create_kpi_fields(clean)
    validation = validate(clean)

    db_path, status = save_outputs(
        clean,
        validation,
    )

    print(f"ETL STATUS: {status}")
    print(f"Clean SQLite: {db_path}")
    print(f"Output folder: {OUT.resolve()}")


if __name__ == "__main__":
    main()
