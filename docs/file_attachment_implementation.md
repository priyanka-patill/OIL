# File Attachment System Architecture & Implementation

## 1. Overview
The File Attachment System provides end-to-end support for uploading, validating, storing, retrieving, previewing, and deleting supporting photos, permits, and documents associated with Safety Reports in the Oil India Limited HSE Safety Intelligence Platform.

## 2. Supported File Types & Security Rules
- **Allowed Extensions**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`
- **Allowed MIME Types**: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`
- **Maximum File Size**: 10 MB per file (configurable via `MAX_FILE_SIZE_MB` in `.env`)
- **Forbidden Executable Extension Blacklist**: `.exe`, `.bat`, `.cmd`, `.sh`, `.js`, `.msi`, `.dll`, `.py`, `.vbs`, `.ps1`, etc.
- **Magic Bytes Validation**: Evaluates initial file bytes (`\xFF\xD8\xFF` for JPEG, `\x89PNG` for PNG, `%PDF` for PDF) to prevent MIME spoofing.
- **Filename Sanitization**: Removes path traversal sequences (`../`, `\`), null bytes, and non-printable characters.
- **Storage Strategy**: Storage files are saved under `uploads/reports/<report_id>/<uuid>.<ext>` to avoid filename collisions and public directory exposure.

## 3. Database Schema
### `report_attachments`
| Field | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment primary key |
| `report_id` | Integer (FK) | Foreign key to `safety_reports.id` |
| `original_filename` | String(255) | Original sanitized user filename |
| `stored_filename` | String(255) | Server UUID filename (`<uuid>.<ext>`) |
| `file_path` | String(500) | Server physical disk path |
| `mime_type` | String(100) | MIME type |
| `file_size` | Integer | Byte count |
| `file_extension` | String(20) | File extension |
| `uploaded_by` | Integer (FK) | Foreign key to `users.id` |
| `created_at` | DateTime | Upload timestamp (UTC) |

## 4. API Specification
- `POST /api/reports/{report_id}/attachments`
  - Multipart file upload for one or multiple files.
  - Requires JWT authentication and report authorization.
- `GET /api/reports/{report_id}/attachments`
  - Returns list of `ReportAttachmentResponse` metadata for authorized report.
- `GET /api/attachments/{attachment_id}/download`
  - Streams physical file with `Content-Disposition: attachment; filename="..."`.
- `GET /api/attachments/{attachment_id}/preview`
  - Streams physical file with `Content-Disposition: inline` for image/PDF browser rendering.
- `DELETE /api/attachments/{attachment_id}`
  - Deletes physical file and database metadata. Restricted to creator or HSE Manager / Admin.

## 5. Frontend Components
- **`FileUploadDropzone.jsx`**: Interactive drag-and-drop / click-to-browse component embedded in `ReportNewPage.jsx` with instant client-side validation for file types and size limits.
- **`AttachmentsSection.jsx`**: Displays attached photos and permits on `ReportDetailPage.jsx` with file type icons, size metadata, modal image previewer, PDF open trigger, download links, and optional delete action.

## 6. Audit Logging
Every file upload, access, and deletion event generates an entry in `audit_logs` table (`ATTACHMENT_UPLOADED`, `ATTACHMENT_ACCESSED`, `ATTACHMENT_DELETED`).
