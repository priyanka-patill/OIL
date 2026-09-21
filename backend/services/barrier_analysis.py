import re
from typing import Dict, Any, List

def analyze_barrier_concerns(report_data: Dict[str, Any]) -> List[str]:
    """
    Evaluates precursor audit flags and report text to identify potential barrier concerns.
    """
    concerns = []
    
    text_content = f"{report_data.get('description', '')} {report_data.get('work_type', '')}".lower()
    
    # 1. PPE Barrier
    if report_data.get("ppe_noncompliance") or any(k in text_content for k in ["without ppe", "no helmet", "no glasses", "harness not hooked"]):
        concerns.append("Personal Protective Equipment (PPE) Defect")
        
    # 2. Supervision & Permit Barrier
    if report_data.get("supervisor_negligence") or any(k in text_content for k in ["permit expired", "no permit", "supervisor absent", "unauthorized work"]):
        concerns.append("Supervision & Work Permit Control Concern")
        
    # 3. Maintenance & Equipment Integrity Barrier
    if report_data.get("maintenance_delay_or_issue") or any(k in text_content for k in ["maintenance delay", "vibration", "seal leak", "defective valve", "corroded"]):
        concerns.append("Equipment Maintenance & Reliability Concern")
        
    # 4. Repeat Hazard & Isolation Barrier
    if report_data.get("repeated_issue_ignored") or (int(report_data.get("previous_similar_reports") or 0) > 0):
        concerns.append("Hazard Recurrence & Isolation Control Concern")

    return concerns
