import logging
import time
from uuid import UUID
from app.db.models import RenderJob, RenderJobStatus
from app.core.database import SessionLocal
from app.worker.renderer import process_render

logger = logging.getLogger(__name__)

def run_render_job(job_id_str: str):
    """
    RQ Task to process a render job.
    """
    db = SessionLocal()
    job_id = UUID(job_id_str)
    
    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in DB")
            return

        # Update status -> RUNNING
        job.status = RenderJobStatus.RUNNING
        db.commit()

        # Run Render (Phase 1: Copy)
        try:
            filename = process_render(job_id_str)
            
            # Update status -> DONE
            job.status = RenderJobStatus.DONE
            job.progress = 100
            # Assuming api serves /static/renders
            job.video_url = f"/static/renders/{filename}"
            db.commit()
            
        except Exception as e:
            logger.error(f"Render failed for {job_id}: {e}")
            job.status = RenderJobStatus.FAILED
            job.error_message = str(e)
            db.commit()

    except Exception as e:
        logger.error(f"Critical worker error check job {job_id}: {e}")
    finally:
        db.close()
