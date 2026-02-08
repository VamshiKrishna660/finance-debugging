"""
Test MongoDB Integration
Tests MongoDB manager functionality for job tracking
"""
import sys
from mongo_manager import get_mongo_manager
from datetime import datetime

def test_mongodb_integration():
    """Test all MongoDB operations"""
    
    print("=" * 60)
    print("Testing MongoDB Atlas Integration")
    print("=" * 60)
    
    try:
        # Get MongoDB manager
        print("\n1. Connecting to MongoDB...")
        mongo_mgr = get_mongo_manager()
        print("   [OK] Connected successfully!")
        
        # Test job creation
        print("\n2. Creating test job...")
        test_job_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = mongo_mgr.create_job(
            job_id=test_job_id,
            query="Test analysis query",
            file_path="data/test.pdf",
            filename="test.pdf"
        )
        if success:
            print(f"   [OK] Job created: {test_job_id}")
        else:
            print("   [FAIL] Failed to create job")
            return False
        
        # Test status update to 'started'
        print("\n3. Updating job status to 'started'...")
        success = mongo_mgr.update_job_status(test_job_id, "started")
        if success:
            print("   [OK] Status updated to 'started'")
        else:
            print("   [FAIL] Failed to update status")
        
        # Test status update to 'processing'
        print("\n4. Updating job status to 'processing'...")
        success = mongo_mgr.update_job_status(test_job_id, "processing")
        if success:
            print("   [OK] Status updated to 'processing'")
        else:
            print("   [FAIL] Failed to update status")
        
        # Test getting job status
        print("\n5. Retrieving job status...")
        status = mongo_mgr.get_job_status(test_job_id)
        if status:
            print(f"   [OK] Status retrieved:")
            print(f"      - Job ID: {status.get('job_id')}")
            print(f"      - Status: {status.get('status')}")
            print(f"      - Created: {status.get('created_at')}")
            print(f"      - Started: {status.get('started_at')}")
        else:
            print("   [FAIL] Failed to get status")
        
        # Test storing job result
        print("\n6. Storing job result...")
        result_dict = {
            "status": "success",
            "job_id": test_job_id,
            "query": "Test analysis query",
            "message": "Test completed successfully"
        }
        success = mongo_mgr.store_job_result(
            test_job_id,
            result_dict,
            "This is a test analysis result."
        )
        if success:
            print("   [OK] Result stored successfully")
        else:
            print("   [FAIL] Failed to store result")
        
        # Test getting complete job data
        print("\n7. Retrieving complete job data...")
        job_data = mongo_mgr.get_job(test_job_id)
        if job_data:
            print(f"   [OK] Job data retrieved:")
            print(f"      - Job ID: {job_data.get('job_id')}")
            print(f"      - Status: {job_data.get('status')}")
            print(f"      - Query: {job_data.get('query')}")
            print(f"      - Result: {job_data.get('result', {}).get('message')}")
        else:
            print("   [FAIL] Failed to get job data")
        
        # Test getting job result
        print("\n8. Retrieving job result...")
        result = mongo_mgr.get_job_result(test_job_id)
        if result and result.get("status") == "finished":
            print("   [OK] Result retrieved:")
            print(f"      - Status: {result.get('status')}")
            print(f"      - Message: {result.get('result', {}).get('message')}")
        else:
            print(f"   [FAIL] Unexpected result: {result}")
        
        # Test error storage
        print("\n9. Testing error storage...")
        error_job_id = f"test_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mongo_mgr.create_job(
            job_id=error_job_id,
            query="Test error query",
            file_path="data/error.pdf",
            filename="error.pdf"
        )
        success = mongo_mgr.store_job_error(error_job_id, "Test error message")
        if success:
            print("   [OK] Error stored successfully")
            error_result = mongo_mgr.get_job_result(error_job_id)
            if error_result.get("status") == "failed":
                print(f"      - Error: {error_result.get('error')}")
        else:
            print("   [FAIL] Failed to store error")
        
        print("\n" + "=" * 60)
        print("SUCCESS: All tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\nERROR: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mongodb_integration()
    sys.exit(0 if success else 1)
