import os
import logging
from typing import Dict, Any, Tuple, List, Optional
from src.predict import load_model, predict_sif

logger = logging.getLogger("backend.services.ml_service")

DEFAULT_MODEL_DIR = "models/final_model"
_MODEL_PACKAGE: Optional[Dict[str, Any]] = None

def init_ml_service(model_dir: str = DEFAULT_MODEL_DIR) -> Dict[str, Any]:
    """
    Initializes and caches the Part 1C ML model package once during application startup.
    """
    global _MODEL_PACKAGE
    try:
        logger.info(f"Loading Part 1C SIF Model package from '{model_dir}'...")
        pkg = load_model(model_dir)
        version = pkg.get("metadata", {}).get("model_version", "sif_model_v1")
        threshold = pkg.get("threshold", 0.60)
        logger.info(f"ML Model Package successfully loaded. Version: '{version}', Threshold: {threshold}")
        _MODEL_PACKAGE = pkg
        return pkg
    except Exception as e:
        logger.error(f"Failed to load Part 1C ML model package: {e}", exc_info=True)
        _MODEL_PACKAGE = None
        raise RuntimeError(f"ML Service Initialization Failed: {e}")

def get_ml_package() -> Dict[str, Any]:
    """
    Returns the cached ML model package. Initializes if not already loaded.
    """
    global _MODEL_PACKAGE
    if _MODEL_PACKAGE is None:
        return init_ml_service()
    return _MODEL_PACKAGE

def prepare_model_input(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts API / ORM report data into Part 1C prediction input dictionary.
    Excludes post-event leakage fields (source_sheet, Potential_Consequence, Risk_Level, etc.)
    """
    model_input = {
        "Near_Miss_Description": str(report_data.get("description") or report_data.get("Near_Miss_Description") or "").strip(),
        "Refinery_Unit": report_data.get("refinery_unit") or report_data.get("Refinery_Unit") or "",
        "Equipment_ID": report_data.get("equipment_id") or report_data.get("Equipment_ID") or "",
        "Work_Type": report_data.get("work_type") or report_data.get("Work_Type") or "",
        "Department": report_data.get("department") or report_data.get("Department") or "",
        "PPE_NonCompliance": bool(report_data.get("ppe_noncompliance")),
        "Supervisor_Negligence": bool(report_data.get("supervisor_negligence")),
        "Maintenance_Delay_or_Issue": bool(report_data.get("maintenance_delay_or_issue")),
        "Repeated_Issue_Ignored": bool(report_data.get("repeated_issue_ignored")),
        "Previous_Similar_Reports": int(report_data.get("previous_similar_reports") or 0),
    }

    # Explicit Leakage Protection: Ensure source_sheet is NOT present
    model_input.pop("source_sheet", None)
    model_input.pop("12_High_Potential", None)

    return model_input

def run_sif_prediction(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes Part 1C predict_sif() using the cached model package.
    """
    pkg = get_ml_package()
    
    # Map 'description' key if needed
    input_report = report_data.copy()
    if "description" in input_report and "Near_Miss_Description" not in input_report:
        input_report["Near_Miss_Description"] = input_report["description"]

    prediction_result = predict_sif(input_report, model_package=pkg)
    return prediction_result
