import json
import os
import vertexai
from vertexai.preview import rag
from vertexai.generative_models import GenerativeModel, Tool, SafetySetting
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.youtube import TranscriptFormat
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from typing import Optional, List
from services.feedback_agent import feedback_agent

load_dotenv()

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# RAG is in us-west1, but models might be better supported in us-central1
LOCATION = "us-west1"
MODEL_LOCATION = "us-central1"

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    print("Warning: GCP_PROJECT_ID not set. Vertex AI functionality will fail.")

# Global variables
model = GenerativeModel("gemini-2.5-flash")
BATCH_SIZE = 10

# Per-user in-memory state (Fallbacks for when DB isn't enough or for speed)
# Ideally, transcripts are in Vertex RAG and concepts are in MongoDB.
user_docs = {} # user_id -> List[Document]

def get_or_create_corpus(user_id: str):
    """Get existing corpus for user or create a new one."""
    display_name = f"user-{user_id}"
    try:
        corpora = rag.list_corpora()
        for corpus in corpora:
            if corpus.display_name == display_name:
                return corpus
    except Exception as e:
        print(f"Error listing corpora: {e}")
    return rag.create_corpus(display_name=display_name)

def purge_corpus_files(corpus_name: str):
    """Delete all files in the specified corpus."""
    try:
        files = list(rag.list_files(corpus_name=corpus_name))
        for file in files:
            rag.delete_file(name=file.name)
    except Exception as e:
        print(f"Error purging corpus files: {e}")

def extract_concepts_batch(combined_text: str) -> list:
    """Extract concepts from a combined text block using the LLM."""
    try:
        prompt = f"""You are a helpful assistant. Extract the main concepts or topics discussed in the following text. 
Return a JSON array of concept strings (max 5-10 words each). 
Return ONLY the JSON array, no other text.

Text:
{combined_text}
"""
        response = model.generate_content(prompt)
        content = response.text.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        concepts = json.loads(content)
        return concepts if isinstance(concepts, list) else []
    except Exception as e:
        print(f"Error extracting concepts: {e}")
        return []

def clear_vector_store(user_id: Optional[str] = None):
    """Clear state for a specific user or all users if user_id is None."""
    global user_docs
    if user_id:
        if user_id in user_docs:
            del user_docs[user_id]
    else:
        user_docs = {}

def get_current_docs(user_id: str) -> list:
    """Get the current documents for a user."""
    return user_docs.get(user_id, [])

def load_youtube_video_stream(url: str, user_id: str):
    """Load YouTube video transcript, process, and upload to Vertex RAG yielding progress."""
    try:
        if not PROJECT_ID:
             yield json.dumps({"status": "error", "message": "GCP_PROJECT_ID not set"}) + "\n"
             return

        # Validate URL
        if not url or not isinstance(url, str):
            yield json.dumps({"status": "error", "message": "Invalid URL"}) + "\n"
            return
        
        # Get/Create User Corpus
        yield json.dumps({"status": "progress", "message": "Initializing user knowledge base...", "progress": 5}) + "\n"
        try:
            corpus = get_or_create_corpus(user_id)
            # Ensure fresh start for this video
            purge_corpus_files(corpus.name)
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to access RAG corpus: {str(e)}"}) + "\n"
            return

        # Load Transcript
        yield json.dumps({"status": "progress", "message": "Loading transcript...", "progress": 10}) + "\n"
        try:
            loader = YoutubeLoader.from_youtube_url(
                url,
                add_video_info=False,
                transcript_format=TranscriptFormat.CHUNKS,
                chunk_size_seconds=30,
            )
            documents = loader.load()
        except Exception as e:
             yield json.dumps({"status": "error", "message": f"Failed to load video: {str(e)}"}) + "\n"
             return
        
        if not documents:
            yield json.dumps({"status": "error", "message": "No transcript found"}) + "\n"
            return
        
        # Update user_docs for quiz.py
        user_docs[user_id] = documents

        # Format transcript with timestamps for RAG
        yield json.dumps({"status": "progress", "message": "Processing transcript...", "progress": 20}) + "\n"
        formatted_transcript = ""
        for doc in documents:
            raw_ts = doc.metadata.get('start_timestamp', 0)
            ts_str = "00:00:00"
            
            try:
                # If it's already a formatted string like HH:MM:SS
                if isinstance(raw_ts, str) and ":" in raw_ts:
                    ts_str = raw_ts
                else:
                    # Treat as seconds (int or float)
                    timestamp = int(float(raw_ts))
                    h = timestamp // 3600
                    m = (timestamp % 3600) // 60
                    s = timestamp % 60
                    ts_str = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception:
                # Fallback
                ts_str = "00:00:00"

            formatted_transcript += f"[{ts_str}] {doc.page_content}\n\n"
        
        # Save to temp file
        temp_file_path = f"temp_transcript_{user_id}.txt"
        with open(temp_file_path, "w") as f:
            f.write(formatted_transcript)
            
        # Extract Concepts
        extracted_concepts = set()
        
        # We can do a quick concept extraction on a subset or full text
        # For progress bar niceness, let's do it in a loop
        # But for RAG, the upload is the main part.
        # Let's run concept extraction on chunks.
        
        full_text = formatted_transcript
        # Split purely for concept extraction batches
        text_chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        
        num_batches = len(text_chunks)
        for i, chunk in enumerate(text_chunks):
            batch_concepts = extract_concepts_batch(chunk)
            extracted_concepts.update(batch_concepts)
            
            prog = 20 + int((i+1)/num_batches * 40) # 20 to 60
            yield json.dumps({
                "status": "progress", 
                "message": f"Extracting concepts {i+1}/{num_batches}", 
                "progress": prog
            }) + "\n"

        # Import to Vertex RAG
        yield json.dumps({"status": "progress", "message": "Indexing to Vertex AI...", "progress": 70}) + "\n"
        
        try:
            # Using upload_file for local files
            rag.upload_file(
                corpus_name=corpus.name,
                path=temp_file_path,
                display_name=f"transcript_{user_id}",
                description="Youtube Video Transcript"
            )
            
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            yield json.dumps({
                "status": "completed", 
                "message": "Video processed successfully", 
                "progress": 100,
                "concepts": list(extracted_concepts)
            }) + "\n"
            
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Vertex RAG Import failed: {str(e)}"}) + "\n"
            # Cleanup
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        yield json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"}) + "\n"

