"""Misc helpers - hardened against B605 OS Command Injection (CWE-78)."""
import os
import shutil
import uuid
from pathlib import Path

# Allowlist of file extensions we will store from uploads
_ALLOWED_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt',
    '.csv', '.doc', '.docx', '.xls', '.xlsx', '.zip',
}


def store_uploaded_file(title, uploaded_file):
    """Persist an uploaded temp file safely.

    SECURITY: previously used os.system("mv ...") with the user-supplied
    title concatenated in - allowed shell metacharacter injection. We now:
      * strip any path components from the title (prevents path traversal)
      * validate the file extension against an allowlist
      * append a random suffix to avoid collisions / overwrite attacks
      * use shutil.move which never spawns a shell
    """
    upload_dir = Path(__file__).resolve().parent / 'static' / 'taskManager' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Path(...).name strips any "../" or absolute path traversal attempts
    safe_name = Path(title or '').name
    if not safe_name:
        safe_name = 'upload'

    suffix = Path(safe_name).suffix.lower()
    if suffix not in _ALLOWED_EXTS:
        suffix = '.bin'
    stem = Path(safe_name).stem[:80] or 'upload'

    final_name = f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"
    dest = upload_dir / final_name

    # No shell - shutil.move handles cross-filesystem safely.
    shutil.move(uploaded_file.temporary_file_path(), dest)

    return f'/static/taskManager/uploads/{final_name}'
