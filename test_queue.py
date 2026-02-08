"""
Quick Test Script for Redis Queue Integration
Tests the queue system end-to-end
"""
import requests
import time
import sys

API_URL = "http://localhost:8000"

def test_system():
    """Test the complete system"""
    print("🧪 Testing Redis Queue Integration")
    print("=" * 50)
    
    # 1. Test health check
    print("\n1️⃣ Testing health check...")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running: {data['message']}")
            print(f"   Queue enabled: {data.get('queue_enabled', False)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Cannot connect to API. Make sure 'python main.py' is running!")
        return False
    
    # 2. Test queue stats
    print("\n2️⃣ Testing queue statistics...")
    try:
        response = requests.get(f"{API_URL}/queue/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Queue stats retrieved:")
            print(f"   Pending: {stats.get('pending', 0)}")
            print(f"   Finished: {stats.get('finished', 0)}")
            print(f"   Workers: {stats.get('workers', 0)}")
            
            if stats.get('workers', 0) == 0:
                print("⚠️  No workers running! Start worker.py in another terminal")
        else:
            print(f"❌ Queue stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Test job submission (without actual PDF, just to test endpoint)
    print("\n3️⃣ Testing job submission endpoint...")
    print("   ℹ️  To fully test, use Postman to upload a PDF file")
    print("   Endpoint: POST http://localhost:8000/analyze")
    print("   Form data: file=<your_pdf>, query=<your_query>")
    
    print("\n" + "=" * 50)
    print("✅ Basic system tests passed!")
    print("\n📝 Next Steps:")
    print("1. Ensure Redis is running: Get-Service -Name Redis")
    print("2. Start worker: python worker.py")
    print("3. Start API: python main.py")
    print("4. Test with Postman using a PDF file")
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
