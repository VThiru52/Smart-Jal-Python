from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

from fastapi.staticfiles import StaticFiles
import os

# Mount static files to serve generated images
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

from fastapi.responses import HTMLResponse
import os

@app.get("/console", response_class=HTMLResponse)
async def get_console():
    """Serve the premium API Control Center"""
    console_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api_console.html")
    with open(console_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/")
async def root():
    return {"message": "Welcome to Smart Jal AI Backend API", "status": "running", "console": "/console"}
