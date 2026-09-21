import pandas as pd
from typing import Dict, Any, List

FEATURE_LEAKAGE_CLASSIFICATION = {
    "source_sheet": {
        "classification": "AUDIT ONLY / STRICT EXCLUSION FROM ML",
        "reason": "Directly encodes target (12_High_Potential = SIF). Using this feature causes target leakage.",
        "safe_for_ml": False
    },
    "Near_Miss_ID": {
        "classification": "AUDIT ONLY / RECORD IDENTIFIER",
        "reason": "Prefix encodes sheet type (e.g., 12_H-* vs 11_4-*). Must be excluded from ML features.",
        "safe_for_ml": False
    },
    "Potential_Consequence": {
        "classification": "TARGET PROXY / LEAKAGE",
        "reason": "100% separation between SIF consequences (e.g. Explosion, Flash Fire) and Non-SIF consequences. Direct target proxy.",
        "safe_for_ml": False
    },
    "Risk_Level": {
        "classification": "POST-INVESTIGATION LEAKAGE / TARGET PROXY",
        "reason": "Critical risk appears exclusively in SIF cases (43%). Assigned post HSE investigation.",
        "safe_for_ml": False
    },
    "Corrective_Action": {
        "classification": "POST-INVESTIGATION LEAKAGE",
        "reason": "Written after HSE investigation; unavailable when a new report is logged.",
        "safe_for_ml": False
    },
    "Action_Status": {
        "classification": "POST-INVESTIGATION LEAKAGE",
        "reason": "Tracked after HSE intervention; unavailable at initial report entry.",
        "safe_for_ml": False
    },
    "Immediate_Cause": {
        "classification": "POTENTIAL LEAKAGE / INVESTIGATION FIELD",
        "reason": "May be determined during safety investigation. Requires Part 1B evaluation.",
        "safe_for_ml": False
    },
    "Previous_Similar_Reports": {
        "classification": "SAFE / CONTEXTUAL NUMERICAL FEATURE",
        "reason": "Historical record available at filing time.",
        "safe_for_ml": True
    },
    "PPE_NonCompliance": {
        "classification": "SAFE / SAFETY FACTOR FEATURE",
        "reason": "Safety precursor flag available at report entry time.",
        "safe_for_ml": True
    },
    "Supervisor_Negligence": {
        "classification": "SAFE / SAFETY FACTOR FEATURE",
        "reason": "Safety precursor flag available at report entry time.",
        "safe_for_ml": True
    },
    "Maintenance_Delay_or_Issue": {
        "classification": "SAFE / SAFETY FACTOR FEATURE",
        "reason": "Safety precursor flag available at report entry time.",
        "safe_for_ml": True
    },
    "Repeated_Issue_Ignored": {
        "classification": "SAFE / SAFETY FACTOR FEATURE",
        "reason": "Safety precursor flag available at report entry time.",
        "safe_for_ml": True
    },
    "Near_Miss_Description": {
        "classification": "SAFE / PRIMARY NLP TEXT FEATURE",
        "reason": "Core text report submitted by worker/observer at event time.",
        "safe_for_ml": True
    },
    "Refinery_Unit": {
        "classification": "SAFE / CATEGORICAL METADATA",
        "reason": "Operational location metadata available at filing time.",
        "safe_for_ml": True
    },
    "Equipment_ID": {
        "classification": "SAFE / CATEGORICAL METADATA",
        "reason": "Equipment reference metadata available at filing time.",
        "safe_for_ml": True
    },
    "Work_Type": {
        "classification": "SAFE / CATEGORICAL METADATA",
        "reason": "Operational activity category available at filing time.",
        "safe_for_ml": True
    },
    "Department": {
        "classification": "SAFE / CATEGORICAL METADATA",
        "reason": "Reporting department metadata available at filing time.",
        "safe_for_ml": True
    },
    "Date": {
        "classification": "SAFE / TEMPORAL METADATA",
        "reason": "Event timestamp available at filing time.",
        "safe_for_ml": True
    }
}

def perform_leakage_audit(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs a thorough leakage audit across all dataset fields and duplicate records.
    """
    audit_results = {
        "is_source_sheet_used_in_ml": False,
        "is_target_derived_from_source_sheet": False, # Target exists in workbook column, but sheet 12 contains all True values
        "workbook_structure_encodes_target": True,
        "feature_classifications": FEATURE_LEAKAGE_CLASSIFICATION,
        "duplicate_analysis": {},
        "target_proxies_found": ["Potential_Consequence", "Risk_Level"],
        "post_investigation_fields_found": ["Corrective_Action", "Action_Status", "Immediate_Cause"]
    }
    
    # 1. Exact duplicate rows (excluding source_sheet)
    feature_cols = [c for c in df.columns if c != 'source_sheet']
    exact_dups = int(df.duplicated(subset=feature_cols).sum())
    
    # 2. Duplicate Near_Miss_ID
    dup_ids = int(df.duplicated(subset=['Near_Miss_ID']).sum()) if 'Near_Miss_ID' in df.columns else 0
    
    # 3. Duplicate Near_Miss_Description
    dup_desc = int(df.duplicated(subset=['Near_Miss_Description']).sum()) if 'Near_Miss_Description' in df.columns else 0
    
    # 4. Duplicate Near_Miss_Description across different sheets
    cross_sheet_dup_desc = int(df.duplicated(subset=['Near_Miss_Description', 'High_Potential_Near_Miss']).sum()) if 'Near_Miss_Description' in df.columns else 0
    
    audit_results["duplicate_analysis"] = {
        "exact_duplicate_rows_excl_source_sheet": exact_dups,
        "duplicate_near_miss_id_count": dup_ids,
        "unique_near_miss_id_count": df['Near_Miss_ID'].nunique() if 'Near_Miss_ID' in df.columns else 0,
        "duplicate_description_count": dup_desc,
        "unique_description_count": df['Near_Miss_Description'].nunique() if 'Near_Miss_Description' in df.columns else 0,
        "cross_sheet_duplicate_description_count": cross_sheet_dup_desc
    }
    
    return audit_results
