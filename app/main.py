import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routers.users import router as users_router
from app.routers.medias import router as medias_router
from app.routers.tweets import router as tweets_router
from app.db.session import SessionLocal
from app.seed import seed_demo_data

app = FastAPI(title="Microblog API", version="0.1.0")
app.include_router(users_router)
app.include_router(medias_router)
app.include_router(tweets_router)

logger = logging.getLogger(__name__)


def _error_payload(error_type: str, message: str) -> dict:
    return {"result": False, "error_type": error_type, "error_message": message}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload("http_error", detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = [f"{'.'.join(str(part) for part in error.get('loc', []))}: {error.get('msg')}" for error in exc.errors()]
    detail = "; ".join(messages) if messages else "validation error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload("validation_error", detail),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("internal_error", "internal server error"),
    )


if os.getenv("APP_SKIP_BOOTSTRAP") != "1":

    @app.on_event("startup")
    def seed_data() -> None:
        with SessionLocal() as db:
            seed_demo_data(db)


MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

DIST_DIR = Path("dist")
assets_dir = DIST_DIR / "assets"
index_path = DIST_DIR / "index.html"

if assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

for subdir in ("css", "js"):
    candidate = DIST_DIR / subdir
    if candidate.is_dir():
        app.mount(f"/{subdir}", StaticFiles(directory=candidate), name=f"dist-{subdir}")

if index_path.exists():

    @app.get("/{full_path:path}")
    async def spa(full_path: str, request: Request):
        return FileResponse(index_path)

else:

    @app.get("/{full_path:path}")
    async def spa_placeholder(full_path: str, request: Request):
        return {"result": True}
