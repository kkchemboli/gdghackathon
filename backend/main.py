from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, Response
from services.rag import load_youtube_video_stream, query_video, clear_vector_store, debug_corpus_state, debug_retrieve_content
from services.quiz import generate_quiz, generate_remedial_quiz
from services.notes import generate_important_notes_pdf
from services.feedback_agent import feedback_agent
from services.database import mongodb_service
from services.user_service import user_service
from services.conversation_service import conversation_service
from services.message_service import message_service
from models.user import User, UserCreate
from models.conversation import ConversationCreate, ConversationResponse
from models.message import MessageCreate, MessageResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from contextlib import asynccontextmanager

origins = ["http://localhost", "http://localhost:3000", "http://localhost:5173","https://frabjous-basbousa-c6ffc6.netlify.app/"]



@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # Startup
    await mongodb_service.connect()
    await mongodb_service.create_indexes()
    print("Connected to Firestore and created indexes")
    yield
    # Shutdown
    await mongodb_service.disconnect()
    print("Disconnected from Firestore")


app = FastAPI(title="YouTube RAG API", version="1.0.0", lifespan=lifespan_context)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await mongodb_service.connect()
    await mongodb_service.create_indexes()
    print("Connected to Firestore and created indexes")
    yield
    # Shutdown
    await mongodb_service.disconnect()
    print("Disconnected from Firestore")


app.router.lifespan_context = lifespan


class VideoRequest(BaseModel):
    url: str
    id: str


class QueryRequest(BaseModel):
    query: str
    id: str
    conversation_id: str


class VideoResponse(BaseModel):
    status: str
    message: str


class QueryResponse(BaseModel):
    answer: str
    timestamp: str


class WrongQuestion(BaseModel):
    question: str
    correct_option: str
    timestamp: str


class RevisionRequest(BaseModel):
    mistakes: List[WrongQuestion]


class RevisionResponse(BaseModel):
    markdown_content: str


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_option: str
    timestamp: str


class QuizRequest(BaseModel):
    user_id: str


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]


class FeedbackRequest(BaseModel):
    user_id: str
    feedback_text: str


class FeedbackResponse(BaseModel):
    status: str
    message: str
    stored: bool


