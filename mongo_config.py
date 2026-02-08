"""
MongoDB Atlas Configuration
Handles MongoDB connection settings and database initialization
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Atlas connection string
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://mrangakrishna:Vamshi1234@cluster0.kwnom.mongodb.net/"
)

# Database and collection names
DATABASE_NAME = "financial_analysis"
JOBS_COLLECTION = "jobs"

# Connection timeout settings
CONNECT_TIMEOUT = 5000  # 5 seconds
SERVER_SELECTION_TIMEOUT = 5000  # 5 seconds


def get_mongo_client():
    """
    Create and return a MongoDB client instance
    
    Returns:
        MongoClient: Connected MongoDB client
        
    Raises:
        ConnectionFailure: If unable to connect to MongoDB
    """
    try:
        client = MongoClient(
            MONGO_URI,
            connectTimeoutMS=CONNECT_TIMEOUT,
            serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT
        )
        # Test the connection
        client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB Atlas")
        return client
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
        raise
    except ConfigurationError as e:
        logger.error(f"❌ MongoDB configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


def get_database():
    """
    Get the database instance
    
    Returns:
        Database: MongoDB database instance
    """
    client = get_mongo_client()
    return client[DATABASE_NAME]


def get_jobs_collection():
    """
    Get the jobs collection instance
    
    Returns:
        Collection: MongoDB jobs collection
    """
    db = get_database()
    return db[JOBS_COLLECTION]
