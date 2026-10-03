import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
