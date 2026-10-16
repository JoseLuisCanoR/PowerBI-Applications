"""
Project 001 - KPI Engine
Reads the clean ETL outputs and creates:
OEE, Availability, Performance, Quality, MTBF, MTTR,
Downtime, Scrap and improvement-priority analyses.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3

ROOT = Path(__file__).resolve().parent
ETL_DIR = ROOT / "project_001_ETL"
OUT = ROOT / "project_001_KPI"
OUT.mkdir(exist_ok=True)


def weighted_oee(df):
    planned = df["Planned_Time_Min"].sum()
    run = df["Run_Time_Min"].sum()
    total = df["Total_Units"].sum()
    good = df["Good_Units"].sum()

    ideal_time = (
        df["Ideal_Cycle_Time_Sec"]
        * df["Total_Units"]
    ).sum() / 60

    availability = run / planned if planned else 0
    performance = ideal_time / run if run else 0
    quality = good / total if total else 0

    return pd.Series({
        "Planned_Time_Min": planned,
        "Run_Time_Min": run,
        "Total_Units": total,
        "Good_Units": good,
        "Scrap_Units": df["Scrap_Units"].sum(),
        "Downtime_Min": planned - run,
        "Availability": availability,
        "Performance": performance,
        "Quality": quality,
        "OEE": availability * performance * quality,
    })


def main():
    p = pd.read_csv(
        ETL_DIR / "fact_production_clean.csv",
        parse_dates=["Date"],
    )

    dt = pd.read_csv(
        ETL_DIR / "fact_downtime_clean.csv",
        parse_dates=["Date"],
    )

    m = pd.read_csv(
        ETL_DIR / "fact_maintenance_clean.csv",
        parse_dates=["Date"],
    )

    machines = pd.read_csv(
        ETL_DIR / "dim_machine_clean.csv"
    )

    plant_kpi = weighted_oee(p).to_frame().T

    by_machine = (
        p.groupby("Machine_ID")
        .apply(weighted_oee, include_groups=False)
        .reset_index()
    )

    by_machine = by_machine.merge(
        machines[
            [
                "Machine_ID",
                "Machine_Name",
                "Line_ID",
                "Process",
                "Criticality",
            ]
        ],
        on="Machine_ID",
        how="left",
    )

    by_shift = (
        p.groupby("Shift_ID")
        .apply(weighted_oee, include_groups=False)
        .reset_index()
    )

    by_line = (
        p.merge(
            machines[["Machine_ID", "Line_ID"]],
            on="Machine_ID",
            how="left",
        )
        .groupby("Line_ID")
        .apply(weighted_oee, include_groups=False)
        .reset_index()
    )

    by_product = (
        p.groupby("Product_ID")
        .apply(weighted_oee, include_groups=False)
        .reset_index()
    )

    by_month = (
        p.assign(
            Month=p["Date"].dt.to_period("M").astype(str)
        )
        .groupby("Month")
        .apply(weighted_oee, include_groups=False)
        .reset_index()
    )

    downtime_by_category = (
        dt.groupby(
            "Downtime_Category",
            as_index=False,
        )["Downtime_Min"]
        .sum()
        .sort_values(
            "Downtime_Min",
            ascending=False,
        )
    )

    failure_events = dt[
        ~dt["Downtime_Category"].isin(
            ["Changeover", "Planned Maintenance"]
        )
    ]

    failure_count = (
        failure_events.groupby("Machine_ID")
        .size()
        .rename("Failure_Count")
    )

    operating_time = (
        p.groupby("Machine_ID")["Run_Time_Min"]
        .sum()
        .rename("Operating_Time_Min")
    )

    corrective = m[
        m["Maintenance_Type"] == "Corrective"
    ]

    repair_time = (
        corrective.groupby("Machine_ID")["Repair_Time_Min"]
        .sum()
        .rename("Repair_Time_Min")
    )

    repair_count = (
        corrective.groupby("Machine_ID")
        .size()
        .rename("Repair_Count")
    )

    reliability = pd.concat(
        [
            operating_time,
            failure_count,
            repair_time,
            repair_count,
        ],
        axis=1,
    ).fillna(0).reset_index()

    reliability["MTBF_Min"] = np.where(
        reliability["Failure_Count"] > 0,
        reliability["Operating_Time_Min"]
        / reliability["Failure_Count"],
        np.nan,
    )

    reliability["MTTR_Min"] = np.where(
        reliability["Repair_Count"] > 0,
        reliability["Repair_Time_Min"]
        / reliability["Repair_Count"],
        np.nan,
    )

    reliability = reliability.merge(
        machines[
            [
                "Machine_ID",
                "Machine_Name",
                "Line_ID",
                "Criticality",
            ]
        ],
        on="Machine_ID",
        how="left",
    )

    outputs = {
        "plant_kpi": plant_kpi,
        "kpi_by_machine": by_machine,
        "kpi_by_shift": by_shift,
        "kpi_by_line": by_line,
        "kpi_by_product": by_product,
        "kpi_by_month": by_month,
        "downtime_by_category": downtime_by_category,
        "reliability_by_machine": reliability,
    }

    for name, df in outputs.items():
        df.to_csv(
            OUT / f"{name}.csv",
            index=False,
        )

    db = OUT / "manufacturing_kpi_engine.db"

    with sqlite3.connect(db) as conn:
        for name, df in outputs.items():
            df.to_sql(
                name,
                conn,
                if_exists="replace",
                index=False,
            )

    print("KPI Engine completed.")
    print(f"SQLite: {db}")


if __name__ == "__main__":
    main()
