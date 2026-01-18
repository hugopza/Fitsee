from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models import RenderJob, RenderJobStatus, SizeEnum
from app.core import config
from redis import Redis
from rq import Queue

# Initialize Redis and Queue
redis_conn = Redis.from_url(config.settings.REDIS_URL)
queue = Queue('renders', connection=redis_conn)

def create_render_job(db: Session, user_id: UUID, product_id: UUID, size: SizeEnum) -> RenderJob:
    job = RenderJob(
        user_id=user_id,
        product_id=product_id,
        size=size,
        status=RenderJobStatus.QUEUED
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue job
    # We pass the job.id (UUID) as a string to the worker task
    queue.enqueue('app.worker.tasks.run_render_job', str(job.id))

    return job

def get_render_job(db: Session, job_id: UUID) -> RenderJob:
    return db.query(RenderJob).filter(RenderJob.id == job_id).first()
