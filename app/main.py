from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers.users import router as users_router
from app.routers.medias import router as medias_router
from app.routers.tweets import router as tweets_router

app = FastAPI(title="Microblog API", version="0.1.0")
app.include_router(users_router)
app.include_router(medias_router)
app.include_router(tweets_router)

app.mount("/media", StaticFiles(directory="media"), name="media")

DIST_DIR = Path("dist")
assets_dir = DIST_DIR / "assets"
index_path = DIST_DIR / "index.html"

if assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

if index_path.exists():

    @app.get("/{full_path:path}")
    async def spa(full_path: str, request: Request):
        return FileResponse(index_path)
else:

    @app.get("/{full_path:path}")
    async def spa_placeholder(full_path: str, request: Request):
        return {"result": True}
