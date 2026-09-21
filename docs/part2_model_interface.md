# OIL SIF Precursor Detection Engine — Part 2 Interface Contract

This document defines the technical integration contract between the **Part 1 SIF NLP Model Engine** and the **Part 2 Backend / Web Application / API Layer**.

---

## 1. Python Module Integration

Part 2 services can import and call the SIF prediction engine directly:

```python
from src.predict import load_model, predict_sif

# Load and cache model artifacts once at startup
model_pkg = load_model("models/final_model")

# Invoke prediction function for a new report
report_data = {
    "Near_Miss_Description": "Worker entered process area without safety helmet and bypassed isolation locks during pump overhaul.",
    "Refinery_Unit": "Hydrogen Unit",
    "Equipment_ID": "P-305",
    "Work_Type": "Preventive Maintenance",
    "Department": "Contractor",
    "PPE_NonCompliance": True,
    "Supervisor_Negligence": False,
    "Maintenance_Delay_or_Issue": True,
    "Repeated_Issue_Ignored": False,
    "Previous_Similar_Reports": 2
}

result = predict_sif(report_data, model_package=model_pkg)
print(result)
```

---

## 2. Input JSON Schema (`predict_sif(report)`)

| Field | Type | Required? | Description |
| :--- | :--- | :---: | :--- |
| `Near_Miss_Description` | `string` | **Yes** | Free-text description logged by worker/observer. |
| `Refinery_Unit` | `string` | Optional | Operational refinery unit location metadata. |
| `Equipment_ID` | `string` | Optional | Tag identifier of involved equipment. |
| `Work_Type` | `string` | Optional | Category of activity (e.g. *Preventive Maintenance*, *Routine Operation*). |
| `Department` | `string` | Optional | Reporting department or contractor. |
| `PPE_NonCompliance` | `boolean` | Optional | Flag indicating PPE non-compliance precursor. |
| `Supervisor_Negligence` | `boolean` | Optional | Flag indicating supervisory breakdown. |
| `Maintenance_Delay_or_Issue` | `boolean` | Optional | Flag indicating deferred or overdue maintenance. |
| `Repeated_Issue_Ignored` | `boolean` | Optional | Flag indicating recurring unaddressed hazard. |
| `Previous_Similar_Reports` | `integer` | Optional | Historical count of similar site incidents. |

> [!WARNING]
> **Leakage Fields Stripping**: If Part 2 passes `source_sheet`, `Potential_Consequence`, `Risk_Level`, `Corrective_Action`, or `Action_Status`, `predict_sif()` will automatically strip them from model input to prevent data leakage.

---

## 3. Output JSON Schema

```json
{
  "prediction": "SIF-Potential",
  "classification": 1,
  "probability": 0.8421,
  "threshold": 0.60,
  "model_version": "sif_model_v1",
  "explanation": [
    {
      "type": "text_ngram",
      "feature": "without safety",
      "weight": 1.4215,
      "contribution": 0.4215
    },
    {
      "type": "text_ngram",
      "feature": "bypassed",
      "weight": 1.1052,
      "contribution": 0.3512
    }
  ],
  "human_readable_explanation": "Model prediction influenced by key safety-hazard terms: 'without safety, bypassed'.",
  "disclaimer": "This prediction is an AI safety decision-support score and requires qualified HSE professional review.",
  "warnings": []
}
```

---

## 4. Output Field Definitions

- `prediction` (`string`): `"SIF-Potential"` or `"Non-SIF"`.
- `classification` (`integer`): `1` for SIF-Potential, `0` for Non-SIF.
- `probability` (`float`): Calibrated positive-class probability `[0.0, 1.0]`.
- `threshold` (`float`): Operational decision threshold (`0.60`).
- `model_version` (`string`): Model version identifier (`"sif_model_v1"`).
- `explanation` (`array`): List of top contributing n-gram terms with model weights.
- `human_readable_explanation` (`string`): Operator-friendly natural language summary.
- `disclaimer` (`string`): Mandatory decision-support notice.
