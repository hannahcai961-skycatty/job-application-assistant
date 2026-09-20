from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


class NoCacheStatic(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response

from .config import FRONTEND_DIR, settings
from .routers.ai_settings import router as ai_settings_router
from .routers.resumes_jobs import jobs_router

app = FastAPI(
    title="Job Application Assistant",
    description="秋招岗位评估与投递记录",
    version="0.3.0",
)

app.include_router(jobs_router)
app.include_router(ai_settings_router)

static_dir = FRONTEND_DIR
if static_dir.exists():
    app.mount("/static", NoCacheStatic(directory=static_dir), name="static")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise RuntimeError("frontend/index.html not found")
    return FileResponse(index_path, headers={"Cache-Control": "no-cache"})


def main() -> None:
    import uvicorn

    uvicorn.run(
        "src.backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
