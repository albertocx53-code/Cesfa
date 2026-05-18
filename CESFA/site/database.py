from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# BASE DIR
BASE_DIR = Path(__file__).resolve().parent


# DATABASE
DATABASE_URL = f"sqlite:///{BASE_DIR}/cesfa.db"


# ENGINE
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# SESSION
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# BASE MODEL
class Base(DeclarativeBase):
    pass


# GET DB
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()