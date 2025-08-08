from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import logging
from config import Config
from database import UserProfile, ContentCalendar, init_db, SessionLocal
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Dummy LinkedInAgent class (replace with actual LangChain/OpenAI implementation)
class LinkedInAgent:
    def __init__(self, openai_api_key: str):
        # Initialize your AI models here
        if not openai_api_key:
            raise ValueError("OpenAI API key is not set.")
        self.openai_api_key = openai_api_key
        # Example of where to initialize LangChain chains, etc.
        # self.llm = OpenAI(api_key=self.openai_api_key)
    def analyze_profile(self, profile_data: dict):
        # Dummy analysis
        bio = profile_data.get("bio", "")
        sentiment_score = 0
        keywords = ["python", "ai", "machine learning"]
        return {"sentiment_score": sentiment_score, "keywords": keywords}
    def generate_content(self, user_profile: UserProfile):
        # Dummy content generation
        content = f"An interesting thought about {user_profile.industry}..."
        hashtags = ["#AI", "#LinkedIn", "#Tech"]
        return {"content": content, "hashtags": hashtags}
    def post_to_linkedin(self, user_id: str, content: str, content_type: str):
        # Dummy post to LinkedIn
        logger.info(f"Posting to LinkedIn for user {user_id}: {content[:30]}...")
        return {"status": "published", "post_id": "dummy_post_id"}
# Initialize the agent
linkedin_agent = LinkedInAgent(openai_api_key=Config.OPENAI_API_KEY)
# --- API Models for Pydantic validation ---
class UserProfileModel(BaseModel):
    user_id: str
    profile_data: dict
class ContentGenerationRequest(BaseModel):
    user_id: str
    content_type: str = "text"
class ScheduledPost(BaseModel):
    user_id: str
    content: str
    content_type: str
    schedule_time: datetime
# --- API Endpoints ---
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
@app.post("/api/analyze")
def analyze_profile_endpoint(profile_data: UserProfileModel, db: Session = Depends(get_db)):
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
def generate_content_endpoint(request: ContentGenerationRequest, db: Session = Depends(get_db)):
    user_profile = db.query(UserProfile).filter(UserProfile.id == request.user_id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please analyze first.")
    generated_content = linkedin_agent.generate_content(user_profile)
    return {"status": "success", "content": generated_content}
@app.post("/api/schedule")
def schedule_post_endpoint(post_data: ScheduledPost, db: Session = Depends(get_db)):
    # This is a simplified scheduling; a real-world app would use a background scheduler like APScheduler
    new_post = ContentCalendar(
        user_id=post_data.user_id,
        content=post_data.content,
        content_type=post_data.content_type,
        schedule_time=post_data.schedule_time
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    # In a real app, this would be queued by a background worker
    # For a simple demo, you might just call the post_to_linkedin function immediately
    return {"status": "success", "message": "Post scheduled successfully."}
# --- Database Initialization on startup ---
@app.on_event("startup")
async def startup_event():
    # Your startup logic here
    print("Initializing resources...")
    # Example: Connect to a database
    app = FastAPI(lifespan=lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    init_db()
    logger.info("Database tables initialized successfully.")
    yield # This yields control to the application
    # This code runs on shutdown (e.g., for cleanup)
    logger.info("Application is shutting down.")

# Update your FastAPI app instance to use the lifespan manager
app = FastAPI(lifespan=lifespan)
@app.get("/predict")
async def predict(x: float):
    result = ml_models["answer_to_everything"](x)
    return {"result": result}

