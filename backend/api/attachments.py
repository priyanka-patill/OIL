from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import APIResponse
from backend.security.dependencies import get_current_active_user
from backend.services import attachment_service

router = APIRouter(prefix="/attachments", tags=["Attachments"])

@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Securely streams an authorized file attachment for download."""
    attachment, file_path = attachment_service.get_attachment_for_access(db, attachment_id, current_user)
    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename,
        content_disposition_type="attachment"
    )

@router.get("/{attachment_id}/preview")
def preview_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Securely streams an authorized file attachment for inline browser preview (images / PDF)."""
    attachment, file_path = attachment_service.get_attachment_for_access(db, attachment_id, current_user)
    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename,
        content_disposition_type="inline"
    )

@router.delete("/{attachment_id}", response_model=APIResponse[bool])
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deletes an authorized attachment and its stored physical file."""
    success = attachment_service.delete_attachment(db, attachment_id, current_user)
    return APIResponse(
        success=True,
        message="Attachment deleted successfully.",
        data=success
    )
