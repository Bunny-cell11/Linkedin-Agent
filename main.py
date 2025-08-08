from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import logging
import redis
from database import UserProfile, ContentCalendar, init_db, SessionLocal
from config import Config
from linkedin_api import LinkedInAPI
from ai_agent import LinkedInAgent
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
        redis_client.set("industry_trends", json.dumps(["AI trends", "Cloud computing", "Digital transformation"]))
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        logger.info("Application is shutting down.")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

linkedin_api = LinkedInAPI(access_token=Config.LINKEDIN_ACCESS_TOKEN)
linkedin_agent = LinkedInAgent(openai_api_key=Config.OPENAI_API_KEY)

class UserProfileModel(BaseModel):
    user_id: str
    profile_data: Dict

class ContentGenerationRequest(BaseModel):
    user_id: str
    content_type: str = "text"
    industry: Optional[str] = None

class ScheduledPost(BaseModel):
    user_id: str
    content: str
    content_type: str
    schedule_time: datetime

class AnalyticsRequest(BaseModel):
    user_id: str
    post_id: str

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/analyze")
async def analyze_profile(profile_data: UserProfileModel, db: Session = Depends(get_db)):
    try:
        analysis_result = linkedin_agent.analyze_profile(profile_data.profile_data)
        user_profile = UserProfile(
            id=profile_data.user_id,
            bio=profile_data.profile_data.get("bio"),
            industry=profile_data.profile_data.get("industry"),
            skills=profile_data.profile_data.get("skills"),
            interests=profile_data.profile_data.get("interests"),
            sentiment_score=analysis_result["sentiment_score"],
            keywords=analysis_result["keywords"]
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        return {"status": "success", "user_profile": user_profile}
    except Exception as e:
        logger.error(f"Error analyzing profile: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/generate")
async def generate_content(request: ContentGenerationRequest, db: Session = Depends(get_db)):
    try:
        user_profile = db.query(UserProfile).filter(UserProfile.id == request.user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found. Please analyze first.")
        trends = json.loads(redis_client.get("industry_trends") or "[]")
        generated_content = linkedin_agent.generate_content(user_profile, request.content_type, trends)
        return {"status": "success", "content": generated_content}
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/schedule")
async def schedule_post(post_data: ScheduledPost, db: Session = Depends(get_db)):
    try:
        new_post = ContentCalendar(
            user_id=post_data.user_id,
            content=post_data.content,
            content_type=post_data.content_type,
            schedule_time=post_data.schedule_time
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        post_result = linkedin_api.post_to_linkedin(post_data.user_id, post_data.content, post_data.content_type)
        return {"status": "success", "message": "Post scheduled successfully", "post_id": post_result.get("post_id")}
    except Exception as e:
        logger.error(f"Error scheduling post: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/analytics")
async def get_analytics(request: AnalyticsRequest, db: Session = Depends(get_db)):
    try:
        analytics = linkedin_api.get_post_analytics(request.post_id)
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/calendar")
async def get_calendar(user_id: str, db: Session = Depends(get_db)):
    try:
        posts = db.query(ContentCalendar).filter(ContentCalendar.user_id == user_id).all()
        return {"status": "success", "calendar": posts}
    except Exception as e:
        logger.error(f"Error fetching calendar: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
