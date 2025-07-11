from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Research(Base):
    __tablename__ = "research"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic research info
    query = Column(String(500), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Research settings
    max_results = Column(Integer, default=20)
    include_summary = Column(Boolean, default=True)
    language = Column(String(10), default="en")
    
    # Results
    summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)  # Store as JSON array
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata_info = Column(JSON, nullable=True)  # Store additional info as JSON
    
    # Relationship to sources
    sources = relationship("Source", back_populates="research")


class Source(Base):
    __tablename__ = "sources"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to research
    research_id = Column(Integer, ForeignKey("research.id"), nullable=False, index=True)
    
    # Source information
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    snippet = Column(Text, nullable=True)
    source_type = Column(String(50), default="web")  # web, academic, news, api
    
    # Content analysis
    credibility_score = Column(Float, default=0.5)  # 0.0 to 1.0
    relevance_score = Column(Float, default=0.5)    # 0.0 to 1.0
    
    # Metadata
    published_date = Column(DateTime(timezone=True), nullable=True)
    author = Column(String(200), nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Full content (if scraped)
    full_content = Column(Text, nullable=True)
    
    # Relationship back to research
    research = relationship("Research", back_populates="sources")