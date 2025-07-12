from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class ResearchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SourceType(str, Enum):
    WEB = "web"
    ACADEMIC = "academic"
    NEWS = "news"
    API = "api"

# Base models
class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = True
    message: str = "Success"

# Request models
class ResearchRequest(BaseModel):
    """Request model for creating new research"""
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=500, 
        description="Research query or question",
        example="Latest developments in artificial intelligence"
    )
    max_results: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Maximum number of sources to collect"
    )
    include_summary: bool = Field(
        default=True, 
        description="Whether to generate AI summary"
    )
    language: str = Field(
        default="en", 
        min_length=2, 
        max_length=5, 
        description="Language code (e.g., 'en', 'es', 'fr')"
    )
    source_types: List[SourceType] = Field(
        default=[SourceType.WEB], 
        description="Types of sources to search"
    )
    date_from: Optional[str] = Field(None, description="Start date YYYY or YYYY-MM")
    min_citations: Optional[int] = Field(0, ge=0)
    sources: Optional[List[str]] = Field(None, description="List of sources: semantic_scholar, pubmed, arxiv, crossref")

class ResearchUpdateRequest(BaseModel):
    """Request model for updating research status"""
    status: Optional[ResearchStatus] = None
    summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    error_message: Optional[str] = None

# Response models for Sources
class SourceBase(BaseModel):
    """Base source model"""
    title: str
    url: str
    snippet: Optional[str] = None
    source_type: str
    credibility_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    published_date: Optional[datetime] = None
    author: Optional[str] = None

class SourceResponse(SourceBase):
    """Complete source response model"""
    id: int
    research_id: int
    scraped_at: datetime
    
    class Config:
        from_attributes = True

class SourceCreate(SourceBase):
    """Model for creating new source"""
    research_id: int
    full_content: Optional[str] = None

# Response models for Research
class ResearchBase(BaseModel):
    """Base research model"""
    query: str
    max_results: int
    include_summary: bool
    language: str

class ResearchResponse(ResearchBase):
    """Complete research response model"""
    id: int
    status: ResearchStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    error_message: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None
    sources: List[SourceResponse] = []
    
    class Config:
        from_attributes = True

class ResearchSummary(BaseModel):
    """Simplified research response for lists"""
    id: int
    query: str
    status: ResearchStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    source_count: int = 0
    
    class Config:
        from_attributes = True

class ResearchCreateResponse(BaseResponse):
    """Response when creating new research"""
    research: ResearchResponse

class ResearchListResponse(BaseResponse):
    """Response for listing research"""
    research_list: List[ResearchSummary]
    total: int
    page: int
    page_size: int

# Error response models
class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    validation_errors: List[Dict[str, str]]

# Health check models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime
    database_connected: bool
    redis_connected: bool = False

# Statistics models
class ResearchStats(BaseModel):
    """Research statistics"""
    total_research: int
    completed_research: int
    pending_research: int
    failed_research: int
    total_sources: int
    average_completion_time: Optional[float] = None

# Pagination models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

class SortParams(BaseModel):
    """Sorting parameters"""
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")

class ResearchFilters(BaseModel):
    """Filters for research queries"""
    status: Optional[ResearchStatus] = None
    language: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    query_contains: Optional[str] = None