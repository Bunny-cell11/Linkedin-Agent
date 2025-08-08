from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from typing import List, Dict
from database import UserProfile

logger = logging.getLogger(__name__)

class LinkedInAgent:
    def __init__(self, openai_api_key: str):
        if not openai_api_key:
            raise ValueError("OpenAI API key is not set.")
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key, temperature=0.7)

    def analyze_profile(self, profile_data: Dict) -> Dict:
        try:
            prompt = PromptTemplate(
                input_variables=["bio", "industry", "skills", "interests"],
                template="Analyze this LinkedIn profile: Bio: {bio}, Industry: {industry}, Skills: {skills}, Interests: {interests}. Return a JSON object with sentiment_score (0-1) and keywords (list)."
            )
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.run(
                bio=profile_data.get("bio", ""),
                industry=profile_data.get("industry", ""),
                skills=profile_data.get("skills", []),
                interests=profile_data.get("interests", [])
            )
            return eval(result)  # Assuming JSON string output
        except Exception as e:
            logger.error(f"Error analyzing profile: {e}")
            return {"sentiment_score": 0, "keywords": []}

    def generate_content(self, user_profile: UserProfile, content_type: str, trends: List[str]) -> Dict:
        try:
            prompt = PromptTemplate(
                input_variables=["industry", "bio", "skills", "trends", "content_type"],
                template="Generate a LinkedIn {content_type} post for a user in {industry} with bio: {bio}, skills: {skills}. Incorporate trends: {trends}. Keep it under 1300 characters, professional, engaging, with 4-6 hashtags and a call-to-action."
            )
            chain = LLMChain(llm=self.llm, prompt=prompt)
            content = chain.run(
                industry=user_profile.industry,
                bio=user_profile.bio,
                skills=user_profile.skills,
                trends=trends,
                content_type=content_type
            )
            return {"content": content, "hashtags": ["#LinkedIn", "#PersonalBranding", f"#{user_profile.industry.replace(' ', '')}"]}
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {"content": "", "hashtags": []}