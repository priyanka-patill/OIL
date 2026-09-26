import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.database.database import SessionLocal, init_db, engine, Base
from backend.database.models import (
    User, UserRole, SafetyReport, ReportType, ReportStatus, 
    HSEReview, HSEDecision, InterventionRecommendation, InterventionCategory, 
    InterventionStatus, InterventionPriority, Action, ActionPriority, ActionStatus
)
from backend.security.auth import hash_password
from backend.services.report_service import generate_unique_report_number
from backend.services.analysis_service import analyze_safety_report

def seed_database():
    print("==================================================")
    print("SEEDING PRODUCTION & DEVELOPMENT DEMO DATABASE")
    print("==================================================")
    
    # Re-create database tables to ensure all schema columns exist
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print(f"--> Note on table drop: {e}")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Create Demo Users
        users_to_create = [
            {
                "name": "Ramesh Sharma",
                "email": "user@oil.in",
                "password": "Password123!",
                "role": UserRole.HSE_USER,
                "department": "Operations",
                "site": "Digboi Refinery"
            },
            {
                "name": "Anil Verma",
                "email": "manager@oil.in",
                "password": "Password123!",
                "role": UserRole.HSE_MANAGER,
                "department": "HSE",
                "site": "Duliajan Site"
            },
            {
                "name": "OIL Admin User",
                "email": "admin@oil.in",
                "password": "Password123!",
                "role": UserRole.ADMIN,
                "department": "IT Admin",
                "site": "Headquarters"
            }
        ]

        created_users = {}

        for u_data in users_to_create:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                u = User(
                    name=u_data["name"],
                    email=u_data["email"],
                    password_hash=hash_password(u_data["password"]),
                    role=u_data["role"],
                    department=u_data["department"],
                    site=u_data["site"],
                    is_active=True
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                created_users[u.email] = u
                print(f"--> Created User: {u.email} (Role: {u.role.value})")
            else:
                created_users[existing.email] = existing
                print(f"--> User exists: {existing.email} (Role: {existing.role.value})")

        demo_user = created_users["user@oil.in"]
        manager_user = created_users["manager@oil.in"]

        # 2. Rich Prebuilt Sample Reports (14 Diverse Safety Observations)
        sample_reports_data = [
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-22",
                "site": "Digboi Refinery",
                "refinery_unit": "Hydrogen Unit",
                "location": "Compressor House B",
                "equipment_id": "P-305",
                "work_type": "Preventive Maintenance",
                "department": "Operations",
                "description": "Contract worker had entered process area without safety helmet and had continued work without LOTO isolation locks during pump overhaul. This abnormal hazard had been reported repeatedly in previous inspections.",
                "ppe_noncompliance": True,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 2,
                "status": ReportStatus.HSE_VALIDATED
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-21",
                "site": "Duliajan Site",
                "refinery_unit": "HCU",
                "location": "Scaffold Deck 4",
                "equipment_id": "SCAF-102",
                "work_type": "Hot Work",
                "department": "Contractor",
                "description": "Welder worked at height without safety harness and had continued work near high pressure hydrocarbon gas line. Repeatedly reported supervisor negligence in previous inspections.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 1,
                "status": ReportStatus.HSE_VALIDATED
            },
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-20",
                "site": "Digboi Refinery",
                "refinery_unit": "Hydrogen Unit",
                "location": "Reactor Feed Pump House",
                "equipment_id": "P-101A",
                "work_type": "Line Breaking",
                "department": "Maintenance",
                "description": "Technician had opened valve flange without depressurizing line and without chemical splash goggles. Similar abnormal maintenance issues had been reported in two previous inspections.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 3,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-19",
                "site": "Digboi Refinery",
                "refinery_unit": "FCCU",
                "location": "Riser Reactor Structure",
                "equipment_id": "E-204",
                "work_type": "Confined Space Entry",
                "department": "Operations",
                "description": "Operator had entered confined space vessel without continuous gas testing monitor. The worker had continued work without standby supervisor as reported in previous inspections.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 2,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_CONDITION,
                "date": "2026-09-18",
                "site": "Digboi Refinery",
                "refinery_unit": "Crude Unit",
                "location": "Pipeline Rack Bay 3",
                "equipment_id": "V-101",
                "work_type": "Inspection",
                "department": "Maintenance",
                "description": "Minor oil weeping observed from valve gland packing during routine operator rounds in tank farm corridor.",
                "ppe_noncompliance": False,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.CLOSED
            },
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-17",
                "site": "Duliajan Site",
                "refinery_unit": "LPG Bottling Plant",
                "location": "Carrousel Shed 2",
                "equipment_id": "COMP-401",
                "work_type": "Electrical Maintenance",
                "department": "Contractor",
                "description": "Electrician had worked inside energized MCC panel without LOTO padlocks and without arc flash suit. Abnormal electrical hazard had been reported repeatedly.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 4,
                "status": ReportStatus.HSE_VALIDATED
            },
            {
                "report_type": ReportType.UNSAFE_CONDITION,
                "date": "2026-09-16",
                "site": "Digboi Refinery",
                "refinery_unit": "Offsite Utilities",
                "location": "Substation 3",
                "equipment_id": "SUB-03",
                "work_type": "Routine Operations",
                "department": "Electrical",
                "description": "Emergency lighting battery backup indicator warning light glowing amber during weekly check.",
                "ppe_noncompliance": False,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.CLOSED
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-15",
                "site": "Duliajan Site",
                "refinery_unit": "HCU",
                "location": "Fractionator Column Base",
                "equipment_id": "T-301",
                "work_type": "Scaffolding",
                "department": "Contractor",
                "description": "Scaffolder had erected platform without toe-boards and had continued work leaving loose metal pipes unanchored on upper deck as reported in previous inspections.",
                "ppe_noncompliance": False,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 2,
                "status": ReportStatus.HSE_VALIDATED
            },
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-14",
                "site": "Digboi Refinery",
                "refinery_unit": "Catalytic Reformer",
                "location": "Furnace F-101 Area",
                "equipment_id": "F-101",
                "work_type": "Hot Work",
                "department": "Operations",
                "description": "Hot work spark had fallen near oily rag bin due to damaged fire blanket shielding. The abnormal hazard had appeared in previous inspections.",
                "ppe_noncompliance": False,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 1,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-13",
                "site": "Digboi Refinery",
                "refinery_unit": "Effluent Treatment Plant",
                "location": "Bio-Reactor Tank 2",
                "equipment_id": "ETP-P-02",
                "work_type": "Chemical Handling",
                "department": "Operations",
                "description": "Operator poured chemical dosing liquid without rubber gloves during routine batch preparation.",
                "ppe_noncompliance": True,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.HSE_VALIDATED
            },
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-12",
                "site": "Duliajan Site",
                "refinery_unit": "Hydrogen Unit",
                "location": "High Pressure Separator",
                "equipment_id": "V-202",
                "work_type": "Preventive Maintenance",
                "department": "Maintenance",
                "description": "Fitter had removed blind flange bolts without verifying zero pressure status on local pressure gauge. Worker had continued work despite abnormal vibration reported repeatedly.",
                "ppe_noncompliance": False,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 3,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_CONDITION,
                "date": "2026-09-11",
                "site": "Digboi Refinery",
                "refinery_unit": "Boiler House 2",
                "location": "Feedwater Pump Area",
                "equipment_id": "B-102",
                "work_type": "Routine Operations",
                "department": "Operations",
                "description": "Insulation lagging loose on 2-inch low pressure steam trace line near walkway stairs.",
                "ppe_noncompliance": False,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-10",
                "site": "Duliajan Site",
                "refinery_unit": "Tank Farm A",
                "location": "Crude Tank TK-502",
                "equipment_id": "TK-502",
                "work_type": "Tank Gauging",
                "department": "Operations",
                "description": "Operator had opened tank hatch without grounding static bonding cable during thunderstorm. Abnormal risk had been reported repeatedly.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 1,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_CONDITION,
                "date": "2026-09-09",
                "site": "Digboi Refinery",
                "refinery_unit": "Hydrogen Unit",
                "location": "Compressor House B",
                "equipment_id": "C-301",
                "work_type": "Valve Overhaul",
                "department": "Contractor",
                "description": "Handrail paint chipped and rusted on secondary access ladder.",
                "ppe_noncompliance": False,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.HSE_REVIEW_PENDING
            }
        ]

        created_reports = []

        for r_data in sample_reports_data:
            existing_rep = db.query(SafetyReport).filter(SafetyReport.description == r_data["description"]).first()
            if not existing_rep:
                rep_num = generate_unique_report_number(db)
                rep = SafetyReport(
                    report_number=rep_num,
                    created_by=demo_user.id,
                    report_type=r_data["report_type"],
                    date=r_data["date"],
                    site=r_data["site"],
                    refinery_unit=r_data["refinery_unit"],
                    location=r_data["location"],
                    equipment_id=r_data["equipment_id"],
                    work_type=r_data["work_type"],
                    department=r_data["department"],
                    description=r_data["description"],
                    ppe_noncompliance=r_data["ppe_noncompliance"],
                    supervisor_negligence=r_data["supervisor_negligence"],
                    maintenance_delay_or_issue=r_data["maintenance_delay_or_issue"],
                    repeated_issue_ignored=r_data["repeated_issue_ignored"],
                    previous_similar_reports=r_data["previous_similar_reports"],
                    status=r_data["status"]
                )
                db.add(rep)
                db.commit()
                db.refresh(rep)
                created_reports.append(rep)
                print(f"--> Created Sample Report: {rep.report_number} ({rep.report_type.value})")

                # Trigger AI analysis for each report
                try:
                    analyze_safety_report(db, rep.id, demo_user)
                    print(f"    |- AI Analysis completed for {rep.report_number}")
                except Exception as ex:
                    print(f"    |- AI Analysis note for {rep.report_number}: {ex}")

                # If status is HSE_VALIDATED, add HSE Manager Review
                if r_data["status"] == ReportStatus.HSE_VALIDATED:
                    rev = HSEReview(
                        report_id=rep.id,
                        reviewer_id=manager_user.id,
                        ai_prediction_accepted=True,
                        hse_decision=HSEDecision.ACCEPTED,
                        review_comment="HSE Manager reviewed and confirmed SIF precursor risk classification."
                    )
                    db.add(rev)
                    db.commit()
            else:
                created_reports.append(existing_rep)

        # 3. Create Sample Interventions and Actions for High Potential SIF Reports
        if created_reports:
            for i, rep in enumerate(created_reports[:4]):
                existing_rec = db.query(InterventionRecommendation).filter(
                    InterventionRecommendation.report_id == rep.id
                ).first()

                if not existing_rec:
                    rec_num = f"REC-2026-{i+1:06d}"
                    rec = InterventionRecommendation(
                        recommendation_number=rec_num,
                        report_id=rep.id,
                        title=f"Enforce Strict LOTO & PPE Compliance in {rep.refinery_unit}",
                        category=InterventionCategory.PPE_CONTROL if i % 2 == 0 else InterventionCategory.ENERGY_ISOLATION,
                        recommendation_text=f"Mandatory pre-job briefing and dual-verification audit required for all {rep.work_type} tasks in {rep.location}.",
                        rationale="System identified recurring high potential SIF precursor indicators and PPE/Isolation noncompliance.",
                        priority_suggestion=InterventionPriority.HIGH,
                        evidence_summary=f"Report #{rep.report_number} flagged for {rep.description[:60]}...",
                        status=InterventionStatus.ACCEPTED if i % 2 == 0 else InterventionStatus.PENDING_HSE_VALIDATION
                    )
                    db.add(rec)
                    db.commit()
                    db.refresh(rec)
                    print(f"--> Created Intervention Recommendation: {rec.recommendation_number}")

                    # Create Action for accepted intervention
                    if rec.status == InterventionStatus.ACCEPTED:
                        act_num = f"ACT-2026-{i+1:06d}"
                        existing_act = db.query(Action).filter(Action.action_number == act_num).first()
                        if not existing_act:
                            act = Action(
                                action_number=act_num,
                                intervention_id=rec.id,
                                report_id=rep.id,
                                title=f"Audit & Replace Safety Locks at {rep.refinery_unit}",
                                description=f"Conduct field verification of all LOTO padlocks and personal protective gear for {rep.department} personnel.",
                                assigned_user_id=demo_user.id,
                                assigned_department=rep.department,
                                site=rep.site,
                                priority=ActionPriority.HIGH,
                                due_date="2026-10-15",
                                status=ActionStatus.IN_PROGRESS if i == 0 else ActionStatus.ASSIGNED,
                                created_by=manager_user.id
                            )
                            db.add(act)
                            db.commit()
                            print(f"    |- Created Action: {act.action_number}")

        print("\nDATABASE SEEDING COMPLETED SUCCESSFULLY.")
        print("Summary of Seeded Data:")
        print(f"  Total Reports: {db.query(SafetyReport).count()}")
        print(f"  HSE Users:     {db.query(User).count()}")
        print("\nDemo Credentials:")
        print("  HSE User:    user@oil.in    / Password123!")
        print("  HSE Manager: manager@oil.in / Password123!")
        print("  Admin:       admin@oil.in   / Password123!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
