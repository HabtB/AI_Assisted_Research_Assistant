from sqlalchemy.orm import Session
from app.models.database import Research, Source
from app.models.schemas import ResearchCreate
from typing import List, Optional
import uuid
from datetime import datetime

class ResearchService:
    def __init__(self, db: Session):
        self.db = db

    def create_research(self, research_data: ResearchCreate) -> Research:
        """Create a new research request"""
        research = Research(
            query=research_data.query,
            max_results=research_data.max_results,
            include_summary=research_data.include_summary,
            language=research_data.language,
            status="pending"
        )
        self.db.add(research)
        self.db.commit()
        self.db.refresh(research)
        return research

    def get_research(self, research_id: int) -> Optional[Research]:
        """Get research by ID"""
        return self.db.query(Research).filter(Research.id == research_id).first()

    def list_research(self, skip: int = 0, limit: int = 20) -> List[Research]:
        """List all research requests"""
        return self.db.query(Research).offset(skip).limit(limit).all()

    def update_status(self, research_id: int, status: str, error_message: str = None):
        """Update research status"""
        research = self.get_research(research_id)
        if research:
            research.status = status
            if error_message:
                research.error_message = error_message
            if status == "completed":
                research.completed_at = datetime.utcnow()
            self.db.commit()

    def delete_research(self, research_id: int) -> bool:
        """Delete research record"""
        research = self.get_research(research_id)
        if research:
            self.db.delete(research)
            self.db.commit()
            return True
        return False