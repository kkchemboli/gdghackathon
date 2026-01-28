import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.getcwd())

from services.feedback_agent import feedback_agent
from services.database import mongodb_service

async def main():
    # Initialize MongoDB connection
    await mongodb_service.connect()
    
    user_id = "test_user_123"
    # A preference that should be remembered
    feedback = "I am a medical student and I prefer explanations with clinical examples."
    
    print(f"--- Processing feedback for {user_id} ---")
    success, message = await feedback_agent.process_feedback(user_id, feedback)
    print(f"Success: {success}, Message: {message}")
    
    print(f"\n--- Retrieving memories for {user_id} ---")
    memories = await feedback_agent.get_user_memories(user_id)
    print(f"Stored Memories:\n{memories}")
    
    # A casual comment that should NOT be remembered
    feedback_casual = "The weather is nice today."
    print(f"\n--- Processing casual feedback for {user_id} ---")
    success, message = await feedback_agent.process_feedback(user_id, feedback_casual)
    print(f"Success: {success}, Message: {message}")

if __name__ == "__main__":
    asyncio.run(main())
