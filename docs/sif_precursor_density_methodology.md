# SIF Precursor Density & Small-Sample Methodology

## 1. Density Formula & Definition

**SIF Precursor Density** is a descriptive ratio representing the proportion of eligible analyzed safety reports that contain Serious Injury & Fatality (SIF) precursors:

$$\text{SIF Precursor Density} = \frac{\text{SIF-Potential Reports}}{\text{Eligible Analyzed Reports}}$$

Where:
- **Numerator ($\text{SIF-Potential Reports}$)**: Count of safety reports in the target sample classified as SIF-Potential (`classification == 1`).
- **Denominator ($\text{Eligible Analyzed Reports}$)**: Count of safety reports in the target sample for which a valid AI SIF analysis exists (`has_ai_analysis == True`).

---

## 2. Critical Non-Probability Disclosure

> [!IMPORTANT]
> **Descriptive Statistic, NOT Probability**: SIF Precursor Density is a descriptive statistic summarizing observed report classifications.
> It is **NOT**:
> - Fatality Probability
> - Probability of a SIF event
> - Probability of a future accident
> - Predictive risk probability

It must never be used to infer future accident probabilities.

---

## 3. Zero-Denominator Handling

If a selected filter population contains zero eligible analyzed reports ($\text{Denominator} = 0$):
- $\text{SIF Precursor Density} = \text{null}$
- $\text{Data Sufficiency} = \text{"NOT_AVAILABLE"}$

The engine does **NOT** return `0%` or `0.0`, as returning zero would incorrectly imply that zero SIF precursors were found in an analyzed dataset.

---

## 4. Small-Sample Protection & Data Sufficiency

To prevent misinterpretation of high density ratios in small samples (e.g., 1 analyzed report with 1 SIF = 100% density), the engine attaches a standard `data_sufficiency` indicator:

| Analyzed Population ($N$) | Data Sufficiency Status | Analytical Guidance |
| :--- | :--- | :--- |
| $N \ge 10$ | **`SUFFICIENT`** | Population size meets standard analytical confidence. |
| $3 \le N \le 9$ | **`LIMITED`** | Limited sample size; interpret metrics with caution. |
| $1 \le N \le 2$ | **`INSUFFICIENT`** | Very small sample size; density ratio is indicative only. |
| $N = 0$ | **`NOT_AVAILABLE`** | Zero analyzed reports available. |

---

## 5. Separate AI vs HSE Metrics

- **AI SIF Precursor Density**: Calculated from initial AI model predictions.
- **HSE Validated Density**: Calculated from human HSE review decisions (`modified_classification == 1`).
- AI and HSE metrics are kept strictly separate in all API outputs and documentation. Missing HSE reviews are represented as `Not Validated` rather than assumed Non-SIF.
