import re
from typing import Dict, Any, List

# IOGP Standardized Life-Saving Rules Mapping Definitions
LSR_RULES = [
  {
    "rule": "Bypassing Safety Controls",
    "keywords": [r"bypass", r"override", r"interlock", r"loto", r"isolation lock", r"safety device", r"tamper"],
    "flag_check": lambda r: bool(r.get("supervisor_negligence") or r.get("repeated_issue_ignored")),
  },
  {
    "rule": "Confined Space",
    "keywords": [r"confined space", r"vessel entry", r"tank", r"manhole", r"sump", r"pit entry", r"column internal"],
    "flag_check": lambda r: False,
  },
  {
    "rule": "Energy Isolation",
    "keywords": [r"loto", r"lockout", r"tagout", r"electrical isolation", r"valve lock", r"de-energiz", r"power supply"],
    "flag_check": lambda r: bool(r.get("maintenance_delay_or_issue")),
  },
  {
    "rule": "Hot Work",
    "keywords": [r"hot work", r"weld", r"grind", r"gas cut", r"spark", r"flame", r"ignition source"],
    "flag_check": lambda r: False,
  },
  {
    "rule": "Line of Fire",
    "keywords": [r"line of fire", r"pressure release", r"flying debris", r"suspended load", r"swinging", r"snapped", r"whiplash"],
    "flag_check": lambda r: False,
  },
  {
    "rule": "Safe Mechanical Lifting",
    "keywords": [r"crane", r"hoist", r"rigging", r"sling", r"lifting operation", r"suspended load", r"derrick"],
    "flag_check": lambda r: False,
  },
  {
    "rule": "Working at Height",
    "keywords": [r"scaffold", r"ladder", r"harness", r"height", r"fall protection", r"elevated platform", r"roof"],
    "flag_check": lambda r: False,
  },
  {
    "rule": "Personal Protective Equipment (PPE)",
    "keywords": [r"ppe", r"helmet", r"safety glass", r"goggles", r"respirator", r"earplug", r"harness", r"gloves"],
    "flag_check": lambda r: bool(r.get("ppe_noncompliance")),
  },
]

def analyze_life_saving_rules(report_data: Dict[str, Any]) -> List[str]:
    """
    Evaluates observation text, work type, activity, and precursor flags to identify
    potentially relevant IOGP Life-Saving Rules.
    """
    text_content = f"{report_data.get('description', '')} {report_data.get('work_type', '')} {report_data.get('activity', '')} {report_data.get('equipment_id', '')}".lower()
    
    matched_rules = []
    
    for item in LSR_RULES:
        rule_name = item["rule"]
        
        # Check text keyword patterns
        text_match = any(re.search(kw, text_content, re.IGNORECASE) for kw in item["keywords"])
        
        # Check precursor flag criteria
        flag_match = item["flag_check"](report_data)
        
        if text_match or flag_match:
            matched_rules.append(rule_name)
            
    return matched_rules
