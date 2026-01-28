import requests
import json
import sys

BASE_URL = "http://localhost:8000"
# Use a specific user ID to test the namespace isolation
USER_ID = "test-user-integration"
# Short video for faster processing (Google Cloud tech video or similar)
VIDEO_URL = "https://www.youtube.com/watch?v=iiADhChRriM" 

def test_root():
    """Test if the API is up."""
    print("Testing Root Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("✅ Root endpoint is up.")
    except Exception as e:
        print(f"❌ Failed to contact API: {e}")
        sys.exit(1)

def test_load_video():
    """Test loading a video (streaming response)."""
    print(f"\nTesting /video endpoint with User ID: {USER_ID}...")
    url = f"{BASE_URL}/video"
    payload = {
        "url": VIDEO_URL,
        "id": USER_ID
    }
    
    try:
        # stream=True to handle the ndjson stream
        with requests.post(url, json=payload, stream=True) as response:
            assert response.status_code == 200
            print("✅ /video request accepted. Receiving stream...")
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status")
                    progress = data.get("progress", 0)
                    msg = data.get("message", "")
                    
                    if status == "error":
                        print(f"❌ Error in video stream: {msg}")
                        # We might fail here, but let's see if it's just a transient issue
                        return False
                    
                    print(f"   - [{progress}%] {msg}")
                    
                    if status == "completed":
                        print("✅ Video processing completed.")
                        return True
            return True
            
    except Exception as e:
        print(f"❌ /video request failed: {e}")
        return False

def test_query_video():
    """Test querying the video."""
    print(f"\nTesting /query endpoint...")
    query = "What is this video about?"
    # We need a conversation ID, but the backend implementation for /query 
    # currently takes conversation_id but mostly relies on user_id + RAG retrieval.
    # We can pass a dummy conversation_id for this test.
    
    payload = {
        "query": query,
        "id": USER_ID,
        "conversation_id": "test-conv-123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload)
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer")
            timestamp = data.get("timestamp")
            print(f"✅ Query successful.")
            print(f"   Q: {query}")
            print(f"   A: {answer}")
            print(f"   Timestamp: {timestamp}")
            return True
        else:
            print(f"❌ Query failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ /query request failed: {e}")
        return False

def test_revision_doc():
    """Test generating a revision document."""
    print(f"\nTesting /revision_doc endpoint...")
    
    # Mock some mistakes
    mistakes = [
        {
            "question": "What is the capital of France?",
            "correct_option": "Paris",
            "timestamp": "00:00:10"
        }
    ]
    
    payload = {
        "mistakes": mistakes,
        "user_id": USER_ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/revision_doc", json=payload)
        if response.status_code == 200:
            data = response.json()
            markdown = data.get("markdown_content")
            print(f"✅ Revision Doc generated.")
            print("   Content Preview:", markdown[:100].replace('\n', ' '))
            return True
        else:
            print(f"❌ Revision Doc failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ /revision_doc request failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting Integration Tests on {BASE_URL}")
    print("Ensure the backend server is running (uvicorn main:app --reload)")
    
    test_root()
    if test_load_video():
        test_query_video()
        test_revision_doc()
    else:
        print("\nSkipping subsequent tests because video load failed.")
