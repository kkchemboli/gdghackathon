import os
import json
import uuid
import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai import agent_engines
from google import adk
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from services.database import mongodb_service


class FeedbackAgent:
    def __init__(self):
        self.project = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "us-central1")

        if self.project:
            vertexai.init(project=self.project, location=self.location)

        self.model_name = "gemini-1.5-pro"
        # We'll use a consistent name for the agent logic, but the engine is unique
        self.agent_name = "feedback_assistant"

        # Define ADK Agent Template
        self.agent = adk.Agent(
            model=self.model_name,
            name=self.agent_name,
            instruction="""You are a helpful assistant with perfect memory.
                Instructions:
                - Use the context to personalize responses
                - Naturally reference past conversations when relevant
                - Build upon previous knowledge about the user
                - If using semantic search, the memories shown are the most relevant to the current query""",
            tools=[PreloadMemoryTool()],
        )

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

    async def _get_user_runner(self, user_id: str):
        """Retrieve or create a reasoning engine for the user and return a Runner."""
        users_collection = mongodb_service.get_collection("users")
        user_doc = await users_collection.find_one({"_id": user_id})

        if not user_doc:
            # Fallback for transient users or create one if needed, 
            # but usually they should be authenticated
            user_doc = {"_id": user_id}

        agent_id = user_doc.get("agent_id")
        agent_engine = None

        if agent_id:
            try:
                print(f"DEBUG: Getting existing Agent Engine for user {user_id}: {agent_id}")
                agent_engine = agent_engines.get(agent_id)
            except Exception as e:
                print(f"DEBUG: Could not get engine {agent_id}, will create new: {e}")
                agent_id = None

        if not agent_id:
            try:
                print(f"DEBUG: Creating new Agent Engine for user {user_id}")
                agent_engine = agent_engines.create()
                agent_id = agent_engine.resource_name
                await users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {"agent_id": agent_id}},
                    upsert=True
                )
                print(f"DEBUG: Created and stored Agent Engine: {agent_id}")
            except Exception as e:
                print(f"ERROR: Failed to create agent engine: {e}")
                raise

        # Initialize Services with this specific engine
        memory_bank_service = VertexAiMemoryBankService(
            project=self.project,
            location=self.location,
            agent_engine_id=agent_id,
        )

        session_service = VertexAiSessionService(
            project=self.project,
            location=self.location,
            agent_engine_id=agent_id,
        )

        app_name = f"feedback_assistant_{user_id[:6]}"

        return adk.Runner(
            agent=self.agent,
            app_name=app_name,
            session_service=session_service,
            memory_service=memory_bank_service,
        ), app_name

    async def process_feedback(self, user_id: str, feedback_text: str):
        """Classify and potentially store user feedback in Memory Bank."""
        print(f"DEBUG: Processing feedback for user {user_id}: {feedback_text}")

        try:
            # Classification call using standard GenerativeModel for internal decision
            model = GenerativeModel(self.model_name)
            prompt = f'{self.classification_prompt}\n\nUser Feedback: "{feedback_text}"'
            response = model.generate_content(prompt)

            # Parse LLM response
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            result = json.loads(raw_text)

            if result.get("worth_remembering"):
                summary = result.get("preference_summary", feedback_text)
                print(f"DEBUG: Feedback worth remembering: {summary}")

                # Get runner dynamically
                runner, app_name = await self._get_user_runner(user_id)

                # ADK memory storage process:
                # 1. Create a session
                session = await runner.session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                )

                # 2. Add the preference to the session history via a call
                # This ensures the memory generation process has context.
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session.id,
                    new_message=types.Content(
                        role="user",
                        parts=[
                            types.Part(text=f"Please note this preference: {summary}")
                        ],
                    ),
                ):
                    pass

                # 3. Retrieve the session and add it to the Memory Bank
                completed_session = await runner.session_service.get_session(
                    app_name=app_name, user_id=user_id, session_id=session.id
                )
                if completed_session:
                    await runner.memory_service.add_session_to_memory(
                        completed_session
                    )

                # Store in MongoDB as a backup/quick cache
                user_memories_collection = mongodb_service.get_collection(
                    "user_memories"
                )
                await user_memories_collection.update_one(
                    {"user_id": user_id},
                    {"$addToSet": {"memories": summary}},
                    upsert=True,
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
            user_memories_collection = mongodb_service.get_collection("user_memories")
            user_data = await user_memories_collection.find_one({"user_id": user_id})
            if user_data and "memories" in user_data and user_data["memories"]:
                memories_list = user_data["memories"]
                return "Known User Preferences & Context:\n" + "\n".join(
                    [f"- {m}" for m in memories_list]
                )
            return ""
        except Exception as e:
            print(f"ERROR retrieving memories: {e}")
            return ""


feedback_agent = FeedbackAgent()
