# LinkedIn Personal Branding AI Agent
Automates LinkedIn content creation, scheduling, and analytics.

## Setup
1. Install dependencies: `pip3 install -r requirements.txt`
2. Ensure `templates/dashboard.html` exists
3. Run: `python3 linkedin_branding_agent.py`

## API Endpoints
- `POST /api/analyze`: Analyze user profile
- `POST /api/generate`: Generate content
- `POST /api/schedule`: Schedule posts
- `GET /api/analytics/<user_id>`: View analytics

## Deployment
- Deploy to Heroku: `heroku create`, `git push heroku main`
- Set env vars: `heroku config:set LINKEDIN_API_KEY=placeholder LINKEDIN_ACCESS_TOKEN=placeholder`
