from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(String, primary_key=True)
    bio = Column(String)
    industry = Column(String)
    skills = Column(JSON)
    interests = Column(JSON)
    sentiment_score = Column(Float)
    keywords = Column(JSON)

class ContentCalendar(Base):
    __tablename__ = "content_calendar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    content = Column(String)
    content_type = Column(String)
    schedule_time = Column(DateTime)

def init_db():
    engine = create_engine(Config.DATABASE_URL)
    Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine(Config.DATABASE_URL))