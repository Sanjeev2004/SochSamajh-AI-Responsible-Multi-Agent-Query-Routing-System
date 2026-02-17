from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
from datetime import datetime

router = APIRouter()

FEEDBACK_FILE = "data/feedback.json"

# Ensure data directory exists
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: str  # "up" or "down"
    request_id: str

@router.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": feedback.request_id,
        "query": feedback.query,
        "response": feedback.response,
        "rating": feedback.rating
    }
    
    # Simple append to JSON list (not efficient for production, but good for research prototype)
    data = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
            
    data.append(entry)
    
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
    return {"status": "success", "message": "Feedback received"}
