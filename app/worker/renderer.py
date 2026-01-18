import shutil
import os
from app.core import config
import logging

logger = logging.getLogger(__name__)

def process_render(job_id: str):
    """
    Phase 1 Renderer: Copies the template MP4 to the output directory.
    In Phase 2, this will call Blender.
    """
    template_path = config.settings.RENDER_TEMPLATE_MP4
    output_dir = config.settings.RENDER_OUTPUT_DIR
    output_filename = f"{job_id}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    logger.info(f"Starting render for job {job_id}")
    logger.info(f"Template: {template_path}")
    logger.info(f"Output: {output_path}")

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found at {template_path}")

    # Copy file (Simulate render)
    shutil.copy2(template_path, output_path)
    
    logger.info(f"Render complete: {output_path}")
    return output_filename
