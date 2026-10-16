# Project 001 - Python Scripts v2

This version is designed for VS Code, PowerShell and CMD.

## Folder structure

Keep the folders like this:

Project_001/
  etl_manufacturing.py
  kpi_engine.py
  project_001_manufacturing_performance/
    dim_date.csv
    dim_machine.csv
    dim_product.csv
    dim_shift.csv
    dim_downtime.csv
    fact_production.csv
    fact_downtime.csv
    fact_maintenance.csv

The scripts automatically use the folder where the script is located
as the project root. Your PowerShell current directory does not matter.

## Run

python etl_manufacturing.py

Then:

python kpi_engine.py

## Outputs

project_001_ETL/
  *_clean.csv
  manufacturing_performance_clean.db
  ETL_Validation_Detail.csv
  ETL_Validation_Report.md

project_001_KPI/
  plant_kpi.csv
  kpi_by_machine.csv
  reliability_by_machine.csv
  kpi_by_month.csv
  kpi_by_shift.csv
  kpi_by_line.csv
  kpi_by_product.csv
  downtime_by_category.csv
  manufacturing_kpi_engine.db
