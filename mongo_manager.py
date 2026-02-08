"""
MongoDB Manager Module
Handles all MongoDB operations for job management
"""
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, IndexModel

from mongo_config import get_database, JOBS_COLLECTION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoManager:
    """Manages MongoDB operations for job tracking"""
    
    def __init__(self):
        """Initialize MongoDB connection and setup indexes"""
        try:
            self.db = get_database()
            self.jobs = self.db[JOBS_COLLECTION]
            self._setup_indexes()
            logger.info(f"✅ MongoDB Manager initialized with collection: {JOBS_COLLECTION}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB Manager: {e}")
            raise
    
    def _setup_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Create indexes
            indexes = [
                IndexModel([("job_id", ASCENDING)], unique=True, name="job_id_unique"),
                IndexModel([("created_at", ASCENDING)], name="created_at_index"),
                IndexModel([("status", ASCENDING)], name="status_index")
            ]
            self.jobs.create_indexes(indexes)
            logger.info("✅ MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create indexes (may already exist): {e}")
    
    def create_job(
        self,
        job_id: str,
        query: str,
        file_path: str,
        filename: str
    ) -> bool:
        """
        Create a new job entry in MongoDB
        
        Args:
            job_id: Unique job identifier
            query: User's analysis query
            file_path: Path to uploaded file
            filename: Original filename
            
        Returns:
            bool: True if created successfully
        """
        try:
            job_doc = {
                "_id": job_id,
                "job_id": job_id,
                "query": query,
                "file_path": file_path,
                "filename": filename,
                "status": "queued",
                "created_at": datetime.utcnow(),
                "started_at": None,
                "ended_at": None,
                "result": None,
                "error": None
            }
            
            self.jobs.insert_one(job_doc)
            logger.info(f"✅ Job {job_id} created in MongoDB")
            return True
            
        except PyMongoError as e:
            logger.error(f"❌ Failed to create job {job_id}: {e}")
            return False
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        **kwargs
    ) -> bool:
        """
        Update job status and optional fields
        
        Args:
            job_id: Job identifier
            status: New status (queued, started, processing, completed, failed)
            **kwargs: Additional fields to update (e.g., started_at, ended_at, error)
            
        Returns:
            bool: True if updated successfully
        """
        try:
            update_doc = {"status": status}
            
            # Add timestamp based on status
            if status == "started" and "started_at" not in kwargs:
                update_doc["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed"] and "ended_at" not in kwargs:
                update_doc["ended_at"] = datetime.utcnow()
            
            # Add any additional fields
            update_doc.update(kwargs)
            
            result = self.jobs.update_one(
                {"job_id": job_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Job {job_id} status updated to '{status}'")
                return True
            else:
                logger.warning(f"⚠️ Job {job_id} not found or already has status '{status}'")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ Failed to update job {job_id} status: {e}")
            return False
    
    def store_job_result(
        self,
        job_id: str,
        result: Dict[str, Any],
        analysis: str
    ) -> bool:
        """
        Store job result upon completion
        
        Args:
            job_id: Job identifier
            result: Complete result dictionary
            analysis: Analysis text
            
        Returns:
            bool: True if stored successfully
        """
        try:
            update_doc = {
                "status": "completed",
                "ended_at": datetime.utcnow(),
                "result": {
                    "status": result.get("status", "success"),
                    "job_id": job_id,
                    "query": result.get("query", ""),
                    "analysis": analysis,
                    "message": result.get("message", "Analysis completed successfully")
                }
            }
            
            result = self.jobs.update_one(
                {"job_id": job_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Job {job_id} result stored in MongoDB")
                return True
            else:
                logger.warning(f"⚠️ Job {job_id} not found when storing result")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ Failed to store job {job_id} result: {e}")
            return False
    
    def store_job_error(
        self,
        job_id: str,
        error_message: str
    ) -> bool:
        """
        Store job error information
        
        Args:
            job_id: Job identifier
            error_message: Error message
            
        Returns:
            bool: True if stored successfully
        """
        try:
            update_doc = {
                "status": "failed",
                "ended_at": datetime.utcnow(),
                "error": error_message
            }
            
            result = self.jobs.update_one(
                {"job_id": job_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Job {job_id} error stored in MongoDB")
                return True
            else:
                logger.warning(f"⚠️ Job {job_id} not found when storing error")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ Failed to store job {job_id} error: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete job information
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job document or None if not found
        """
        try:
            job = self.jobs.find_one({"job_id": job_id})
            if job:
                # Convert datetime objects to ISO strings for JSON serialization
                if job.get("created_at"):
                    job["created_at"] = job["created_at"].isoformat()
                if job.get("started_at"):
                    job["started_at"] = job["started_at"].isoformat()
                if job.get("ended_at"):
                    job["ended_at"] = job["ended_at"].isoformat()
                # Remove MongoDB _id from response
                job.pop("_id", None)
            return job
            
        except PyMongoError as e:
            logger.error(f"❌ Failed to get job {job_id}: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status information
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job status information or None if not found
        """
        try:
            job = self.jobs.find_one(
                {"job_id": job_id},
                {
                    "job_id": 1,
                    "status": 1,
                    "created_at": 1,
                    "started_at": 1,
                    "ended_at": 1,
                    "error": 1
                }
            )
            
            if job:
                # Convert datetime objects to ISO strings
                if job.get("created_at"):
                    job["created_at"] = job["created_at"].isoformat()
                if job.get("started_at"):
                    job["started_at"] = job["started_at"].isoformat()
                if job.get("ended_at"):
                    job["ended_at"] = job["ended_at"].isoformat()
                # Remove MongoDB _id
                job.pop("_id", None)
                return job
            else:
                return None
                
        except PyMongoError as e:
            logger.error(f"❌ Failed to get job {job_id} status: {e}")
            return None
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job result if completed
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job result or status information
        """
        try:
            job = self.jobs.find_one({"job_id": job_id})
            
            if not job:
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "message": "Job not found"
                }
            
            if job["status"] == "completed" and job.get("result"):
                return {
                    "job_id": job_id,
                    "status": "finished",
                    "result": job["result"]
                }
            elif job["status"] == "failed":
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": job.get("error", "Unknown error")
                }
            else:
                return {
                    "job_id": job_id,
                    "status": job["status"],
                    "message": f"Job is {job['status']}, not yet complete"
                }
                
        except PyMongoError as e:
            logger.error(f"❌ Failed to get job {job_id} result: {e}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }


# Singleton instance
_mongo_manager = None


def get_mongo_manager() -> MongoManager:
    """Get or create MongoManager singleton instance"""
    global _mongo_manager
    if _mongo_manager is None:
        _mongo_manager = MongoManager()
    return _mongo_manager
