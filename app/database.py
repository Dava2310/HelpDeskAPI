from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app import models # noqa: F401
from app.config import get_settings

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    
engine = create_engine(settings.database_url, connect_args=connect_args)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]