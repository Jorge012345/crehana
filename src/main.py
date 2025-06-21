"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.infrastructure.database import init_database
from src.presentation.exception_handlers import add_exception_handlers
from src.presentation.routers import auth, tasks, task_lists

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Task Manager API")
    settings.setup_logging()
    
    # Initialize database
    db_manager = init_database(settings.database_url)
    await db_manager.create_tables()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Task Manager API")
    await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="A comprehensive task management API built with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(task_lists.router, prefix=settings.api_v1_str, tags=["task-lists"])
app.include_router(tasks.router, prefix=settings.api_v1_str, tags=["tasks"])


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "task-manager-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 