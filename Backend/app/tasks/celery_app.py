from celery import Celery
from app.core.config import settings
import os


# Create Celery instance
celery_app = Celery(
    "research_assistant",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.research_tasks"]  # Import our task modules
)

# Detect Windows and use appropriate pool
is_windows = os.name == "nt"

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # Limit prefetch to one task at a time
    task_acks_late=True,  # Acknowledge tasks after completion


    # Windows Compatibility
    worker_pool='solo' if is_windows else 'prefork',
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Task routing
    # task_routes={
    #    "app.tasks.research_tasks.*": {"queue": "research_tasks"},
    # },
)

# Optional: Add periodic task settings
celery_app.conf.beat_schedule = {
    # Example periodic task (uncomment to use)
    # "example-task": {
    #     "task": "app.tasks.example_task",
    #     "schedule": 60.0,  # Every 60 seconds
    # }
}