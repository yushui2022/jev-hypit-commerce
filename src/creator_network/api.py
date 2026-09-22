import hmac
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .media import media_path
from .models import CatalogImport, MatchRequest, RenderRequest, ReviewRequest
from .rendering import approved_snapshot
from .store import Conflict, Store
from .worker import Worker


def create_app(settings=None):
    settings = settings or Settings()
    store = Store(settings.database)
    worker = Worker(settings, store)

    @asynccontextmanager
    async def lifespan(app):
        thread = None
        if settings.worker_enabled:
            thread = threading.Thread(target=worker.run, daemon=True)
            thread.start()
        yield
        worker.stop.set()
        if thread:
            thread.join(timeout=2)

    app = FastAPI(title="Jev Creator Network", version="0.4.0", lifespan=lifespan)
    app.state.store = store
    app.state.worker = worker

    @app.middleware("http")
    async def authenticate(request: Request, call_next):
        if request.url.path.startswith("/api/") and settings.api_token:  # noqa: SIM102
            if not hmac.compare_digest(
                request.headers.get("authorization", ""), "Bearer " + settings.api_token
            ):
                return JSONResponse({"detail": "API token required"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "Resource not found"}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "version": "0.4.0",
            "retrieval": settings.retrieval,
            "jev_configured": bool(settings.jev_key),
            "worker": "embedded" if settings.worker_enabled else "external",
        }

    @app.get("/api/catalog")
    def catalog(kind: str | None = None):
        if kind not in (None, "product", "creator"):
            raise ValueError("kind must be product or creator")
        return {"items": store.items(kind)}

    @app.post("/api/catalog")
    def import_catalog(body: CatalogImport):
        store.upsert([x.model_dump() for x in body.items])
        return {"imported": len(body.items)}

    def key(value):
        if value is not None and (not value.strip() or len(value) > 128):
            raise ValueError("Idempotency-Key must contain 1–128 characters")
        return value

    @app.post("/api/matches", status_code=202)
    def match(body: MatchRequest, idempotency_key: str | None = Header(default=None)):
        p = store.item(body.product_id)
        if p["kind"] != "product" or not p["active"]:
            raise ValueError("Product is unavailable")
        return store.enqueue("match", body.model_dump(), key(idempotency_key))

    @app.get("/api/jobs")
    def jobs():
        return {"jobs": store.jobs()}

    @app.get("/api/jobs/{id}")
    def job(id: str):
        return store.job(id)

    @app.get("/api/jobs/{id}/events")
    def events(id: str):
        return {"events": store.events(id)}

    @app.post("/api/jobs/{id}/retry")
    def retry(id: str):
        return store.retry(id)

    @app.post("/api/matches/{id}/review")
    def review(id: str, body: ReviewRequest):
        return store.review(id, body.action, body.creator_id, body.note)

    @app.post("/api/renders", status_code=202)
    def rendering(
        body: RenderRequest, idempotency_key: str | None = Header(default=None)
    ):
        return store.enqueue(
            "render", approved_snapshot(store, body.match_job_id), key(idempotency_key)
        )

    @app.get("/api/jobs/{id}/files/{name}")
    def artifact(id: str, name: str):
        job = store.job(id)
        if (
            job["kind"] != "render"
            or job["status"] != "completed"
            or name not in ("guanyi.mp4", "yeadon.mp4")
        ):
            raise KeyError(id)
        path = settings.data / "jobs" / job["id"] / name
        if not path.is_file():
            raise KeyError(name)
        return FileResponse(path, media_type="video/mp4", filename=name)

    @app.get("/media/{path:path}")
    def media(path: str):
        return FileResponse(media_path(settings.root, path))

    app.mount(
        "/",
        StaticFiles(directory=settings.root / "apps/workbench", html=True),
        name="workbench",
    )
    return app
