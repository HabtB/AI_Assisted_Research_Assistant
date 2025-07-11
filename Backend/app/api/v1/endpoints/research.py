from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.database import Research, Source
from app.tasks.celery_app import celery_app
from app.models.schemas import (
    ResearchRequest, ResearchResponse, ResearchCreateResponse,
    ResearchSummary, ResearchListResponse, HealthResponse
)
from app.tasks.research_tasks import process_research_task


router = APIRouter()

@router.post("/start", response_model=ResearchCreateResponse)
async def start_research(
    request: ResearchRequest,
    db: Session = Depends(get_db)
):
    """Start a new research task in background"""
    try:
        # Create new research record
        research = Research(
            query=request.query,
            status="pending",
            max_results=request.max_results,
            include_summary=request.include_summary,
            language=request.language,
            metadata_info={
                "source_types": [st.value for st in request.source_types],
                "created_via": "api"
            }
        )
        
        db.add(research)
        db.commit()
        db.refresh(research)


        # Start background task
        task = process_research_task.delay(research.id)
        
        # Store task ID in metadata
        research.metadata_info["task_id"] = task.id
        db.commit()
        
        # Convert to response model
        research_response = ResearchResponse.model_validate(research)
        
        return ResearchCreateResponse(
            message=f"Research task started successfully. Task ID: {task.id}",
            research=research_response
        )
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create research: {str(e)}")

@router.get("/{research_id}", response_model=ResearchResponse)
async def get_research(
    research_id: int,
    db: Session = Depends(get_db)
):
    """Get research by ID with all sources"""
    research = db.query(Research).filter(Research.id == research_id).first()
    
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    return ResearchResponse.model_validate(research)

@router.get("/", response_model=ResearchListResponse)
async def list_research(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """List all research with pagination"""
    # Build query
    query = db.query(Research)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Research.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    research_list = query.order_by(Research.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to summary models
    research_summaries = []
    for research in research_list:
        source_count = db.query(Source).filter(Source.research_id == research.id).count()
        summary = ResearchSummary.model_validate(research)
        summary.source_count = source_count
        research_summaries.append(summary)
    
    return ResearchListResponse(
        message=f"Found {total} research records",
        research_list=research_summaries,
        total=total,
        page=page,
        page_size=page_size
    )

@router.delete("/{research_id}")
async def delete_research(
    research_id: int,
    db: Session = Depends(get_db)
):
    """Delete research by ID"""
    research = db.query(Research).filter(Research.id == research_id).first()
    
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # Delete associated sources first
    db.query(Source).filter(Source.research_id == research_id).delete()
    
    # Delete research
    db.delete(research)
    db.commit()
    
    return {"message": f"Research {research_id} deleted successfully"}

@router.get("/{research_id}/status")
async def get_research_status(
    research_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed research task status"""
    research = db.query(Research).filter(Research.id == research_id).first()
    
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # Get task status if task_id exists
    task_info = None
    if research.metadata_info and "task_id" in research.metadata_info:
        task_id = research.metadata_info["task_id"]
        task_result = celery_app.AsyncResult(task_id)
        
        task_info = {
            "task_id": task_id,
            "task_status": task_result.status,
            "task_info": task_result.info if task_result.info else {}
        }
    
    return {
        "research_id": research_id,
        "status": research.status,
        "created_at": research.created_at,
        "completed_at": research.completed_at,
        "task_info": task_info,
        "error_message": research.error_message
    }

@celery_app.task
def test_task():
    print("Test task executed!")
