# Python Environment Setup

## 1. Overview

This document explains how to configure and run the Python
scripts associated with the Manufacturing Performance Analytics
project.

## 2. Prerequisites

Install the following software:

- Python 3.10 or later
- Visual Studio Code (optional)
- Git (optional)

## 3. Project Structure

```text
Project_001_Python_Scripts_PowerBI/
├── etl_manufacturing.py
├── kpi_engine.py
├── create_clean_excel.py
├── PYTHON_SETUP.md
├── README.md
├── Project_001_Manufacturing_Clean.xlsx
├── Project_001_Manufacturing_Performance_Dashboard.pbix
├── project_001_manufacturing_performance/
│   ├── dim_date.csv
│   ├── dim_downtime.csv
│   ├── dim_machine.csv
│   ├── dim_product.csv
│   ├── dim_shift.csv
│   ├── fact_downtime.csv
│   ├── fact_maintenance.csv
│   └── fact_production.csv
├── project_001_ETL/
└── project_001_KPI/
```
4. Install Dependencies

Open a terminal in the project directory and execute:

python -m pip install pandas openpyxl

If additional libraries are required, install them according
to the Python import statements in the scripts.

5. Run the ETL Process

Execute:

python etl_manufacturing.py

This process prepares and validates manufacturing datasets.

6. Generate Manufacturing KPIs

After the ETL process finishes, execute:

python kpi_engine.py

The scripts generate output files for manufacturing
performance and reliability analysis.

7. Generated Outputs
ETL Outputs
Cleaned datasets
SQLite database
ETL validation report
KPI Outputs
Plant-level KPIs
Machine-level performance
Reliability indicators
Monthly and shift-level KPIs
Downtime analysis
8. Troubleshooting

If Python is not recognized, verify that Python is installed
and available in the system PATH.

If a module is missing, install the required dependency
using pip.

Author

Jose Luis Cano Romero

Manufacturing Operations | Maintenance & Reliability |
Operational Excellence | Data Analytics
