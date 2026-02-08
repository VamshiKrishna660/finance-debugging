from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import logging

from queue_manager import get_queue_manager
from jobs import process_financial_analysis
from redis_config import QUEUE_ENABLED
from mongo_manager import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI-powered financial document analysis with queue-based processing",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize queue manager
try:
    queue_mgr = get_queue_manager()
    logger.info("✅ Queue manager initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize queue manager: {e}")
    logger.warning("⚠️ Running without queue support - Redis may not be available")
    queue_mgr = None

# Initialize MongoDB manager
try:
    mongo_mgr = get_mongo_manager()
    logger.info("✅ MongoDB manager initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize MongoDB manager: {e}")
    logger.warning("⚠️ Running without MongoDB support")
    mongo_mgr = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial Document Analyzer API is running",
        "version": "2.0.0",
        "queue_enabled": QUEUE_ENABLED and queue_mgr is not None,
        "mongodb_enabled": mongo_mgr is not None,
        "features": ["async_processing", "job_tracking", "multi_agent_analysis", "persistent_storage"]
    }


@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """
    Submit financial document for analysis (async processing)
    
    Returns job ID immediately for tracking
    """
    if not queue_mgr:
        raise HTTPException(
            status_code=503,
            detail="Queue service unavailable. Please ensure Redis is running."
        )
    
    job_id = str(uuid.uuid4())
    file_path = f"data/job_{job_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file with job ID
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"📄 File saved: {file_path} ({len(content)} bytes)")
        
        # Validate query
        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"
        
        # Store job metadata in MongoDB
        if mongo_mgr:
            mongo_mgr.create_job(
                job_id=job_id,
                query=query.strip(),
                file_path=file_path,
                filename=file.filename
            )
        
        # Enqueue the job
        queue_mgr.enqueue_job(
            process_financial_analysis,
            job_id,
            file_path,
            query.strip(),
            job_id=job_id
        )
        
        logger.info(f"✅ Job {job_id} enqueued successfully")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Analysis job queued successfully",
            "query": query.strip(),
            "file_name": file.filename,
            "endpoints": {
                "status": f"/job/{job_id}/status",
                "result": f"/job/{job_id}/result"
            }
        }
        
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        logger.error(f"❌ Error enqueueing job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a job"""
    try:
        # Try MongoDB first for persistent status
        if mongo_mgr:
            status_info = mongo_mgr.get_job_status(job_id)
            if status_info:
                return status_info
        
        # Fallback to Redis if MongoDB unavailable or job not found
        if queue_mgr:
            status_info = queue_mgr.get_job_status(job_id)
            return status_info
        
        raise HTTPException(
            status_code=503,
            detail="Job tracking services unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job status: {str(e)}"
        )


@app.get("/job/{job_id}/result")
async def get_job_result(job_id: str):
    """Get the result of a completed job"""
    try:
        # Try MongoDB first for persistent results
        if mongo_mgr:
            result = mongo_mgr.get_job_result(job_id)
            
            if result.get("status") == "finished":
                return {
                    "job_id": job_id,
                    "status": "success",
                    **result.get("result", {})
                }
            elif result.get("status") == "failed":
                return JSONResponse(
                    status_code=500,
                    content={
                        "job_id": job_id,
                        "status": "failed",
                        "error": result.get("error", "Job failed")
                    }
                )
            elif result.get("status") != "not_found":
                return {
                    "job_id": job_id,
                    "status": result.get("status"),
                    "message": result.get("message", "Job not yet complete")
                }
        
        # Fallback to Redis if MongoDB unavailable or job not found
        if queue_mgr:
            result = queue_mgr.get_job_result(job_id)
            
            if result.get("status") == "finished":
                return {
                    "job_id": job_id,
                    "status": "success",
                    **result.get("result", {})
                }
            elif result.get("status") == "failed":
                return JSONResponse(
                    status_code=500,
                    content={
                        "job_id": job_id,
                        "status": "failed",
                        "error": result.get("error", "Job failed")
                    }
                )
            else:
                return {
                    "job_id": job_id,
                    "status": result.get("status"),
                    "message": result.get("message", "Job not yet complete")
                }
        
        raise HTTPException(
            status_code=503,
            detail="Job tracking services unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting job result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job result: {str(e)}"
        )


@app.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a queued job"""
    if not queue_mgr:
        raise HTTPException(
            status_code=503,
            detail="Queue service unavailable"
        )
    
    try:
        cancelled = queue_mgr.cancel_job(job_id)
        if cancelled:
            return {
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancelled successfully"
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "job_id": job_id,
                    "status": "not_cancelled",
                    "message": "Job cannot be cancelled (already started or completed)"
                }
            )
    except Exception as e:
        logger.error(f"❌ Error cancelling job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling job: {str(e)}"
        )


@app.get("/queue/stats")
async def get_queue_stats():
    """Get queue statistics"""
    if not queue_mgr:
        raise HTTPException(
            status_code=503,
            detail="Queue service unavailable"
        )
    
    try:
        stats = queue_mgr.get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting queue stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving queue statistics: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)