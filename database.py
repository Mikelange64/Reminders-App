from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
from config import settings

load_dotenv()

# Default back to sqlite ONLY if the .env variable is missing
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# No 'check_same_thread' because we are on Postgres now!
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db