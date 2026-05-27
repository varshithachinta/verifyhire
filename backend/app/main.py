from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.database import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create directories and DB tables."""
    logger.info(f"Starting {settings.APP_NAME}...")

    # Create upload directories
    for directory in [settings.videos_dir, settings.audio_dir, settings.faces_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {directory}")

    # Create DB tables (dev mode — use Alembic in production)
    await create_tables()
    logger.info("Database tables created/verified")

    yield

    logger.info(f"{settings.APP_NAME} shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Verified Video Resume Platform for Blue-Collar Workers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register all routers
from app.routes import auth, worker, employer, videos, matches, admin

app.include_router(auth.router)
app.include_router(worker.router)
app.include_router(employer.router)
app.include_router(videos.router)
app.include_router(matches.router)
app.include_router(admin.router)

# Health check
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }


# Serve uploaded files (dev only)
uploads_path = Path(settings.UPLOAD_DIR)
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")
