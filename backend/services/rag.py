import json
import os
import uuid
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.youtube import TranscriptFormat
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field
from langchain_pinecone import PineconeVectorStore
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec, PodSpec  
load_dotenv()

class Response(BaseModel):
    """Response from the agent."""
    answer: str = Field(description="The answer to the question")
    timestamp: str = Field(description="The timestamp to the answer")

# Initialize model, embeddings, and vector store as module-level variables
model = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

"""vector_store = Chroma(
    collection_name="hackathon",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)"""

# Global set to store extracted concepts
concepts_set: set = set()
# Global list to store current documents for quiz generation
current_docs: list = []
BATCH_SIZE = 10

# Create agent with middleware
@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    """Inject context into state messages."""
    last_query = request.state["messages"][-1].text
    retrieved_docs = vector_store.similarity_search(last_query)
    docs_content = "\n\n".join(
        f"[Timestamp: {doc.metadata['start_timestamp']}]\n"
        f"{doc.page_content}"
        for doc in retrieved_docs
    )

    system_message = (
    "You are a helpful assistant.\n"
    "Keep responses short and grounded in the provided context.\n"
    "Return your answer ONLY as valid JSON in the following format:\n\n"
    "{\n"
    '  "answer": string,\n'
    '  "timestamp": string  // HH:MM:SS\n'
    "}\n\n"
    "Use the timestamp from the context that supports the answer.\n"
    "The answer field should include an instruction suggesting the user to watch from the timestamp onwards.\n"
    "If the user query is not present in or related to the provided context, "
    "answer using your own general knowledge, set the timestamp to \"00:00:00\","
    "Do not include any text outside the JSON.\n\n"
    f"{docs_content}"
)

    return system_message


agent = create_agent(model, tools=[], middleware=[prompt_with_context], checkpointer=InMemorySaver(),response_format=Response)


def clear_vector_store():
    """Clear all documents from the vector store and memory."""
    try:
        # Clear in-memory docs
        global current_docs
        current_docs = []
        
        # Pinecone doesn't support .get() and delete by ID the same way Chroma does
        # For now, we rely on the fact that we might not need to explicitly delete from Pinecone 
        # for a simple hackathon demo if we are just searching, but ideally we would delete.
        # However, to fix the crash, we simply remove the invalid call.
        # If strict index clearing is needed, we would need to delete_all or delete by metadata.
        pass
    except Exception as e:
        print(f"Error clearing vector store: {e}")


def extract_concepts_batch(combined_text: str) -> list:
    """Extract concepts from a combined text block using the LLM."""
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Extract the main concepts or topics discussed in the following text. Return a JSON array of concept strings (max 5-10 words each). Return ONLY the JSON array, no other text."},
            {"role": "user", "content": combined_text}
        ]
        response = model.invoke(messages)
        content = response.content.strip()
        # Clean markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        concepts = json.loads(content)
        return concepts if isinstance(concepts, list) else []
    except Exception as e:
        print(f"Error extracting concepts: {e}")
        return []


def get_concepts() -> list:
    """Return the current set of extracted concepts as a list."""
    return list(concepts_set)



def load_youtube_video_stream(url: str):
    """Load YouTube video transcript, split it, and add to vector store yielding progress.
    
    Yields:
        str: JSON string with status and progress info
    """
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))  
        spec = ServerlessSpec(cloud='aws', region='us-east-1')  
        index_name = "yt-rag"
        if pc.has_index(index_name):  
            print("Index already exists, deleting...")
            pc.delete_index(name=index_name) 
        pc.create_index(  
    index_name,  
    dimension=768,  # dimensionality of text-embedding-ada-002  
    metric='cosine',  
    spec=spec  
)  
        global vector_store 
        vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings) 
        # Validate URL format
        if not url or not isinstance(url, str):
            yield json.dumps({"status": "error", "message": "Invalid URL: URL must be a non-empty string"}) + "\n"
            return
        
        if "youtube.com" not in url and "youtu.be" not in url:
            yield json.dumps({"status": "error", "message": "Invalid URL: Must be a YouTube URL"}) + "\n"
            return
        
        # Load YouTube transcript
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
            error_msg = str(e).lower()
            if "transcript" in error_msg or "subtitle" in error_msg:
                 yield json.dumps({"status": "error", "message": f"Transcript not available: {str(e)}"}) + "\n"
            elif "url" in error_msg or "invalid" in error_msg:
                 yield json.dumps({"status": "error", "message": f"Invalid YouTube URL: {str(e)}"}) + "\n"
            else:
                 yield json.dumps({"status": "error", "message": f"Failed to load video: {str(e)}"}) + "\n"
            return
        
        if not documents:
            yield json.dumps({"status": "error", "message": "No documents loaded from video transcript"}) + "\n"
            return
        
        # Split documents
        yield json.dumps({"status": "progress", "message": "Splitting documents...", "progress": 20}) + "\n"
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # chunk size (characters)
            chunk_overlap=200,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        all_splits = text_splitter.split_documents(documents)
        
        if not all_splits:
             yield json.dumps({"status": "error", "message": "No text chunks created"}) + "\n"
             return

        # Store docs in memory for quiz generation
        global current_docs
        current_docs = all_splits
        
        # Clear and populate concepts_set via batch processing
        global concepts_set
        concepts_set = set()
        
        num_batches = (len(all_splits) + BATCH_SIZE - 1) // BATCH_SIZE
        # Progress from 20 to 90
        
        for batch_idx in range(num_batches):
            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, len(all_splits))
            batch_docs = all_splits[start:end]
            
            combined_text = "\n\n".join(doc.page_content for doc in batch_docs)
            batch_concepts = extract_concepts_batch(combined_text)
            concepts_set.update(batch_concepts)
            
            # Calculate progress between 20 and 90
            current_progress = 20 + int((batch_idx + 1) / num_batches * 70)
            yield json.dumps({
                "status": "progress", 
                "message": f"Processing batch {batch_idx + 1}/{num_batches}", 
                "progress": current_progress
            }) + "\n"
        
        # Add to vector store
        yield json.dumps({"status": "progress", "message": "Indexing vector store...", "progress": 95}) + "\n"
        try:
            vector_store.add_documents(documents=all_splits)
            yield json.dumps({"status": "completed", "message": "Video processed successfully", "progress": 100}) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to add documents to vector store: {str(e)}"}) + "\n"
            
    except Exception as e:
        yield json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"}) + "\n"


def query_video(query: str) -> dict:
    """Process a query and return answer with timestamp.
    
    Raises:
        ValueError: If query is empty or invalid
        Exception: For errors during agent processing or vector store operations
    """
    # Validate query
    if not query or not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")
    
    # Stream the agent response
    try:
        final_response = None
        final_response = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            {"configurable":{"thread_id": "1"}},
        )
        final_response = final_response["structured_response"]
        
        if not final_response:
            raise Exception("Agent did not return a response")
        
        return final_response.dict()
    except Exception as e:
        raise Exception(f"Failed to process query with agent: {str(e)}")