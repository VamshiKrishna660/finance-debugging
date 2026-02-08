"""
Redis Configuration Module
Centralizes all Redis and RQ configuration settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Queue settings
DEFAULT_QUEUE_NAME = "financial_analysis"
JOB_TIMEOUT = 1800  # 30 minutes max per job (increased for CrewAI analysis)
RESULT_TTL = 86400  # Results stored for 24 hours (in seconds)
MAX_RETRIES = 3  # Number of retry attempts for failed jobs

# Queue enabled flag
QUEUE_ENABLED = os.getenv("QUEUE_ENABLED", "true").lower() == "true"

def get_redis_url():
    """Generate Redis connection URL"""
    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
