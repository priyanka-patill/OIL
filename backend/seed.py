import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.database.database import SessionLocal, init_db
from backend.database.models import User, UserRole, SafetyReport, ReportType, ReportStatus
from backend.security.auth import hash_password
from backend.services.report_service import generate_unique_report_number

def seed_database():
    print("==================================================")
    print("SEEDING DEVELOPMENT DATABASE")
    print("==================================================")
    
    init_db()
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

        # 2. Create Sample Reports
        demo_user = created_users["user@oil.in"]
        
        sample_reports_data = [
            {
                "report_type": ReportType.NEAR_MISS,
                "date": "2026-09-15",
                "site": "Digboi Refinery",
                "refinery_unit": "Hydrogen Unit",
                "location": "Compressor House B",
                "equipment_id": "P-305",
                "work_type": "Preventive Maintenance",
                "department": "Operations",
                "description": "Worker entered process area without safety helmet and bypassed mandatory isolation locks during pump overhaul.",
                "ppe_noncompliance": True,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 2,
                "status": ReportStatus.SUBMITTED
            },
            {
                "report_type": ReportType.UNSAFE_ACT,
                "date": "2026-09-14",
                "site": "Duliajan Site",
                "refinery_unit": "HCU",
                "location": "Scaffold Deck 4",
                "equipment_id": "SCAF-102",
                "work_type": "Hot Work",
                "department": "Contractor",
                "description": "Welder worked at height without connecting safety harness near high pressure hydrocarbon line.",
                "ppe_noncompliance": True,
                "supervisor_negligence": True,
                "maintenance_delay_or_issue": False,
                "repeated_issue_ignored": True,
                "previous_similar_reports": 1,
                "status": ReportStatus.HSE_REVIEW_PENDING
            },
            {
                "report_type": ReportType.UNSAFE_CONDITION,
                "date": "2026-09-10",
                "site": "Digboi Refinery",
                "refinery_unit": "Crude Unit",
                "location": "Pipeline Rack",
                "equipment_id": "V-101",
                "work_type": "Inspection",
                "department": "Maintenance",
                "description": "Minor oil weeping observed from valve gland packing during routine operator rounds.",
                "ppe_noncompliance": False,
                "supervisor_negligence": False,
                "maintenance_delay_or_issue": True,
                "repeated_issue_ignored": False,
                "previous_similar_reports": 0,
                "status": ReportStatus.CLOSED
            }
        ]

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
                print(f"--> Created Sample Report: {rep.report_number} ({rep.report_type.value})")

        print("\nDATABASE SEEDING COMPLETED SUCCESSFULLY.")
        print("\nDemo Credentials:")
        print("  HSE User:    user@oil.in    / Password123!")
        print("  HSE Manager: manager@oil.in / Password123!")
        print("  Admin:       admin@oil.in   / Password123!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
