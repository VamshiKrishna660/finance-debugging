"""
Redis Queue Worker
Background worker that processes jobs from the queue
"""
import sys
import logging
from rq import Worker, Queue
import redis

from redis_config import REDIS_HOST, REDIS_PORT, REDIS_DB, DEFAULT_QUEUE_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Start the RQ worker to process jobs
    """
    try:
        # Connect to Redis
        redis_conn = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=False  # RQ handles its own serialization
        )
        
        # Test connection
        redis_conn.ping()
        logger.info(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        
        # Create queue
        queue = Queue(DEFAULT_QUEUE_NAME, connection=redis_conn)
        
        # Create worker and start
        worker = Worker([queue], connection=redis_conn)
        logger.info(f"🎧 Worker started, listening on '{DEFAULT_QUEUE_NAME}' queue")
        logger.info("⏳ Waiting for jobs...")
        logger.info("Press Ctrl+C to stop")
        
        worker.work()
        
    except redis.ConnectionError as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        logger.error("Please ensure Redis server is running.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
