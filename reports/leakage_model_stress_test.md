# OIL SIF Precursor Detection — Leakage Stress Test Report (Part 1B)

## Executive Summary
This stress test quantifies the performance distortion caused when target proxy fields (`Potential_Consequence`, `Risk_Level`) are inappropriately included as model features compared to clean baseline configurations.

---

## Stress Test Results Comparison (Validation Set)

| Feature Configuration | SIF Precision | SIF Recall | SIF F1 | Accuracy | Target Proxy Inclusion | Risk Level |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Config A (Text Only)** | `0.2564` | `0.6667` | `0.3704` | `0.7606` | Excluded | Safe |
| **Config B (Clean Structured)** | `0.5238` | `0.7333` | `0.6111` | `0.9014` | Excluded | Safe |
| **Config C (Combined Clean)** | `0.4091` | `0.6` | `0.4865` | `0.8662` | Excluded | Safe |
| **LEAKAGE MODEL (With Potential_Consequence & Risk_Level)** | `1.0` | `1.0` | `1.0` | `1.0` | **INCLUDED** | 🚨 **TARGET LEAKAGE** |

---

## Audit Conclusion & Recommendation
- **Leakage Impact**: Including `Potential_Consequence` and `Risk_Level` yields artificially inflated 100% metrics because `Potential_Consequence` categories strictly separate SIF vs Non-SIF cases.
- **Enforced Safeguard**: `Potential_Consequence`, `Risk_Level`, `Corrective_Action`, `Action_Status`, and `source_sheet` MUST remain strictly excluded from all Part 1C model feature pipelines.
