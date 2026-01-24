import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from services.database import mongodb_service

class FeedbackAgent:
    def __init__(self):
        # Using gemini-1.5-flash-002 for better compatibility
        # Ensure we are initialized for the model
        project = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_LOCATION", "us-central1")
        if project:
            vertexai.init(project=project, location=location)
            
        self.model = GenerativeModel("gemini-2.5-pro")
        
        self.classification_prompt = """
You are a specialized AI agent focused on student success. Your goal is to analyze user feedback and decide if it reveals a persistent learning preference, a specific difficulty, or a personal context that should be remembered to improve future tutoring sessions.

Worth Remembering (learning preferences, barriers, specific goals):
- "I find technical terms really hard to follow."
- "Explain things using simple analogies."
- "I prefer short, bulleted notes."
- "I'm a medical student, so focus on clinical applications."
- "English isn't my first language."

NOT Worth Remembering (transient states, unrelated chatter):
- "I'm feeling a bit sleepy."
- "The weather is nice today."
- "I'm eating a sandwich."
- "This video is 10 minutes long." (Fact about the content, not a preference)

Output only a JSON object with:
{
  "worth_remembering": boolean,
  "preference_summary": "a concise, third-person summary of the preference (e.g., 'User finds technical terms hard to follow')",
  "reason": "brief explanation"
}
"""

    async def process_feedback(self, user_id: str, feedback_text: str):
        """Classify and potentially store user feedback."""
        print(f"DEBUG: Processing feedback for user {user_id}: {feedback_text}")
        
        try:
            # Classification call
            prompt = f"{self.classification_prompt}\n\nUser Feedback: \"{feedback_text}\""
            response = self.model.generate_content(prompt)
            
            # Parse LLM response
            raw_text = response.text.strip()
            # Clean up potential markdown blocks
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(raw_text)
            
            if result.get("worth_remembering"):
                summary = result.get("preference_summary", feedback_text)
                print(f"DEBUG: Feedback worth remembering: {summary}")
                
                # Store in MongoDB
                # We'll use a collection called 'user_memories'
                await mongodb_service.db.user_memories.update_one(
                    {"user_id": user_id},
                    {"$addToSet": {"memories": summary}},
                    upsert=True
                )
                return True, f"Memory stored: {summary}"
            else:
                print("DEBUG: Feedback ignored (not worth remembering)")
                return False, "Feedback acknowledged but not stored as a preference."
                
        except Exception as e:
            print(f"ERROR in FeedbackAgent: {str(e)}")
            return False, f"Error processing feedback: {str(e)}"

    async def get_user_memories(self, user_id: str) -> str:
        """Retrieve stored memories for prompt injection."""
        try:
            user_data = await mongodb_service.db.user_memories.find_one({"user_id": user_id})
            if user_data and "memories" in user_data and user_data["memories"]:
                memories_list = user_data["memories"]
                return "Known User Preferences & Context:\n" + "\n".join([f"- {m}" for m in memories_list])
            return ""
        except Exception as e:
            print(f"ERROR retrieving memories: {e}")
            return ""

feedback_agent = FeedbackAgent()