async def query_video(query: str, user_id: str) -> dict:
    """Process a query using Vertex RAG with explicit context injection."""
    if not query:
        raise ValueError("Query cannot be empty")
        
    try:
        corpus = get_or_create_corpus(user_id)
        
        # Explicitly retrieve content from the corpus
        retrieval_response = rag.retrieval_query(
            rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
            text=query,
            similarity_top_k=5,
            vector_distance_threshold=0.65
        )
        
        # Build context from retrieved chunks
        context_parts = []
        for ctx in retrieval_response.contexts.contexts:
            context_parts.append(ctx.text)
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."
        
        # Ensure we are initialized in a region that supports the model
        # Try to re-init if us-west1 failed for generative models previously
        vertexai.init(project=PROJECT_ID, location=MODEL_LOCATION)
        
        # Get user memories for personalization
        memories = await feedback_agent.get_user_memories(user_id)
        if memories:
            context = f"{memories}\n\n---\n\n{context}"

        # Generate answer using the retrieved context
        prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context (Youtube Video Transcript).
If the answer is in the context, provide the timestamp from the context in the format HH:MM:SS.
Return your answer in the following JSON format:
{{
  "answer": "string",
  "timestamp": "HH:MM:SS"
}}
If the context doesn't contain the answer, say so and set timestamp to "00:00:00".

CONTEXT:
{context}

USER QUESTION: {query}"""

        response = model.generate_content(prompt)
        
        # Re-init back to RAG location just in case
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Parse response
        text = response.text.strip()
        try:
            # Clean markdown JSON block if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Simple JSON parse
            try:
                res_json = json.loads(text)
                return res_json
            except json.JSONDecodeError:
                # If JSON parse fails, try to find "answer": "..." using regex
                import re
                # This regex looks for the content inside "answer": "..." even if JSON is malformed/truncated
                answer_match = re.search(r'"answer":\s*"(.*?)"(?:\s*,|\s*})', text, re.DOTALL)
                if answer_match:
                    ans = answer_match.group(1).encode().decode('unicode_escape')
                    return {"answer": ans, "timestamp": "00:00:00"}
                
                # If that fails, maybe the LLM just returned the text directly despite the JSON request
                if "###" in text or "**Timestamp:**" in text:
                    return {"answer": text, "timestamp": "00:00:00"}
                
                raise # Go to fallback
                
        except Exception:
            # Fallback if all extraction fails
            return {
                "answer": response.text,
                "timestamp": "00:00:00"
            }
            
    except Exception as e:
        raise Exception(f"Query failed: {str(e)}")

def debug_corpus_state(user_id: str) -> dict:
    """Return the files currently in the user's corpus."""
    try:
        corpus = get_or_create_corpus(user_id)
        files = list(rag.list_files(corpus_name=corpus.name))
        return {
            "corpus_name": corpus.name,
            "display_name": corpus.display_name,
            "created_time": str(corpus.create_time),
            "file_count": len(files),
            "files": [{"name": f.name, "display_name": f.display_name} for f in files]
        }
    except Exception as e:
        return {"error": str(e)}

def debug_retrieve_content(user_id: str, query: str) -> dict:
    """Directly retrieve content from the user's corpus for debugging."""
    try:
        corpus = get_or_create_corpus(user_id)
        
        # Use the rag.retrieval_query to get the raw chunks
        response = rag.retrieval_query(
            rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
            text=query,
            similarity_top_k=3,
            vector_distance_threshold=0.8
        )
        
        chunks = []
        for context in response.contexts.contexts:
            chunks.append({
                "text": context.text[:500],  # Truncate for readability
                "source_uri": context.source_uri,
                "distance": context.distance
            })
        
        return {
            "query": query,
            "chunk_count": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        return {"error": str(e)}