import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.jobs.expiration_worker import start_expiration_worker

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("connectED")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing connectED backend...")
    worker_task = None
    try:
        await connect_to_mongo()
        # Start persistent 48h deadline expiration worker in background
        worker_task = asyncio.create_task(start_expiration_worker(poll_interval_seconds=60))
    except Exception as e:
        logger.warning("MongoDB startup initialization deferred or error (expected in some test runs): %s", e)

    yield

    # Shutdown actions
    logger.info("Shutting down connectED backend...")
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    await close_mongo_connection()

app = FastAPI(
    title="connectED API",
    description="AI-powered professional networking platform connecting students, alumni, faculty, recruiters, and startup founders.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
origins = list(set(settings.ALLOWED_ORIGINS + [settings.FRONTEND_ORIGIN]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom standard error exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount mandatory v1 API endpoints
app.include_router(api_router)

# Health endpoint (separate from mandatory business endpoints)
@app.get("/health", tags=["System Health"])
async def health_check():
    return {"status": "ok", "service": "connectED-backend", "version": "1.0.0"}
