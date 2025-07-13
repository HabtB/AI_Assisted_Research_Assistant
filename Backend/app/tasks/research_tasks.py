from celery import current_task
from sqlalchemy.orm import Session
from app.models.database import Research, Source
from app.core.database import SessionLocal
from app.tasks.celery_app import celery_app
from app.services.academic_fetcher import EnhancedAcademicFetcher
from app.services.ai_analyzer import AIAnalyzer
from datetime import datetime
import asyncio
import logging
import os
import time

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_research_task(self, research_id: int):
    """Process research task with real web scraping and AI analysis"""
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get research record
        research = db.query(Research).filter(Research.id == research_id).first()
        if not research:
            raise ValueError(f"Research with id {research_id} not found")
        
        # Update status to processing
        research.status = "processing"
        db.commit()
        
        logger.info(f"Starting research for: {research.query}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Refining query...'}
        )
        
        # Query Refiner Agent: Use AI to expand query
        ai_analyzer = AIAnalyzer(preferred_provider=os.getenv("PREFERRED_AI_PROVIDER", "groq"))
        refined_query = asyncio.run(ai_analyzer.refine_query(research.query))  # New method; see below
        
        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': 'Fetching papers...'})
        fetcher = EnhancedAcademicFetcher()
        papers = fetcher.fetch_papers(
            refined_query or research.query,
            research.max_results,
            research.metadata_info.get("date_from"),
            research.metadata_info.get("min_citations", 0),
            research.metadata_info.get("selected_sources")
        )
        
        sources_data = []
        for idx, paper in enumerate(papers):
            progress = 30 + (idx / len(papers)) * 40
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100, 'status': f'Processing paper {idx + 1}/{len(papers)}...'})
            
            # Basic processing (no scraping needed)
            keywords = ai_analyzer.extract_keywords(paper.get('abstract', ''), num_keywords=5)  # Reuse if exists
            max_citation = max(1, max(p['citation_count'] for p in papers))
            sources_data.append({
                'url': paper.get('pdf_url') or f"https://doi.org/{paper.get('doi', '')}",
                'title': paper['title'],
                'summary': paper.get('abstract', '')[:500],  # Truncate
                'relevance_score': paper['citation_count'] / max_citation,  # Normalize
                'source_type': 'academic',  # Required
                'credibility_score': 0.9,  # Required; high for academic APIs
                'published_date': datetime(int(paper['year']), 1, 1) if paper.get('year') else None,  # Map year to date
                'author': ', '.join(paper['authors'])[:200] if paper.get('authors') else None,  # Join list, truncate
                'snippet': paper.get('abstract', '')[:200],  # Optional but useful
                'metadata': {
                    'authors': paper['authors'],
                    'year': paper['year'],
                    'venue': paper['venue'],
                    'citation_count': paper['citation_count'],
                    'keywords': keywords,
                    'source_api': paper['source'],
                },
                'doi': paper.get('doi'),  # New field
                'citation_count': paper['citation_count'],  # New field
            })
            
            logger.info(f"Processed source: {paper['title']}")
        
        # AI Analysis Phase
        self.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': 'Performing AI analysis...'}
        )
        
        # Check if AI is available
        available_providers = ai_analyzer.get_available_providers()
        if available_providers:
            logger.info(f"Using AI provider: {available_providers[0]}")
            
            # Prepare content for AI
            contents_for_ai = [{
                'title': s['title'],
                'abstract': s['summary'],  # Use abstract
            } for s in sources_data]
            
            # Get AI analysis
            ai_analysis = asyncio.run(
                ai_analyzer.analyze_research(research.query, contents_for_ai)
            )
            
            # Use AI-generated summary and insights
            research.summary = ai_analysis.get('summary', 'Analysis completed')
            research.key_findings = ai_analysis.get('key_findings', [])[:5]  # Limit to 5 findings
            
            # Add recommender
            recommendations = asyncio.run(ai_analyzer.generate_recommendations(research.query, ai_analysis))
            metadata = {
                'sources_analyzed': len(sources_data),
                'ai_provider': ai_analysis.get('provider_used', 'none'),
                'themes': ai_analysis.get('themes', []),
                'contradictions': ai_analysis.get('contradictions', []),
                'recommendations': recommendations,
                'processing_time': time.time() - start_time
            }
        else:
            # Fallback if no AI provider is configured
            logger.warning("No AI provider configured, using basic summary")
            all_summaries = [s['summary'] for s in sources_data]
            research.summary = f"Research on '{research.query}' found {len(sources_data)} relevant sources. " + \
                              f"Key findings: {' '.join(all_summaries[:2])}"[:500]
            research.key_findings = [
                f"Found {len(sources_data)} relevant sources",
                f"Topics cover various aspects of {research.query}",
                "Configure AI provider for better analysis"
            ]
            
            metadata = {
                'sources_analyzed': len(sources_data),
                'ai_provider': 'none',
                'processing_time': time.time() - start_time
            }
        
        # Save sources to database
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Saving results...'}
        )
        
        for source_data in sources_data:
            # Remove content field before saving (too large for DB)
            source_dict = source_data.copy()
            source_dict.pop('content', None)
            
            source = Source(
                research_id=research.id,
                **source_dict
            )
            db.add(source)
        
        # Update research metadata
        research.metadata_info = metadata
        
        # Update research status
        research.status = "completed"
        research.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Research completed for: {research.query}")
        
        return {
            "status": "completed",
            "research_id": research_id,
            "sources_found": len(sources_data),
            "summary": research.summary,
            "ai_provider": metadata.get('ai_provider', 'none'),
            "processing_time": metadata.get('processing_time', 0)
        }
        
    except Exception as e:
        logger.error(f"Error processing research {research_id}: {str(e)}")
        if research:
            research.status = "failed"
            research.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()

@celery_app.task
def cleanup_old_research(days: int = 30):
    """Clean up research older than specified days"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_research = db.query(Research).filter(Research.created_at < cutoff_date).all()
        
        for research in old_research:
            # Delete associated sources first
            db.query(Source).filter(Source.research_id == research.id).delete()
            db.delete(research)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_research)} old research records")
        return f"Cleaned up {len(old_research)} old research records"
    except Exception as e:
        logger.error(f"Error cleaning up old research: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@celery_app.task  
def get_task_status(task_id: str):
    """Helper task to get detailed task status"""
    result = celery_app.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result,
        'info': result.info
    }

@celery_app.task
def test_task():
    """Simple test task"""
    logger.info("Test task executed!")
    return "Hello from Celery!"