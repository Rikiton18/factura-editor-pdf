import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .session_store import cleanup_expired_sessions
from .routers.upload import router as upload_router
from .routers.export import router as export_router
from .routers.demo import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_expired_sessions())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Invoice PDF Editor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Runs in ServerErrorMiddleware, outside CORSMiddleware, so the CORS header
    # must be added by hand. Without it the browser hides any 500 behind a
    # generic "Network Error".
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
        headers={"Access-Control-Allow-Origin": "*"},
    )


app.include_router(upload_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(demo_router, prefix="/api")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
