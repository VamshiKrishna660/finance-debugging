"""
Queue Manager Module
Handles job queuing, status tracking, and result retrieval
"""
import redis
from rq import Queue
from rq.job import Job
from typing import Optional, Dict, Any
import logging

from redis_config import (
    get_redis_url, 
    DEFAULT_QUEUE_NAME, 
    RESULT_TTL,
    JOB_TIMEOUT,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueueManager:
    """Manages Redis Queue operations"""
    
    def __init__(self):
        """Initialize Redis connection and queue"""
        try:
            # Connection for RQ (without decode_responses to handle binary data)
            self.rq_conn = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=False  # RQ handles its own serialization
            )
            # Connection for direct Redis operations (with decode_responses for convenience)
            self.redis_conn = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.redis_conn.ping()
            # Use rq_conn for queue operations
            self.queue = Queue(DEFAULT_QUEUE_NAME, connection=self.rq_conn)
            logger.info(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def enqueue_job(self, func, *args, job_id: str = None, **kwargs) -> str:
        """
        Enqueue a job to the queue
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            job_id: Optional custom job ID
            **kwargs: Keyword arguments for the function
            
        Returns:
            str: Job ID
        """
        try:
            job = self.queue.enqueue(
                func,
                *args,
                **kwargs,
                job_id=job_id,
                result_ttl=RESULT_TTL,
                job_timeout=JOB_TIMEOUT,
            ) 
            logger.info(f"📝 Job enqueued: {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"❌ Failed to enqueue job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job
        
        Args:
            job_id: Job ID to check
            
        Returns:
            dict: Job status information
        """
        try:
            job = Job.fetch(job_id, connection=self.rq_conn)
            
            # Calculate position in queue if job is queued
            position = None
            if job.is_queued:
                position = job.get_position()
            
            return {
                "job_id": job.id,
                "status": job.get_status(),
                "position": position,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "exc_info": job.exc_info if job.is_failed else None
            }
        except Exception as e:
            logger.error(f"❌ Failed to get job status for {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": str(e)
            }
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed job
        
        Args:
            job_id: Job ID to retrieve result for
            
        Returns:
            dict: Job result or error information
        """
        try:
            job = Job.fetch(job_id, connection=self.rq_conn)
            
            if job.is_finished:
                return {
                    "job_id": job.id,
                    "status": "finished",
                    "result": job.result
                }
            elif job.is_failed:
                return {
                    "job_id": job.id,
                    "status": "failed",
                    "error": job.exc_info
                }
            else:
                return {
                    "job_id": job.id,
                    "status": job.get_status(),
                    "message": f"Job is {job.get_status()}, not yet complete"
                }
        except Exception as e:
            logger.error(f"❌ Failed to get job result for {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued job
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            job = Job.fetch(job_id, connection=self.rq_conn)
            if job.is_queued or job.is_deferred:
                job.cancel()
                logger.info(f"🚫 Job cancelled: {job_id}")
                return True
            else:
                logger.warning(f"⚠️ Cannot cancel job {job_id} - status: {job.get_status()}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to cancel job {job_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            dict: Queue statistics
        """
        try:
            # Get worker count
            from rq import Worker
            workers = Worker.all(connection=self.rq_conn)
            
            return {
                "queue_name": DEFAULT_QUEUE_NAME,
                "pending": len(self.queue),
                "started": self.queue.started_job_registry.count,
                "finished": self.queue.finished_job_registry.count,
                "failed": self.queue.failed_job_registry.count,
                "deferred": self.queue.deferred_job_registry.count,
                "scheduled": self.queue.scheduled_job_registry.count,
                "workers": len(workers),
                "worker_names": [w.name for w in workers]
            }
        except Exception as e:
            logger.error(f"❌ Failed to get queue stats: {e}")
            return {
                "error": str(e)
            }

# Singleton instance
_queue_manager = None

def get_queue_manager() -> QueueManager:
    """Get or create QueueManager singleton instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager
