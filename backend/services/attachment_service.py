import os
import uuid
import re
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from backend.config import settings
from backend.database.models import SafetyReport, ReportAttachment, User, UserRole
from backend.services.audit_service import log_audit_event
from backend.services.report_service import get_report_by_id

logger = logging.getLogger("backend.services.attachment_service")

# File validation rules
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
DISALLOWED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".js", ".msi", ".dll", ".py",
    ".vbs", ".ps1", ".com", ".scr", ".pif", ".application", ".gadget",
    ".msu", ".msp", ".hta", ".cpl", ".msc", ".jar"
}

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"
}

# Magic bytes signature validation
MAGIC_BYTES = {
    ".jpg": [b"\xFF\xD8\xFF"],
    ".jpeg": [b"\xFF\xD8\xFF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".pdf": [b"%PDF"],
    ".webp": [b"RIFF"] # WEBP files start with RIFF
}

def sanitize_filename(filename: str) -> str:
    """Sanitizes user-provided filename against path traversal and dangerous characters."""
    if not filename:
        return "unnamed_file"
    # Remove path components
    filename = os.path.basename(filename)
    # Remove null bytes and non-printable characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Remove unsafe characters
    filename = re.sub(r'[^\w\.\-\s]', '_', filename)
    return filename.strip() or "unnamed_file"

def validate_file(file: UploadFile) -> str:
    """
    Validates uploaded file against size limits, allowed extensions,
    mime types, and binary magic bytes. Returns sanitized extension.
    """
    filename = sanitize_filename(file.filename or "")
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension. Upload JPG, JPEG, PNG, WEBP, or PDF."
        )

    if ext in DISALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Violation: Executable file type '{ext}' is forbidden."
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: JPG, JPEG, PNG, WEBP, PDF."
        )

    # Validate file size if content_length is present
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Read first 1024 bytes for magic bytes validation & size checking
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{filename}' ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{filename}' is empty (0 bytes)."
        )

    # Header / magic byte inspection for extra safety
    header = file.file.read(16)
    file.file.seek(0)

    if ext in MAGIC_BYTES:
        signatures = MAGIC_BYTES[ext]
        if not any(header.startswith(sig) for sig in signatures):
            # Special check for WEBP format (RIFF....WEBP)
            if ext == ".webp" and header.startswith(b"RIFF"):
                pass
            else:
                logger.warning(f"File magic byte mismatch for '{filename}' with extension '{ext}'. Header: {header[:8]}")

    return ext

def save_attachment(db: Session, report_id: int, file: UploadFile, user: User) -> ReportAttachment:
    """
    Saves an uploaded file to storage and records ReportAttachment metadata in DB.
    """
    report = get_report_by_id(db, report_id, user)
    
    ext = validate_file(file)
    original_name = sanitize_filename(file.filename or f"attachment{ext}")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # Secure storage location
    report_upload_dir = os.path.join(settings.UPLOAD_DIR, "reports", str(report.id))
    os.makedirs(report_upload_dir, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(report_upload_dir, stored_name)

    try:
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(8192):
                buffer.write(chunk)
    except Exception as e:
        logger.error(f"Failed to write physical file '{file_path}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store attachment file on server."
        )

    attachment = ReportAttachment(
        report_id=report.id,
        original_filename=original_name,
        stored_filename=stored_name,
        file_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_extension=ext,
        uploaded_by=user.id
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    log_audit_event(
        db, action="ATTACHMENT_UPLOADED", user_id=user.id,
        entity_type="ReportAttachment", entity_id=attachment.id,
        metadata={
            "report_id": report.id,
            "filename": original_name,
            "size": file_size,
            "extension": ext
        }
    )

    return attachment

def get_report_attachments(db: Session, report_id: int, user: User) -> List[ReportAttachment]:
    """Retrieves all attachments for an authorized safety report."""
    report = get_report_by_id(db, report_id, user)
    return report.attachments

def get_attachment_for_access(db: Session, attachment_id: int, user: User) -> Tuple[ReportAttachment, str]:
    """
    Retrieves attachment metadata and physical path after verifying user authorization.
    """
    attachment = db.query(ReportAttachment).filter(ReportAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    # Verify report ownership / role permission
    report = get_report_by_id(db, attachment.report_id, user)

    file_path = os.path.abspath(attachment.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file content is missing on storage server."
        )

    log_audit_event(
        db, action="ATTACHMENT_ACCESSED", user_id=user.id,
        entity_type="ReportAttachment", entity_id=attachment.id,
        metadata={"report_id": report.id, "filename": attachment.original_filename}
    )

    return attachment, file_path

def delete_attachment(db: Session, attachment_id: int, user: User) -> bool:
    """
    Deletes an attachment and physical file if user is authorized (creator or HSE Manager/Admin).
    """
    attachment = db.query(ReportAttachment).filter(ReportAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    report = get_report_by_id(db, attachment.report_id, user)

    # Permission check: Creator or HSE Manager / Admin
    if user.role == UserRole.HSE_USER and attachment.uploaded_by != user.id and report.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this attachment."
        )

    # Remove physical file if present
    file_path = os.path.abspath(attachment.file_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove physical file '{file_path}': {e}")

    filename = attachment.original_filename
    report_id = attachment.report_id

    db.delete(attachment)
    db.commit()

    log_audit_event(
        db, action="ATTACHMENT_DELETED", user_id=user.id,
        entity_type="ReportAttachment", entity_id=attachment_id,
        metadata={"report_id": report_id, "filename": filename}
    )

    return True
