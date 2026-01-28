import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_user_flow(user_id, video_url, query_text):
    print(f"\n--- Testing User: {user_id} ---")
    
    # 1. Load Video
    print(f"Loading video: {video_url}")
    video_payload = {
        "url": video_url,
        "id": user_id
    }
    
    conversation_id = None
    try:
        response = requests.post(f"{BASE_URL}/video", json=video_payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                if data.get("type") == "conversation_info":
                    conversation_id = data.get("conversation_id")
                    print(f"Conversation ID: {conversation_id}")
                elif data.get("status") == "complete":
                    print("Video processing complete.")
    except Exception as e:
        print(f"Error loading video: {e}")
        return

    if not conversation_id:
        print("Failed to get conversation_id")
        return

    # 2. Query Video
    print(f"Querying: {query_text}")
    query_payload = {
        "query": query_text,
        "id": user_id,
        "conversation_id": conversation_id
    }
    
    try:
        # Give a small delay to ensure RAG is ready (though processing complete should be enough)
        time.sleep(1)
        response = requests.post(f"{BASE_URL}/query", json=query_payload)
        response.raise_for_status()
        result = response.json()
        print(f"Answer: {result.get('answer')}")
        print(f"Timestamp: {result.get('timestamp')}")
    except Exception as e:
        print(f"Error querying video: {e}")

if __name__ == "__main__":
    # User 1: JavaScript Promises
    test_user_flow(
        user_id="user_js_promises",
        video_url="https://www.youtube.com/watch?v=DHvZLI7Db8E",
        query_text="What are the main states of a JavaScript promise?"
    )
    
    # User 2: .NET Language
    test_user_flow(
        user_id="user_dotnet_lang",
        video_url="https://www.youtube.com/watch?v=MFsYaRnrcPQ",
        query_text="What is the .NET framework and what languages does it support?"
    )
