from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

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

from app.api.v1 import streams
from app.api.v1 import sessions
from app.api.v1 import defects

app.include_router(streams.router, prefix="/api/v1/streams", tags=["streams"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
from fastapi.staticfiles import StaticFiles
import os

app.include_router(defects.router, prefix="/api/v1/defects", tags=["defects"])
from app.api.v1 import settings
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])

# Create media dir if not exists
os.makedirs("data/media", exist_ok=True)
app.mount("/media", StaticFiles(directory="data/media"), name="media")

@app.get("/")
def root():
    return {"message": "AI Metal Sheet Monitor API is running"}
