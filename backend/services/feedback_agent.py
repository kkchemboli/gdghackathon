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

        # Initialize Agent Engine
        try:
            # Try to get existing or create
            # In a real scenario, we might want to store the resource name
            self.agent_engine = agent_engines.create()
            print(f"Created Agent Engine: {self.agent_engine.resource_name}")
        except Exception as e:
            print(
                f"Note: Agent Engine creation might have failed or already exists: {e}"
            )
            # Fallback or assume it's handled by environment
            self.agent_engine = None

        self.model_name = "gemini-1.5-pro"
        self.app_name = "feedback_assistant_" + str(uuid.uuid4())[:6]

        # Define ADK Agent
        self.agent = adk.Agent(
            model=self.model_name,
            name="feedback_assistant",
            instruction="""You are a helpful assistant with perfect memory.
                Instructions:
                - Use the context to personalize responses
                - Naturally reference past conversations when relevant
                - Build upon previous knowledge about the user
                - If using semantic search, the memories shown are the most relevant to the current query""",
            tools=[PreloadMemoryTool()],
        )

        # Configure services
        agent_engine_id = self.agent_engine.name if self.agent_engine else "default"

        self.memory_bank_service = VertexAiMemoryBankService(
            project=self.project,
            location=self.location,
            agent_engine_id=agent_engine_id,
        )

        self.session_service = VertexAiSessionService(
            project=self.project,
            location=self.location,
            agent_engine_id=agent_engine_id,
        )

        self.runner = adk.Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
            memory_service=self.memory_bank_service,
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

                # ADK memory storage process:
                # 1. Create a session
                session = await self.runner.session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id,
                )

                # 2. Add the preference to the session history via a call
                # This ensures the memory generation process has context.
                async for event in self.runner.run_async(
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
                completed_session = await self.runner.session_service.get_session(
                    app_name=self.app_name, user_id=user_id, session_id=session.id
                )
                if completed_session:
                    await self.memory_bank_service.add_session_to_memory(
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
