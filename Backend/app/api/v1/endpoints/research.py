from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.database import Research, Source
from app.tasks.celery_app import celery_app
from app.models.schemas import (
    ResearchRequest, ResearchResponse, ResearchCreateResponse,
    ResearchSummary, ResearchListResponse, HealthResponse, SourceType
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
        # Fallback for source_types validation
        if not request.source_types or not all(isinstance(st, SourceType) for st in request.source_types):
            request.source_types = [SourceType.ACADEMIC]  # Default to academic for new logic
        
        # Create new research record
        research = Research(
            query=request.query,
            status="pending",
            max_results=request.max_results,
            include_summary=request.include_summary,
            language=request.language,
            metadata_info={
                "source_types": [st.value for st in request.source_types],
                "created_via": "api",
                "date_from": request.date_from,
                "min_citations": request.min_citations,
                "selected_sources": request.sources,
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
        # Temporary fix: count only by ID to avoid missing column issues
        source_count = db.query(Source.id).filter(Source.research_id == research.id).count()
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

# New enhanced endpoints

@router.get("/{research_id}/export")
async def export_research(
    research_id: int,
    format: str = Query("json", description="Export format: csv, json, excel, bibtex"),
    db: Session = Depends(get_db)
):
    """Export research results in various formats"""
    from fastapi.responses import FileResponse
    from app.services.academic_fetcher import EnhancedAcademicFetcher
    import pandas as pd
    import tempfile
    import os
    
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # Get sources data
    sources = db.query(Source).filter(Source.research_id == research_id).all()
    if not sources:
        raise HTTPException(status_code=404, detail="No sources found for this research")
    
    # Convert to DataFrame format
    papers_data = []
    for source in sources:
        papers_data.append({
            'title': source.title,
            'authors': source.metadata.get('authors', []) if source.metadata else [],
            'year': source.metadata.get('year') if source.metadata else None,
            'venue': source.metadata.get('venue') if source.metadata else None,
            'abstract': source.summary,
            'pdf_url': source.url if source.url.endswith('.pdf') else None,
            'citation_count': source.citation_count or 0,
            'source': source.metadata.get('source_api') if source.metadata else 'unknown',
            'doi': source.doi,
            'relevance_score': source.relevance_score
        })
    
    df = pd.DataFrame(papers_data)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as tmp_file:
        filename = tmp_file.name
    
    try:
        # Use EnhancedAcademicFetcher export functionality
        fetcher = EnhancedAcademicFetcher()
        fetcher.export_results(df, filename, format=format)
        
        # Return file
        media_type = {
            'csv': 'text/csv',
            'json': 'application/json',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'bibtex': 'application/x-bibtex'
        }.get(format, 'application/octet-stream')
        
        return FileResponse(
            filename,
            media_type=media_type,
            filename=f"research_{research_id}_results.{format}"
        )
    
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(filename):
            os.unlink(filename)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/{research_id}/summary")
async def get_research_summary(
    research_id: int,
    db: Session = Depends(get_db)
):
    """Get enhanced summary report for research"""
    from app.services.academic_fetcher import EnhancedAcademicFetcher
    import pandas as pd
    
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    sources = db.query(Source).filter(Source.research_id == research_id).all()
    if not sources:
        return {"message": "No sources found for summary"}
    
    # Convert to DataFrame for analysis
    papers_data = []
    for source in sources:
        papers_data.append({
            'title': source.title,
            'authors': source.metadata.get('authors', []) if source.metadata else [],
            'year': source.metadata.get('year') if source.metadata else None,
            'venue': source.metadata.get('venue') if source.metadata else None,
            'citation_count': source.citation_count or 0,
            'source': source.metadata.get('source_api') if source.metadata else 'unknown',
            'has_pdf': bool(source.url and source.url.endswith('.pdf')),
            'relevance_score': source.relevance_score or 0
        })
    
    df = pd.DataFrame(papers_data)
    
    # Generate enhanced summary using EnhancedAcademicFetcher
    fetcher = EnhancedAcademicFetcher()
    summary_report = fetcher.create_summary_report(df)
    
    # Add research-specific information
    summary_report.update({
        'research_id': research_id,
        'query': research.query,
        'status': research.status,
        'created_at': research.created_at,
        'completed_at': research.completed_at
    })
    
    return summary_report

@router.get("/{research_id}/filter")
async def filter_research_results(
    research_id: int,
    year_from: int = Query(None, description="Filter papers from this year"),
    year_to: int = Query(None, description="Filter papers to this year"),
    min_citations: int = Query(None, description="Minimum citation count"),
    venues: str = Query(None, description="Comma-separated list of venues"),
    has_pdf: bool = Query(None, description="Filter papers with PDF only"),
    db: Session = Depends(get_db)
):
    """Filter research results by various criteria"""
    from app.services.academic_fetcher import EnhancedAcademicFetcher
    import pandas as pd
    
    research = db.query(Research).filter(Research.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    sources = db.query(Source).filter(Source.research_id == research_id).all()
    if not sources:
        return {"message": "No sources found to filter"}
    
    # Convert to DataFrame
    papers_data = []
    for source in sources:
        papers_data.append({
            'title': source.title,
            'authors': source.metadata.get('authors', []) if source.metadata else [],
            'year': source.metadata.get('year') if source.metadata else None,
            'venue': source.metadata.get('venue') if source.metadata else None,
            'abstract': source.summary,
            'citation_count': source.citation_count or 0,
            'source': source.metadata.get('source_api') if source.metadata else 'unknown',
            'has_pdf': bool(source.url and source.url.endswith('.pdf')),
            'relevance_score': source.relevance_score or 0,
            'doi': source.doi,
            'url': source.url
        })
    
    df = pd.DataFrame(papers_data)
    
    # Apply filters using EnhancedAcademicFetcher
    fetcher = EnhancedAcademicFetcher()
    
    # Prepare filter parameters
    year_range = None
    if year_from or year_to:
        year_range = (year_from or 1900, year_to or 2030)
    
    venue_list = None
    if venues:
        venue_list = [v.strip() for v in venues.split(',')]
    
    # Apply filters
    filtered_df = fetcher.filter_papers(
        df,
        year_range=year_range,
        venues=venue_list,
        min_citations=min_citations,
        has_pdf=has_pdf
    )
    
    # Convert back to response format
    filtered_results = []
    for _, paper in filtered_df.iterrows():
        filtered_results.append({
            'title': paper['title'],
            'authors': paper['authors'],
            'year': paper['year'],
            'venue': paper['venue'],
            'abstract': paper['abstract'],
            'citation_count': paper['citation_count'],
            'source': paper['source'],
            'has_pdf': paper['has_pdf'],
            'relevance_score': paper['relevance_score'],
            'doi': paper['doi'],
            'url': paper['url']
        })
    
    return {
        'research_id': research_id,
        'total_results': len(df),
        'filtered_results': len(filtered_results),
        'filters_applied': {
            'year_range': year_range,
            'venues': venue_list,
            'min_citations': min_citations,
            'has_pdf': has_pdf
        },
        'results': filtered_results
    }

@celery_app.task
def test_task():
    print("Test task executed!")