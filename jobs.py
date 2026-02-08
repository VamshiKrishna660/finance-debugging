"""
Background Job Functions
Contains the actual job functions executed by RQ workers
"""
import os
import logging
from typing import Dict, Any

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import analyze_financial_document, document_verification, investment_analysis, risk_assessment
from mongo_manager import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_financial_analysis(job_id: str, file_path: str, query: str) -> Dict[str, Any]:
    """
    Background job function to process financial document analysis
    
    This function is executed by RQ workers in the background.
    It runs the complete crew analysis with all 4 agents.
    
    Args:
        job_id: Unique job identifier
        file_path: Path to the uploaded PDF file
        query: User's analysis query
        
    Returns:
        dict: Result containing status and analysis
        
    Raises:
        Exception: Any errors during processing (RQ will mark job as failed)
    """
    logger.info(f"🚀 Starting job {job_id}: {file_path}")
    
    # Get MongoDB manager
    try:
        mongo_mgr = get_mongo_manager()
    except:
        mongo_mgr = None
        logger.warning("⚠️ MongoDB manager not available for job tracking")
    
    try:
        # Update status to 'started' in MongoDB
        if mongo_mgr:
            mongo_mgr.update_job_status(job_id, "started")
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"📄 Processing file: {file_path}")
        logger.info(f"❓ Query: {query}")
        
        # Update status to 'processing' in MongoDB
        if mongo_mgr:
            mongo_mgr.update_job_status(job_id, "processing")
        
        # Create and run the financial analysis crew
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[document_verification, analyze_financial_document, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=False,
            tracing=False  # Explicitly disable execution traces
        )
        
        # Execute the crew with inputs
        logger.info(f"🤖 Running crew analysis with 4 agents...")
        result = financial_crew.kickoff(inputs={'query': query, 'file_path': file_path})
        
        # Save result to file
        os.makedirs("outputs", exist_ok=True)
        with open(f"outputs/{job_id}.txt", "w") as f:
            f.write(str(result))
        logger.info(f"✅ Job {job_id} completed successfully")
        
        # Prepare result dictionary
        result_dict = {
            "status": "success",
            "job_id": job_id,
            "query": query,
            "analysis": str(result),
            "message": "Financial analysis completed successfully"
        }
        
        # Store result in MongoDB
        if mongo_mgr:
            mongo_mgr.store_job_result(job_id, result_dict, str(result))
        
        # Clean up the uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Cleaned up file: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Failed to clean up file {file_path}: {cleanup_error}")
        
        return result_dict
        
    except FileNotFoundError as e:
        logger.error(f"❌ File error in job {job_id}: {e}")
        
        # Store error in MongoDB
        if mongo_mgr:
            mongo_mgr.store_job_error(job_id, f"File not found: {str(e)}")
        
        # Clean up if file exists
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
        
    except Exception as e:
        logger.error(f"❌ Error in job {job_id}: {e}")
        
        # Store error in MongoDB
        if mongo_mgr:
            mongo_mgr.store_job_error(job_id, str(e))
        
        # Clean up the file even on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Cleaned up file after error: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Failed to clean up file {file_path}: {cleanup_error}")
        
        # Re-raise the exception so RQ marks the job as failed
        raise
