from fastapi import FastAPI
from app.routers.test_router import router as test_router

from typing import Annotated
from fastapi import Depends
from app.config import Settings, get_settings

# App definition
app = FastAPI()

# Inclusion of routers
app.include_router(test_router)

# Health endpoint
@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Hello World"}

# Environment test
@app.get("/info")
def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {"env": settings.environment}