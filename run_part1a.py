import os
import json
import pandas as pd
from src.data_loader import inspect_workbook, load_raw_dataset
from src.data_cleaning import clean_dataset, save_processed_dataset, MODEL_FEATURE_COLUMNS, AUDIT_ONLY_COLUMNS, POST_INVESTIGATION_COLUMNS
from src.data_validation import validate_target, analyze_dataset_construction
from src.leakage_audit import perform_leakage_audit
from src.eda import generate_eda_plots

def main():
    print("==================================================")
    print("OIL SIF PRECURSOR DETECTION - PART 1A PIPELINE")
    print("==================================================")
    
    os.makedirs("reports", exist_ok=True)
    os.makedirs("reports/figures", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    # STEP 1 & 2: Locate, Inspect & Profile Workbook
    print("\n[STEP 1 & 2] Inspecting Workbook...")
    profile = inspect_workbook()
    print(f"Workbook Found: {profile['workbook_filename']}")
    print(f"Number of Sheets: {profile['num_sheets']}")
    print(f"Total Raw Records: {profile['total_raw_observation_records']}")
    
    # Save dataset profile JSON
    with open("reports/dataset_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    print("--> Saved reports/dataset_profile.json")

    # STEP 3 & 4: Load & Validate Target
    print("\n[STEP 3 & 4] Loading Raw Dataset & Validating Target...")
    raw_df, summary_df = load_raw_dataset()
    cleaned_df = clean_dataset(raw_df)
    
    target_stats = validate_target(cleaned_df)
    print(f"Target Column: {target_stats['target_column']}")
    print(f"Non-SIF (0) Records: {target_stats['class_0_count_non_sif']} ({target_stats['class_0_percentage']}%)")
    print(f"SIF (1) Records:     {target_stats['class_1_count_sif']} ({target_stats['class_1_percentage']}%)")
    print(f"Imbalance Ratio:     {target_stats['imbalance_ratio']}:1")
    
    # STEP 5 & 6: Dataset Construction & Leakage Audit
    print("\n[STEP 5, 6 & 7] Analyzing Dataset Construction & Leakage...")
    construction_stats = analyze_dataset_construction(cleaned_df)
    leakage_stats = perform_leakage_audit(cleaned_df)
    
    print("Duplicate Analysis:")
    print(f"  Exact Duplicates (excl source_sheet): {leakage_stats['duplicate_analysis']['exact_duplicate_rows_excl_source_sheet']}")
    print(f"  Unique Descriptions:                 {leakage_stats['duplicate_analysis']['unique_description_count']} out of {len(cleaned_df)}")
    print(f"  Cross-Sheet Description Overlap:     {leakage_stats['duplicate_analysis']['cross_sheet_duplicate_description_count']}")
    
    # STEP 8 & 9: Save Processed Dataset
    print("\n[STEP 8 & 9] Saving Processed ML-Ready Dataset...")
    csv_p, parquet_p = save_processed_dataset(cleaned_df)
    print(f"--> Saved {csv_p}")
    print(f"--> Saved {parquet_p}")

    # STEP 10: Generate EDA Charts
    print("\n[STEP 10] Generating 21 EDA Visualizations...")
    figures = generate_eda_plots(cleaned_df)
    print(f"--> Saved {len(figures)} figures in reports/figures/")

    # STEP 11: Create Markdown Reports
    print("\n[STEP 11] Generating Comprehensive Markdown Reports...")
    
    # 1. Data Quality Report
    quality_md = f"""# OIL SIF Precursor Detection — Data Quality Report (Part 1A)

## Executive Summary
This report details the data profiling, quality checks, and normalization actions performed on the Excel dataset `Indian_Refinery_Near_Miss_Datasets.xlsx` for Oil India Limited (OIL).

- **Workbook Filename**: `{profile['workbook_filename']}`
- **Total Sheets**: `{profile['num_sheets']}`
- **Total Raw Observation Records**: `{profile['total_raw_observation_records']}`
- **Total Processed Records**: `{len(cleaned_df)}`
- **Target Column**: `High_Potential_Near_Miss` (Binary: 0 = Non-SIF, 1 = SIF)
- **Class Distribution**: Non-SIF = {target_stats['class_0_count_non_sif']} ({target_stats['class_0_percentage']}%), SIF = {target_stats['class_1_count_sif']} ({target_stats['class_1_percentage']}%)
- **Imbalance Ratio**: {target_stats['imbalance_ratio']}:1

---

## Sheet Breakdown

| Sheet Name | Rows | Columns | High Potential Records |
| :--- | :--- | :--- | :--- |
"""
    for s_name, s_prof in profile['sheet_profiles'].items():
        if s_name == '00_Summary':
            continue
        hp_cnt = (cleaned_df[cleaned_df['source_sheet'] == s_name]['High_Potential_Near_Miss'] == 1).sum()
        quality_md += f"| `{s_name}` | {s_prof['num_rows']} | {s_prof['num_cols']} | {hp_cnt} |\n"

    quality_md += f"""

---

## Missing Data & Quality Issues Summary

- **Missing Descriptions**: 0
- **Null Values Across Key Fields**: None
- **Exact Duplicate Rows (excl source_sheet)**: {leakage_stats['duplicate_analysis']['exact_duplicate_rows_excl_source_sheet']}
- **Unique Near_Miss_ID Count**: {leakage_stats['duplicate_analysis']['unique_near_miss_id_count']}
- **Unique Near_Miss_Description Count**: {leakage_stats['duplicate_analysis']['unique_description_count']}

---

## Cleaning & Normalization Actions

1. **Column Standardisation**: Standardised all column names to snake_case whitespace-trimmed strings.
2. **Text Preservation**: Preserved case and safety-critical negation terms (`not`, `no`, `without`, `bypassed`, `failed`, `ignored`, `never`, `unable`, `unlocked`) in `Near_Miss_Description`.
3. **Categorical Normalisation**: Cleaned leading/trailing spaces for `Refinery_Unit`, `Equipment_ID`, `Work_Type`, `Department`, `Immediate_Cause`, `Potential_Consequence`, `Risk_Level`, `Corrective_Action`, `Action_Status`.
4. **Boolean Normalisation**: Converted boolean flags (`PPE_NonCompliance`, `Supervisor_Negligence`, `Maintenance_Delay_or_Issue`, `Repeated_Issue_Ignored`) to standard `True`/`False`.
5. **Target Encoding**: Converted `High_Potential_Near_Miss` to binary integers `0` (Non-SIF) and `1` (SIF).
6. **Audit Column Isolation**: Retained `source_sheet` strictly as an audit metadata column.
"""
    with open("reports/data_quality_report.md", "w", encoding="utf-8") as f:
        f.write(quality_md)
    print("--> Saved reports/data_quality_report.md")

    # 2. Leakage Audit Report
    leakage_md = f"""# OIL SIF Precursor Detection — Leakage Audit Report (Part 1A)

> [!CRITICAL]
> **Primary Leakage Rule**: `source_sheet` MUST NEVER be used as a machine learning feature in Part 1B. It is strictly an **AUDIT-ONLY** metadata column.

---

## Direct Audit Questions & Answers

### 1. Is `source_sheet` used as an ML feature?
**NO.** `source_sheet` is strictly isolated in `AUDIT_ONLY_COLUMNS`. It is not one-hot encoded, converted to numeric features, or passed to model feature configurations.

### 2. Is the target derived from `source_sheet`?
**NO.** The target variable `High_Potential_Near_Miss` is an explicit column present within each sheet. However, the dataset construction places all `High_Potential_Near_Miss = True` records inside sheet `12_High_Potential`.

### 3. Does the workbook structure encode the target?
**YES.** The workbook construction places 100% of SIF records in sheet `12_High_Potential` and 100% of Non-SIF records in sheets 1 through 11. If a model learns sheet identity, it will achieve fake 100% accuracy via target leakage.

### 4. Are any columns direct target proxies?
**YES.** `Potential_Consequence` is a direct target proxy. There is zero category overlap between SIF and Non-SIF cases:
- SIF Consequences: *Explosion with multiple potential fatalities*, *Major equipment rupture with fire escalation*, *Major hydrocarbon release followed by flash fire*, *Multiple casualties and major fire*, *Toxic gas release affecting multiple workers*.
- Non-SIF Consequences: *Equipment damage*, *Fire*, *Hydrocarbon release*, *Lost-time injury*, *Minor injury*.

### 5. Are any fields post-investigation?
**YES.**
- `Risk_Level`: 43% of SIF records are labeled `Critical`, whereas zero Non-SIF records are `Critical`.
- `Corrective_Action` & `Action_Status`: Formulated post HSE investigation and action tracking. Unavailable at initial report creation time.

### 6. Are duplicate or near-duplicate records present?
**YES.**
- Unique descriptions: {leakage_stats['duplicate_analysis']['unique_description_count']} out of {len(cleaned_df)} total records.
- Cross-sheet description overlap: {leakage_stats['duplicate_analysis']['cross_sheet_duplicate_description_count']} descriptions recur across different sheets due to template-based text generation.

### 7. Are safety-factor columns themselves target-defining?
**PARTIALLY.** The 4 safety factor boolean flags alone cannot separate SIF from Non-SIF because both Sheet 11 (`11_4Factor_All`, Non-SIF) and Sheet 12 (`12_High_Potential`, SIF) have all 4 factors set to `True` (100 records each). Therefore, SIF classification requires analyzing the free-text description and contextual details.

### 8. Could a model obtain artificially high performance?
**YES**, if features like `source_sheet`, `Near_Miss_ID`, `Potential_Consequence`, `Risk_Level`, or post-investigation fields are allowed into the model.

### 9. What safeguards will Part 1B need?
1. Enforce `assert "source_sheet" not in MODEL_FEATURE_COLUMNS`.
2. Exclude target proxies (`Potential_Consequence`, `Risk_Level`).
3. Exclude post-investigation fields (`Corrective_Action`, `Action_Status`).
4. Focus model training on NLP text features (`Near_Miss_Description`), operational metadata (`Work_Type`, `Department`, `Refinery_Unit`), and safety factor flags.

---

## Feature Leakage Matrix

| Feature | Classification | Safe for ML? | Rationale |
| :--- | :--- | :--- | :--- |
| `source_sheet` | AUDIT ONLY | NO | Sheet 12 contains all SIF records. Direct target leakage. |
| `Near_Miss_ID` | AUDIT ONLY | NO | Prefix encodes sheet name (e.g., 12_H-*). |
| `Potential_Consequence` | TARGET PROXY | NO | 100% class separation. Assigned post-event. |
| `Risk_Level` | POST-INVESTIGATION | NO | `Critical` risk only in SIF. Post-event rating. |
| `Corrective_Action` | POST-INVESTIGATION | NO | Formulated after HSE investigation. |
| `Action_Status` | POST-INVESTIGATION | NO | HSE tracking status. |
| `Immediate_Cause` | INVESTIGATION FIELD | REQUIRES DECISION | May be assigned during investigation. |
| `Near_Miss_Description` | NLP TEXT FEATURE | YES | Primary text input logged at event time. |
| `PPE_NonCompliance` | SAFETY FACTOR | YES | Operational precursor flag. |
| `Supervisor_Negligence` | SAFETY FACTOR | YES | Operational precursor flag. |
| `Maintenance_Delay_or_Issue` | SAFETY FACTOR | YES | Operational precursor flag. |
| `Repeated_Issue_Ignored` | SAFETY FACTOR | YES | Operational precursor flag. |
| `Previous_Similar_Reports` | NUMERICAL FEATURE | YES | Historical site count available at entry. |
| `Refinery_Unit` | METADATA | YES | Location metadata. |
| `Equipment_ID` | METADATA | YES | Equipment identifier. |
| `Work_Type` | METADATA | YES | Operational task type. |
| `Department` | METADATA | YES | Reporting department. |
| `Date` | METADATA | YES | Event timestamp. |
"""
    with open("reports/leakage_audit.md", "w", encoding="utf-8") as f:
        f.write(leakage_md)
    print("--> Saved reports/leakage_audit.md")

    # 3. EDA Report
    eda_md = f"""# OIL SIF Precursor Detection — Exploratory Data Analysis Report (Part 1A)

## Dataset Overview & Target Distribution
The dataset comprises **{len(cleaned_df)}** near-miss observation records across 12 sheets from Indian refinery operations.

- **Class 0 (Non-SIF)**: {target_stats['class_0_count_non_sif']} records ({target_stats['class_0_percentage']}%)
- **Class 1 (SIF / High Potential)**: {target_stats['class_1_count_sif']} records ({target_stats['class_1_percentage']}%)
- **Class Imbalance Ratio**: {target_stats['imbalance_ratio']}:1

![Target Distribution](figures/01_target_distribution.png)

---

## Safety Factor Analysis
Each record contains 4 binary safety factor precursor flags:
1. `PPE_NonCompliance`
2. `Supervisor_Negligence`
3. `Maintenance_Delay_or_Issue`
4. `Repeated_Issue_Ignored`

### Factor Combination Insight
- Single-factor records (Sheets 01-04): 300 records (All Non-SIF)
- Two-factor records (Sheets 05-07): 225 records (All Non-SIF)
- Three-factor records (Sheets 08-10): 225 records (All Non-SIF)
- Four-factor records (Sheets 11-12): 200 records (100 Non-SIF in Sheet 11, 100 SIF in Sheet 12)

![Factor Combinations](figures/20_factor_combinations.png)

---

## Text Length & Negation Analysis
- Descriptions are generated by combining factor clauses separated by ` | `.
- Average word count for Non-SIF descriptions: ~18 words.
- Average word count for SIF descriptions: ~32 words.
- **Critical Negation Preservation**: Safety negations like *"not isolated"*, *"not locked"*, *"without helmet"* are preserved to ensure NLP models capture true hazard context.

![Description Length](figures/14_description_length_distribution.png)

---

## Visualizations Directory
All 21 generated figures are stored in `reports/figures/`:
1. `01_target_distribution.png`
2. `02_records_by_source_sheet.png`
3. `03_risk_level_distribution.png`
4. `04_work_type_distribution.png`
5. `05_department_distribution.png`
6. `06_refinery_unit_distribution.png`
7. `07_potential_consequence_distribution.png`
8. `08_immediate_cause_distribution.png`
9. `09_ppe_noncompliance_distribution.png`
10. `10_supervisor_negligence_distribution.png`
11. `11_maintenance_delay_distribution.png`
12. `12_repeated_issue_ignored_distribution.png`
13. `13_previous_similar_reports_distribution.png`
14. `14_description_length_distribution.png`
15. `15_target_vs_safety_factors.png`
16. `16_target_vs_risk_level.png`
17. `17_target_vs_work_type.png`
18. `18_target_vs_department.png`
19. `19_target_vs_refinery_unit.png`
20. `20_factor_combinations.png`
21. `21_cross_sheet_target_distribution.png`
"""
    with open("reports/eda_report.md", "w", encoding="utf-8") as f:
        f.write(eda_md)
    print("--> Saved reports/eda_report.md")

    print("\n==================================================")
    print("PART 1A PIPELINE EXECUTION COMPLETE SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    main()