@app.post("/video")
async def load_video(request: VideoRequest):
    """Load and process a YouTube video for a specific user."""
    try:
        # Check if conversation already exists for this user and video URL
        existing_conversation = await conversation_service.find_by_video_url(
            user_id=request.id, video_url=request.url
        )

        # Clear vector store globals (for quiz compatibility)
        clear_vector_store()

        if existing_conversation:
            # Video already processed, use existing conversation but process video anyway
            async def video_processing_stream():
                import json
                print(f"DEBUG: Processing existing video for conversation {existing_conversation.id}")
                
                # First, yield the existing conversation info
                yield (
                    json.dumps(
                        {
                            "type": "conversation_info",
                            "conversation_id": existing_conversation.id,
                            "status": "existing_conversation",
                            "message": "Using existing conversation, reprocessing video for fresh data",
                        }
                    )
                    + "\n"
                )

                # Then stream the video processing updates
                # Pass user_id (request.id) to RAG
                for chunk in load_youtube_video_stream(request.url, request.id):
                    try:
                        data = json.loads(chunk)
                        if data.get("status") == "completed" and "concepts" in data:
                            print(f"DEBUG: Saving {len(data['concepts'])} concepts for conversation {existing_conversation.id}")
                            await conversation_service.update_conversation(
                                conversation_id=existing_conversation.id,
                                concepts=data["concepts"]
                            )
                            print(f"DEBUG: Successfully saved concepts.")
                    except Exception as e:
                        print(f"DEBUG: Error parsing chunk for concepts: {e}")
                    yield chunk

            return StreamingResponse(
                video_processing_stream(), media_type="application/x-ndjson"
            )

        # No existing conversation, create new one
        conversation_data = ConversationCreate(
            user_id=request.id,
            video_url=request.url,
            title=None,  # Could be extracted from URL if needed
        )
        conversation = await conversation_service.create_conversation(conversation_data)

        # Create a generator that yields conversation info first, then processing
        async def video_processing_stream():
            import json
            print(f"DEBUG: Processing NEW video for conversation {conversation.id}")

            # First, yield the new conversation info
            yield (
                json.dumps(
                    {
                        "type": "conversation_info",
                        "conversation_id": conversation.id,
                        "status": "new_conversation",
                        "message": "Created new conversation, processing video",
                    }
                )
                + "\n"
            )

            # Then stream the video processing updates
            # Pass user_id (request.id) to RAG
            for chunk in load_youtube_video_stream(request.url, request.id):
                try:
                    data = json.loads(chunk)
                    if data.get("status") == "completed" and "concepts" in data:
                        print(f"DEBUG: Saving {len(data['concepts'])} concepts for conversation {conversation.id}")
                        await conversation_service.update_conversation(
                            conversation_id=conversation.id,
                            concepts=data["concepts"]
                        )
                        print(f"DEBUG: Successfully saved concepts.")
                except Exception as e:
                    print(f"DEBUG: Error parsing chunk for concepts: {e}")
                yield chunk

        return StreamingResponse(
            video_processing_stream(), media_type="application/x-ndjson"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start video processing: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the loaded video with a question and save to database."""
    try:
        # Save user message
        user_message = MessageCreate(
            conversation_id=request.conversation_id,
            user_id=request.id,
            content=request.query,
            message_type="user",
        )
        await message_service.create_message(user_message)

        # Process query with RAG, passing user_id
        result = await query_video(request.query, request.id)

        # Save assistant response
        assistant_message = MessageCreate(
            conversation_id=request.conversation_id,
            user_id=request.id,
            content=result["answer"],
            message_type="assistant",
            metadata={"timestamp": result["timestamp"]},
        )
        await message_service.create_message(assistant_message)

        return QueryResponse(answer=result["answer"], timestamp=result["timestamp"])

    except ValueError as e:
        # Invalid query or no video loaded
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Agent or processing errors
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        )


class RevisionRequest(BaseModel):
    mistakes: List[WrongQuestion]
    user_id: str = "demo-user"  # Default for backward compatibility


@app.post("/revision_doc", response_model=RevisionResponse)
async def generate_revision_doc(request: RevisionRequest):
    """Generate a revision document for incorrect questions."""
    try:
        markdown_content = "# Revision Document\n\n"

        for i, mistake in enumerate(request.mistakes, 1):
            # Construct a query to explain the concept
            query = f"Explain the concept behind this question: '{mistake.question}'. The correct answer is '{mistake.correct_option}'. Provide a concise explanation."

            # Query the RAG system using user_id
            try:
                result = await query_video(query, request.user_id)
                answer = result["answer"]
                timestamp = result["timestamp"]
            except Exception as e:
                answer = "Could not generate explanation."
                timestamp = "00:00:00"
                print(f"Error querying for mistake {i}: {e}")

            # Append to markdown
            markdown_content += f"## {i}. Question: {mistake.question}\n\n"
            markdown_content += f"**Correct Option:** {mistake.correct_option}\n"
            markdown_content += f"**Your Timestamp:** {mistake.timestamp}\n\n"
            markdown_content += f"### Concept & Explanation\n"
            markdown_content += f"{answer}\n\n"
            markdown_content += f"**Watch from:** {timestamp}\n\n"
            markdown_content += "---\n\n"

        return RevisionResponse(markdown_content=markdown_content)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate revision document: {str(e)}"
        )


@app.post("/create_quiz", response_model=QuizResponse)
async def create_quiz_endpoint(request: QuizRequest):
    """Generate a quiz from the loaded video for a specific user."""
    try:
        questions_data = generate_quiz(request.user_id)
        return QuizResponse(questions=questions_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate quiz: {str(e)}"
        )


@app.post("/learn_from_mistakes", response_model=QuizResponse)
async def learn_from_mistakes_endpoint(request: RevisionRequest):
    """Generate a remedial quiz based on user mistakes."""
    try:
        # Convert Pydantic models to list of dicts for the service
        mistakes_dicts = [m.dict() for m in request.mistakes]
        questions_data = generate_remedial_quiz(mistakes_dicts, request.user_id)
        return QuizResponse(questions=questions_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate remedial quiz: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "YouTube RAG API", "version": "1.0.0"}


# User endpoints
@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    try:
        return await user_service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{id}", response_model=User)
async def get_user(id: str):
    user = await user_service.get_user(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Conversation endpoints
@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    try:
        return await conversation_service.create_conversation(conversation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{id}", response_model=List[ConversationResponse])
async def get_user_conversations(id: str):
    try:
        return await conversation_service.get_user_conversations(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Message endpoints
@app.post("/messages", response_model=MessageResponse)
async def create_message(message: MessageCreate):
    try:
        return await message_service.create_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    try:
        return await message_service.get_conversation_messages(
            conversation_id, page, limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/important_notes")
async def get_important_notes(user_id: str, conversation_id: str):
    """Generate and return important notes PDF."""
    try:
        print(f"DEBUG: get_important_notes called with user_id={user_id}, conversation_id={conversation_id}")
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            print(f"DEBUG: Conversation {conversation_id} not found")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        concepts = conversation.concepts
        print(f"DEBUG: Found {len(concepts)} concepts: {concepts}")
        pdf_bytes = await generate_important_notes_pdf(user_id, concepts)
        print(f"DEBUG: PDF generated successfully, size={len(pdf_bytes)}")
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        print(f"ERROR in get_important_notes: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class UpdateNotesRequest(BaseModel):
    notes_url: str


@app.put("/conversations/{conversation_id}/notes")
async def update_conversation_notes(conversation_id: str, request: UpdateNotesRequest):
    """Update conversation with generated notes URL."""
    try:
        conversation = await conversation_service.update_conversation(
            conversation_id, request.notes_url
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update conversation: {str(e)}"
        )


@app.get("/debug/corpus/{user_id}")
async def get_corpus_debug(user_id: str):
    """Debug endpoint to inspect the user's RAG corpus state."""
    return debug_corpus_state(user_id)


@app.get("/debug/retrieve/{user_id}")
async def debug_retrieve(user_id: str, q: str = "What is this video about?"):
    """Debug endpoint to retrieve content directly from the RAG corpus."""
    return debug_retrieve_content(user_id, q)


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for agent personalization."""
    stored, message = await feedback_agent.process_feedback(
        request.user_id, request.feedback_text
    )
    return FeedbackResponse(
        status="success" if stored else "acknowledged",
        message=message,
        stored=stored,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
