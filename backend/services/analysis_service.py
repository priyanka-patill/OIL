import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.database.models import SafetyReport, AIAnalysis, ReportStatus, User
from backend.services import (
    ml_service, life_saving_rules, hazard_analysis, barrier_analysis, 
    similarity_service, risk_service, audit_service
)

logger = logging.getLogger("backend.services.analysis_service")

def analyze_safety_report(db: Session, report_id: int, current_user: User) -> AIAnalysis:
    """
    Orchestrates end-to-end AI safety analysis for a report:
    1. Fetches report from DB.
    2. Runs Part 1C predict_sif().
    3. Runs Life-Saving Rules, Hazard, and Barrier analysis.
    4. Runs SIM_EVAL_v1 Similarity Engine (system-calculated previous similar reports count).
    5. Runs RISK_EVAL_v1 Risk Assessment Engine (system-calculated Risk Level).
    6. Persists AIAnalysis record into database.
    7. Updates report previous_similar_reports, risk_level, and status to AI_ANALYZED.
    8. Logs audit event.
    """
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety report with ID #{report_id} not found."
        )

    # Convert ORM model to dictionary for prediction
    report_dict = {
        "description": report.description,
        "refinery_unit": report.refinery_unit,
        "equipment_id": report.equipment_id,
        "work_type": report.work_type,
        "activity": report.activity,
        "department": report.department,
        "ppe_noncompliance": report.ppe_noncompliance,
        "supervisor_negligence": report.supervisor_negligence,
        "maintenance_delay_or_issue": report.maintenance_delay_or_issue,
        "repeated_issue_ignored": report.repeated_issue_ignored,
        "previous_similar_reports": report.previous_similar_reports,
    }

    try:
        # 1. Run Part 1C ML Prediction & TF-IDF Explainability
        ml_result = ml_service.run_sif_prediction(report_dict)
        
        # 2. Run Deterministic Rule-Based Analyses
        lsr_matched = life_saving_rules.analyze_life_saving_rules(report_dict)
        hazards_matched = hazard_analysis.analyze_hazards(report_dict)
        barriers_matched = barrier_analysis.analyze_barrier_concerns(report_dict)

        # 3. System-Calculated Previous Similar Reports (SIM_EVAL_v1)
        sim_result = similarity_service.calculate_report_similarity(db, report, current_user)
        similar_count = sim_result["previous_similar_reports_count"]

        # 4. System-Calculated Risk Level Assessment (RISK_EVAL_v1)
        risk_result = risk_service.calculate_report_risk(
            report_dict=report_dict,
            ml_result=ml_result,
            hazards=hazards_matched,
            barriers=barriers_matched,
            previous_similar_reports_count=similar_count
        )
        calculated_risk_level = risk_result["risk_level"]

        # 5. Check for existing analysis (idempotency)
        existing_analysis = db.query(AIAnalysis).filter(AIAnalysis.report_id == report_id).first()
        
        if existing_analysis:
            analysis = existing_analysis
            analysis.model_version = ml_result["model_version"]
            analysis.prediction = ml_result["prediction"]
            analysis.classification = ml_result["classification"]
            analysis.probability_or_score = ml_result["probability"]
            analysis.threshold = ml_result["threshold"]
            analysis.explanation_json = json.dumps({
                "explanation": ml_result.get("explanation", []),
                "human_readable": ml_result.get("human_readable_explanation", ""),
                "disclaimer": ml_result.get("disclaimer", "")
            })
            analysis.life_saving_rules_json = json.dumps(lsr_matched)
            analysis.hazards_json = json.dumps(hazards_matched)
            analysis.barrier_concerns_json = json.dumps(barriers_matched)
            analysis.previous_similar_reports_count = similar_count
            analysis.similar_reports_json = json.dumps(sim_result["similar_reports"])
            analysis.risk_level = calculated_risk_level
            analysis.risk_explanation_json = json.dumps(risk_result["risk_explanation"])
            analysis.risk_methodology_version = risk_result["methodology_version"]
            analysis.similarity_methodology_version = sim_result["methodology_version"]
            analysis.analysis_status = "COMPLETED"
        else:
            analysis = AIAnalysis(
                report_id=report.id,
                model_version=ml_result["model_version"],
                prediction=ml_result["prediction"],
                classification=ml_result["classification"],
                probability_or_score=ml_result["probability"],
                threshold=ml_result["threshold"],
                explanation_json=json.dumps({
                    "explanation": ml_result.get("explanation", []),
                    "human_readable": ml_result.get("human_readable_explanation", ""),
                    "disclaimer": ml_result.get("disclaimer", "")
                }),
                life_saving_rules_json=json.dumps(lsr_matched),
                hazards_json=json.dumps(hazards_matched),
                barrier_concerns_json=json.dumps(barriers_matched),
                previous_similar_reports_count=similar_count,
                similar_reports_json=json.dumps(sim_result["similar_reports"]),
                risk_level=calculated_risk_level,
                risk_explanation_json=json.dumps(risk_result["risk_explanation"]),
                risk_methodology_version=risk_result["methodology_version"],
                similarity_methodology_version=sim_result["methodology_version"],
                analysis_status="COMPLETED"
            )
            db.add(analysis)

        # 6. Update SafetyReport table with authoritative system-calculated values
        report.previous_similar_reports = similar_count
        report.risk_level = calculated_risk_level

        if report.status == ReportStatus.DRAFT:
            report.status = ReportStatus.SUBMITTED

        db.commit()
        db.refresh(analysis)
        db.refresh(report)

        # 5. Audit Logging
        audit_service.log_audit_event(
            db=db,
            action="REPORT_AI_ANALYZED",
            user_id=current_user.id,
            entity_type="SafetyReport",
            entity_id=str(report.id),
            metadata={"prediction": ml_result["prediction"], "probability": ml_result["probability"]}
        )

        logger.info(f"AI Analysis completed for Report #{report.id} ({report.report_number}): {ml_result['prediction']}")
        return analysis

    except Exception as e:
        db.rollback()
        logger.error(f"Error executing AI Analysis for Report #{report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Safety Analysis execution failed: {str(e)}"
        )

def get_analysis_for_report(db: Session, report_id: int) -> Optional[AIAnalysis]:
    """Retrieves persisted AI analysis for a safety report."""
    return db.query(AIAnalysis).filter(AIAnalysis.report_id == report_id).first()
