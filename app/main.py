from fastapi import FastAPI

from contextlib import asynccontextmanager

from app.routers.test_router import router as test_router
from app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# App definition
app = FastAPI(lifespan=lifespan)

# Inclusion of routers
app.include_router(test_router)

# Health endpoint
@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Hello World"}
