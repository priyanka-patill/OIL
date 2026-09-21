# Cross-Report Correlation & Safety Intelligence Methodology

## 1. Definition of Cross-Report Correlation

In this platform, **correlation** refers to the empirical frequency of co-occurrence of safety dimensions across multiple independent safety reports.

> [!IMPORTANT]
> **Non-Causal Principle**: Correlation does **NOT** imply causation.
> The analytics engine identifies observed recurring combinations (e.g., *Pump A + Maintenance + Energy Isolation* occurring 5 times). It does not claim that *Energy Isolation caused the incident*, but rather that *Energy Isolation appeared repeatedly in contributing reports during Maintenance on Pump A*.

---

## 2. Analyzed Dimensions & Combinations

The correlation engine evaluates co-occurrences across:
1. **Equipment Identifiers** (`equipment_id`)
2. **Operational Activities** (`activity`)
3. **Work Types** (`work_type`)
4. **Physical Locations** (`location`, `refinery_unit`, `site`)
5. **Departments** (`department`)
6. **Precursor Flags** (`ppe_noncompliance`, `supervisor_negligence`, `maintenance_delay_or_issue`, `repeated_issue_ignored`)
7. **AI & HSE Barriers / Hazards** (`barriers`, `hazards`, `life_saving_rules`)

### Combination Types Generated
- **Single-Dimension Recurrence**: High frequency of a single entity (e.g. `Equipment = Pump P-101`, count = 7).
- **Pairwise Recurrence**: Two co-occurring factors (e.g. `Activity = Maintenance` + `Barrier = Energy Isolation`, count = 5).
- **Multi-Factor Recurrence**: Three or more co-occurring factors (e.g. `Equipment = Pump P-101` + `Activity = Seal Replacement` + `Precursor = Maintenance Delay`, count = 5).

---

## 3. Support Thresholds & One-Off Observations

- **Minimum Pattern Support (`ANALYTICS_MIN_PATTERN_COUNT`)**: Set centrally to `3` by default.
- **Rule of One-Off Observations**: A combination that appears only once or twice is classified as an `Observed Combination` and is excluded from recurring pattern outputs. A single incident NEVER constitutes a pattern.

---

## 4. Model Version & SIF Count Isolation

- **AI SIF Counts**: Calculated strictly from AI predictions (`classification == 1`).
- **HSE Validated SIF Counts**: Calculated strictly from HSE human review decisions (`modified_classification == 1`).
- AI and HSE counts are stored and displayed separately. HSE reviews do not overwrite original AI prediction records.
- Model versions (e.g., `sif_model_v1`) are tracked on every `AIAnalysis` DTO to prevent mixing metrics from incompatible model releases.

---

## 5. Related Report Evidence Generation

Relatedness between reports is computed via weighted multi-dimensional overlap:
- Equipment match weight: `3.0`
- Activity match weight: `2.0`
- Location match weight: `2.0`
- Shared Hazard / Barrier weight: `1.5` per item
- Description TF-IDF Cosine Similarity weight: `4.0` (for similarity > `0.30`)

Every related report output presents explicit, transparent textual evidence explaining why the reports were paired (e.g., `"Matching Equipment: Pump P-101; Shared Barrier: Energy Isolation; Description Text Similarity: 84.2%"`). No similarity scores are fabricated without actual algorithm execution.
