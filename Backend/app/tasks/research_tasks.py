from celery import current_task
from sqlalchemy.orm import Session
from app.models.database import Research, Source
from app.core.database import SessionLocal
from app.tasks.celery_app import celery_app
from app.services.web_scraper import WebScraper
from app.services.content_processor import ContentProcessor
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
    scraper = WebScraper()
    processor = ContentProcessor()
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
            meta={'current': 10, 'total': 100, 'status': 'Searching web...'}
        )
        
        # Search the web
        search_results = asyncio.run(
            scraper.search_web(research.query, num_results=5)
        )
        
        logger.info(f"Found {len(search_results)} search results")
        
        # Process each result
        sources_data = []
        total_results = len(search_results)
        
        for idx, result in enumerate(search_results):
            progress = 20 + (idx / total_results) * 60
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Analyzing source {idx + 1}/{total_results}...'
                }
            )
            
            # Scrape content
            scraped_data = asyncio.run(
                scraper.scrape_content(result['url'])
            )
            
            # Process content
            processed_data = processor.process_content(scraped_data)
            
            # Extract keywords
            keywords = processor.extract_keywords(
                scraped_data.get('content', ''), 
                num_keywords=5
            )
            
            sources_data.append({
                'url': processed_data['url'],
                'title': processed_data['title'],
                'summary': processed_data['summary'],
                'relevance_score': processed_data['relevance_score'],
                'metadata': {
                    'word_count': processed_data['word_count'],
                    'key_points': processed_data['key_points'],
                    'keywords': keywords,
                    'scraped_at': datetime.utcnow().isoformat()
                },
                'content': scraped_data.get('content', '')  # Keep content for AI analysis
            })
            
            logger.info(f"Processed source: {processed_data['title']}")
        
        # AI Analysis Phase
        self.update_state(
            state='PROGRESS',
            meta={'current': 85, 'total': 100, 'status': 'Performing AI analysis...'}
        )
        
        # Initialize AI analyzer
        ai_analyzer = AIAnalyzer(preferred_provider=os.getenv("PREFERRED_AI_PROVIDER", "groq"))
        
        # Check if AI is available
        available_providers = ai_analyzer.get_available_providers()
        if available_providers:
            logger.info(f"Using AI provider: {available_providers[0]}")
            
            # Prepare content for AI
            contents_for_ai = [{
                'title': s['title'],
                'url': s['url'],
                'content': s.get('content', s['summary'])
            } for s in sources_data]
            
            # Get AI analysis
            ai_analysis = asyncio.run(
                ai_analyzer.analyze_research(research.query, contents_for_ai)
            )
            
            # Use AI-generated summary and insights
            research.summary = ai_analysis.get('summary', 'Analysis completed')
            research.key_findings = ai_analysis.get('key_findings', [])[:5]  # Limit to 5 findings
            
            metadata = {
                'sources_analyzed': len(sources_data),
                'ai_provider': ai_analysis.get('provider_used', 'none'),
                'themes': ai_analysis.get('themes', []),
                'contradictions': ai_analysis.get('contradictions', []),
                'recommendations': ai_analysis.get('recommendations', []),
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