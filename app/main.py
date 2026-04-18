"""
Intelligent Healthcare Ecosystem - Neurology Focus
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import mri, prediction, decision, resources
from database.connection import init_db
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    logger.info("🧠 Starting Neuro Health Ecosystem...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("🛑 Shutting down Neuro Health Ecosystem...")


app = FastAPI(
    title="Intelligent Healthcare Ecosystem (Neurology)",
    description="AI-powered brain tumor detection, risk classification, and resource allocation system.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins (works for any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(mri.router,        prefix="/api/v1", tags=["MRI Upload"])
app.include_router(prediction.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(decision.router,   prefix="/api/v1", tags=["Decision Engine"])
app.include_router(resources.router,  prefix="/api/v1", tags=["Resource Allocation"])


@app.get("/", tags=["Health Check"])
async def root():
    return {
        "system": "Intelligent Healthcare Ecosystem (Neurology)",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/v1/upload-mri",
            "GET  /api/v1/prediction/{scan_id}",
            "GET  /api/v1/decision/{scan_id}",
            "GET  /api/v1/resources",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)