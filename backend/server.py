from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import base64
import re


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get API key from environment
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY', '')

# Define Models
class PlantAnalysisRequest(BaseModel):
    image_base64: str
    
class PlantAnalysisResponse(BaseModel):
    id: str
    health_status: str
    issues: List[str]
    remedies: List[str]
    detailed_analysis: str
    image_base64: str
    timestamp: datetime

class ScanHistory(BaseModel):
    id: str
    health_status: str
    issues: List[str]
    remedies: List[str]
    detailed_analysis: str
    image_base64: str
    timestamp: datetime


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Plant Health Scanner API"}


@api_router.post("/analyze-plant", response_model=PlantAnalysisResponse)
async def analyze_plant(request: PlantAnalysisRequest):
    try:
        # Validate base64 image
        if not request.image_base64:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Remove data URI prefix if present
        image_data = request.image_base64
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        # Create a unique session ID for this analysis
        session_id = str(uuid.uuid4())
        
        # Initialize LlmChat with OpenAI GPT-5.2
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="You are an expert botanist and plant pathologist. Analyze plant images and provide detailed health assessments with specific remedies."
        ).with_model("openai", "gpt-5.2")
        
        # Create image content
        image_content = ImageContent(image_base64=image_data)
        
        # Create user message with image
        user_message = UserMessage(
            text="""Analyze this plant/leaf image and provide:
1. Overall health status (Healthy/Minor Issues/Moderate Issues/Severe Issues/Critical)
2. List of specific issues or diseases identified
3. Detailed remedies and treatment recommendations
4. Care tips and preventive measures

Provide the response in the following format:
HEALTH STATUS: [status]
ISSUES:
- [issue 1]
- [issue 2]
REMEDIES:
- [remedy 1]
- [remedy 2]
DETAILED ANALYSIS:
[Detailed analysis text]""",
            file_contents=[image_content]
        )
        
        # Send message and get response
        response = await chat.send_message(user_message)
        
        # Parse the response
        health_status = "Unknown"
        issues = []
        remedies = []
        detailed_analysis = response
        
        # Extract health status
        status_match = re.search(r'HEALTH STATUS:\s*(.+)', response, re.IGNORECASE)
        if status_match:
            health_status = status_match.group(1).strip()
        
        # Extract issues
        issues_section = re.search(r'ISSUES:\s*(.+?)(?=REMEDIES:|DETAILED ANALYSIS:|$)', response, re.IGNORECASE | re.DOTALL)
        if issues_section:
            issues_text = issues_section.group(1)
            issues = [line.strip('- ').strip() for line in issues_text.split('\n') if line.strip().startswith('-')]
        
        # Extract remedies
        remedies_section = re.search(r'REMEDIES:\s*(.+?)(?=DETAILED ANALYSIS:|$)', response, re.IGNORECASE | re.DOTALL)
        if remedies_section:
            remedies_text = remedies_section.group(1)
            remedies = [line.strip('- ').strip() for line in remedies_text.split('\n') if line.strip().startswith('-')]
        
        # Extract detailed analysis
        analysis_section = re.search(r'DETAILED ANALYSIS:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        if analysis_section:
            detailed_analysis = analysis_section.group(1).strip()
        
        # Create response object
        analysis_id = str(uuid.uuid4())
        result = PlantAnalysisResponse(
            id=analysis_id,
            health_status=health_status,
            issues=issues if issues else ["No specific issues detected"],
            remedies=remedies if remedies else ["Continue regular plant care"],
            detailed_analysis=detailed_analysis,
            image_base64=request.image_base64,
            timestamp=datetime.utcnow()
        )
        
        # Store in database
        await db.plant_scans.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing plant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing plant: {str(e)}")


@api_router.get("/scan-history", response_model=List[ScanHistory])
async def get_scan_history():
    try:
        scans = await db.plant_scans.find().sort("timestamp", -1).limit(20).to_list(20)
        return [ScanHistory(**scan) for scan in scans]
    except Exception as e:
        logger.error(f"Error fetching scan history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
