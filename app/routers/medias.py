from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.deps.auth import get_current_user, get_db
from app.models.media import Media

router = APIRouter(prefix="/api", tags=["medias"])
MEDIA_DIR = Path("media")


@router.post("/medias")
async def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    original_name = Path(file.filename or "upload").name
    dest = MEDIA_DIR / original_name
    i = 1
    while dest.exists():
        dest = MEDIA_DIR / f"{i}_{original_name}"
        i += 1
    content = await file.read()
    dest.write_bytes(content)
    m = Media(path=f"/media/{dest.name}", uploader_id=user.id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"result": True, "media_id": m.id}
