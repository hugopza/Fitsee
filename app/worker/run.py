import sys
import os
from redis import Redis
from rq import Worker, Queue, Connection
from app.core import config
import logging

# Ensure python path includes app
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

listen = ['renders']

if __name__ == '__main__':
    logger.info("Starting Worker...")
    redis_url = config.settings.REDIS_URL
    conn = Redis.from_url(redis_url)

    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
