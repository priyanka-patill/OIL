# OIL SIF Precursor Detection — False Negative Analysis (Part 1B)

## Executive Summary
False Negatives represent actual SIF-Potential cases missed by the model (predicted as Non-SIF). In high-hazard refinery operations, False Negatives are the most critical safety failure mode.

- **Total Actual SIF Records Evaluated**: `15`
- **True Positives (SIF Detected)**: `11`
- **False Negatives (SIF Missed)**: `4`
- **False Negative Rate**: `26.7%`
- **False Positives (False Alarms)**: `8`

---

## False Negative Records Detail

| Record ID | Source Sheet | Work Type | Department | Probability | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `12_H-100` | `12_High_Potential` | Material Handling | Electrical Maintenance | `0.414` | Contractor used damaged safety shoes \| Maintenance continued without confirmed isolation \| Pressure gauge malfunction remained awaiting replacement \| Oil accumulation near pump had generated repeated housekeeping complaints |
| `12_H-023` | `12_High_Potential` | Preventive Maintenance | Electrical Maintenance | `0.426` | Maintenance worker handled chemical line without chemical-resistant gloves \| Hot work continued before required gas test was completed \| Corrosion on process pipeline was identified but repair was deferred \| Compressor abnormal vibration had been reported three times |
| `12_H-047` | `12_High_Potential` | Inspection | Mechanical Maintenance | `0.371` | Worker selected unsuitable respiratory protection for task \| Lifting operation continued despite unsafe weather conditions \| Repeated mechanical seal leakage was deferred to shutdown \| Pump leakage had been reported twice previously |
| `12_H-090` | `12_High_Potential` | Routine Operation | Mechanical Maintenance | `0.530` | Worker entered process area without safety helmet \| Supervisor observed missing PPE but allowed work to continue \| Hydrocarbon leakage from process pipeline flange remained pending for repair \| Bearing temperature had repeatedly been reported as abnormal |


---

## Pattern Analysis & Root Causes

1. **Short / Ambiguous Descriptions**: Near-miss descriptions with very concise wording or missing explicit hazard keywords.
2. **Precursor Factor Masking**: Scenarios where safety factors are active but phrasing resembles routine operational maintenance.
3. **Template Variations**: Novel clause combinations present in test/validation sets not seen in training.
4. **Safeguards for Part 1C**:
   - Apply optimal decision threshold (e.g., lower threshold to boost SIF recall).
   - Implement an automated high-risk keyword trigger alongside model prediction scores.
