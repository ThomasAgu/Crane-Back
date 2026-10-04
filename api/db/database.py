''' This file is used to create a database connection and session for the FastAPI application. '''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from api.config.constants import SQLITE_FILE


engine = create_engine(SQLITE_FILE, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_db_and_tables():
    ''' Create database and tables '''
    Base.metadata.create_all(bind=engine)


def get_db():
    ''' Get database session '''
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.close()
