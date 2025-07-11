from fastapi import APIRouter
from app.api.v1.endpoints import research

api_router = APIRouter()

# Include research endpoints
api_router.include_router(
    research.router, 
    prefix="/research", 
    tags=["research"]
)

# Add a test endpoint for the API
@api_router.get("/test")
async def test_api():
    """Test endpoint to verify API is working"""
    return {
        "message": "Research Assistant API v1 is working!",
        "version": "1.0.0",
        "endpoints": [
            "POST /research/start",
            "GET /research/{id}",
            "GET /research/",
            "DELETE /research/{id}"
        ]
    }