import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles
from app.core.database import get_db
from app.core.config import settings
from app.models.rehearsal import Rehearsal

router = APIRouter(prefix="/api/rehearsals", tags=["media"])

ALLOWED_EXTENSIONS = {".webm", ".wav", ".mp3", ".mp4", ".ogg", ".m4a"}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


@router.post("/{rehearsal_id}/audio")
async def upload_audio(
    rehearsal_id: int,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")

    ext = Path(audio.filename or "audio.webm").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    filename = f"rehearsal_{rehearsal_id}_{uuid.uuid4().hex}{ext}"
    file_path = settings.media_dir / filename

    # Stream file to disk
    size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await audio.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                await f.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large (max 200MB)")
            await f.write(chunk)

    rehearsal.audio_path = str(file_path)
    await db.commit()

    return {"rehearsal_id": rehearsal_id, "audio_path": filename, "size_bytes": size}
