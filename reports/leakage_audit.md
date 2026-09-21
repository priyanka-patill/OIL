# OIL SIF Precursor Detection — Leakage Audit Report (Part 1A)

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
- Unique descriptions: 609 out of 950 total records.
- Cross-sheet description overlap: 340 descriptions recur across different sheets due to template-based text generation.

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
