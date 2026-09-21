# OIL SIF Precursor Detection — Data Quality Report (Part 1A)

## Executive Summary
This report details the data profiling, quality checks, and normalization actions performed on the Excel dataset `Indian_Refinery_Near_Miss_Datasets.xlsx` for Oil India Limited (OIL).

- **Workbook Filename**: `Indian_Refinery_Near_Miss_Datasets.xlsx`
- **Total Sheets**: `13`
- **Total Raw Observation Records**: `950`
- **Total Processed Records**: `950`
- **Target Column**: `High_Potential_Near_Miss` (Binary: 0 = Non-SIF, 1 = SIF)
- **Class Distribution**: Non-SIF = 850 (89.47%), SIF = 100 (10.53%)
- **Imbalance Ratio**: 8.5:1

---

## Sheet Breakdown

| Sheet Name | Rows | Columns | High Potential Records |
| :--- | :--- | :--- | :--- |
| `01_PPE_NonCompliance` | 75 | 18 | 0 |
| `01_Supervisor_Negligence` | 75 | 18 | 0 |
| `01_Maintenance_Delay_or_Issue` | 75 | 18 | 0 |
| `01_Repeated_Issue_Ignored` | 75 | 18 | 0 |
| `05_2Factor_1` | 75 | 18 | 0 |
| `05_2Factor_2` | 75 | 18 | 0 |
| `05_2Factor_3` | 75 | 18 | 0 |
| `08_3Factor_1` | 75 | 18 | 0 |
| `08_3Factor_2` | 75 | 18 | 0 |
| `08_3Factor_3` | 75 | 18 | 0 |
| `11_4Factor_All` | 100 | 18 | 0 |
| `12_High_Potential` | 100 | 18 | 100 |


---

## Missing Data & Quality Issues Summary

- **Missing Descriptions**: 0
- **Null Values Across Key Fields**: None
- **Exact Duplicate Rows (excl source_sheet)**: 0
- **Unique Near_Miss_ID Count**: 650
- **Unique Near_Miss_Description Count**: 609

---

## Cleaning & Normalization Actions

1. **Column Standardisation**: Standardised all column names to snake_case whitespace-trimmed strings.
2. **Text Preservation**: Preserved case and safety-critical negation terms (`not`, `no`, `without`, `bypassed`, `failed`, `ignored`, `never`, `unable`, `unlocked`) in `Near_Miss_Description`.
3. **Categorical Normalisation**: Cleaned leading/trailing spaces for `Refinery_Unit`, `Equipment_ID`, `Work_Type`, `Department`, `Immediate_Cause`, `Potential_Consequence`, `Risk_Level`, `Corrective_Action`, `Action_Status`.
4. **Boolean Normalisation**: Converted boolean flags (`PPE_NonCompliance`, `Supervisor_Negligence`, `Maintenance_Delay_or_Issue`, `Repeated_Issue_Ignored`) to standard `True`/`False`.
5. **Target Encoding**: Converted `High_Potential_Near_Miss` to binary integers `0` (Non-SIF) and `1` (SIF).
6. **Audit Column Isolation**: Retained `source_sheet` strictly as an audit metadata column.
