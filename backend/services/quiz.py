import json
from typing import List, Dict
from services import rag
from langchain_core.messages import HumanMessage, SystemMessage

def generate_quiz() -> List[Dict]:
    """
    Generates a quiz based on the content in the vector store.
    Returns a list of dictionaries, where each dictionary represents a question.
    """
    try:
        # Get all documents from the global in-memory store
        documents = rag.current_docs

        if not documents:
            raise ValueError("No video loaded. Please load a video first.")

        # Construct context from documents
        context_parts = []
        for doc in documents:
            # Document object from LangChain should have metadata with timestamp
            timestamp = doc.metadata.get("start_timestamp", "00:00:00")
            context_parts.append(f"[Timestamp: {timestamp}]\n{doc.page_content}")
        
        # Limit context size if necessary, but for now we'll try to use a good chunk of it
        # Since we want to cover the whole video, we pass as much as possible fitting in context.
        # If it's too large, we might need a strategy (summarization or sampling), 
        # but let's assume it fits for hackathon scale.
        full_context = "\n\n".join(context_parts)
        
        system_prompt = """You are a helpful education assistant.
Your task is to generate a quiz based on the provided video transcript segments.
Create 5 to 10 multiple-choice questions that test the user's understanding of the key concepts.

Return the output strictly as a JSON array of objects. Each object must have the following fields:
- "question": The question string.
- "options": An array of 4 string options.
- "correct_option": The string text of the correct option (must be one of the options).
- "timestamp": The timestamp string (HH:MM:SS) where this topic is discussed.

Do not include any markdown formatting (like ```json), just the raw JSON string.
"""

        user_prompt = f"""Here is the transcript of the video:

{full_context}

Generate the quiz JSON now.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = rag.model.invoke(messages)
        content = response.content.strip()
        
        # Clean up code blocks if present (the model might add them despite instructions)
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        quiz_data = json.loads(content)
        
        # Handle case where LLM wraps the list in a dict (e.g., {"questions": [...]})
        if isinstance(quiz_data, dict):
            if "questions" in quiz_data and isinstance(quiz_data["questions"], list):
                quiz_data = quiz_data["questions"]
            elif "quiz" in quiz_data and isinstance(quiz_data["quiz"], list):
                quiz_data = quiz_data["quiz"]
            else:
                 # Attempt to find any list in values
                 for val in quiz_data.values():
                     if isinstance(val, list):
                         quiz_data = val
                         break
        
        if not isinstance(quiz_data, list):
            raise ValueError("Model output is not a list of questions")

        return quiz_data

    except Exception as e:
        print(f"Error generating quiz: {e}")
        # In case of error, ensuring we don't crash everything, but maybe re-raise tailored error
        raise ValueError(f"Failed to generate quiz: {str(e)}")

def generate_remedial_quiz(mistakes: List[Dict]) -> List[Dict]:
    """
    Generates a remedial quiz based on the user's mistakes.
    """
    try:
        if not mistakes:
            return generate_quiz() # Fallback to generic quiz if no mistakes provided (though logic should prevent this call)
            
        mistakes_context = "\n".join([f"- Question: {m.get('question')}\n  Correct Answer: {m.get('correct_option')}" for m in mistakes])

        system_prompt = """You are a helpful education assistant.
Your task is to generate a REMEDIAL quiz based on the concepts related to the user's mistakes.
The user struggled with the following questions. Identify the underlying concepts and create 5 NEW multiple-choice questions to test these specific concepts again.

Return the output strictly as a JSON array of objects. Each object must have the following fields:
- "question": The question string.
- "options": An array of 4 string options.
- "correct_option": The string text of the correct option (must be one of the options).
- "timestamp": The timestamp string (HH:MM:SS) where this topic is discussed (you may need to infer or leave as 'N/A' if unknown, but best effort).

Do not include any markdown formatting just the raw JSON string.
"""

        user_prompt = f"""These were the questions I got wrong:

{mistakes_context}

Generate 5 new questions to help me learn these concepts.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = rag.model.invoke(messages)
        content = response.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        quiz_data = json.loads(content)
        
        # Handle case where LLM wraps the list in a dict
        if isinstance(quiz_data, dict):
            if "questions" in quiz_data and isinstance(quiz_data["questions"], list):
                quiz_data = quiz_data["questions"]
            elif "quiz" in quiz_data and isinstance(quiz_data["quiz"], list):
                quiz_data = quiz_data["quiz"]
            else:
                 for val in quiz_data.values():
                     if isinstance(val, list):
                         quiz_data = val
                         break

        if not isinstance(quiz_data, list):
             raise ValueError("Model output is not a list of questions")

        return quiz_data

    except Exception as e:
        print(f"Error generating remedial quiz: {e}")
        raise ValueError(f"Failed to generate remedial quiz: {str(e)}")
