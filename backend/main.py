from fastapi import FastAPI, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, Response
from services.rag import (
    load_youtube_video_stream,
    query_video,
    clear_vector_store,
    debug_corpus_state,
    debug_retrieve_content,
)
from services.quiz import generate_quiz, generate_remedial_quiz
from services.notes import generate_important_notes_pdf
from services.feedback_agent import feedback_agent
from services.database import mongodb_service
from services.user_service import user_service, UserService
from services.conversation_service import conversation_service
from services.message_service import message_service
from services import security_service
from models.user import User, Token
from models.conversation import ConversationCreate, ConversationResponse
from models.message import MessageCreate, MessageResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query, APIRouter
from contextlib import asynccontextmanager

# --- App Initialization ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://frabjous-basbousa-c6ffc6.netlify.app/",
]


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # Startup
    await mongodb_service.connect()
    await mongodb_service.create_indexes()
    print("Connected to MongoDB and created indexes")
    yield
    # Shutdown
    await mongodb_service.disconnect()
    print("Disconnected from MongoDB")


app = FastAPI(title="YouTube RAG API", version="1.0.0", lifespan=lifespan_context)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
auth_router = APIRouter()
api_router = APIRouter()


# --- Pydantic Models ---
class VideoRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    query: str
    conversation_id: str


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


class QuizResponse(BaseModel):
    questions: List[dict]


class FeedbackRequest(BaseModel):
    feedback_text: str


class FeedbackResponse(BaseModel):
    status: str
    message: str
    stored: bool


# --- Authentication Endpoints ---
@auth_router.post("/google", response_model=Token)
async def login_with_google(
    token: security_service.GoogleToken, user_service: UserService = Depends()
):
    print("DEBUG: Received request for /auth/google")
    try:
        google_user_info = await security_service.verify_google_token(token.credential)
        print(f"DEBUG: Google token verified. User info: {google_user_info}")

        user = await user_service.get_or_create_user_from_google(google_user_info)
        print(f"DEBUG: User retrieved or created: {user.email}")

        access_token = security_service.create_access_token(data={"sub": user.email})
        print("DEBUG: Access token created successfully.")

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        print(f"DEBUG: HTTPException in login_with_google: {e.detail}")
        raise e
    except Exception as e:
        print(f"DEBUG: Exception in login_with_google: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


# --- Protected API Endpoints ---
@api_router.post("/video")
async def load_video(
    request: VideoRequest,
    current_user: User = Depends(security_service.get_current_user),
):
    """Load and process a YouTube video for the authenticated user."""
    try:
        user_id = current_user.id
        existing_conversation = await conversation_service.find_by_video_url(
            user_id=user_id, video_url=request.url
        )

        clear_vector_store(user_id)  # Clear any previous in-memory state for this user

        async def video_processing_stream(conversation_id, is_new):
            import json

            status = "new_conversation" if is_new else "existing_conversation"
            message = (
                "Created new conversation, processing video"
                if is_new
                else "Using existing conversation, reprocessing video for fresh data"
            )

            yield (
                json.dumps(
                    {
                        "type": "conversation_info",
                        "conversation_id": conversation_id,
                        "status": status,
                        "message": message,
                    }
                )
                + "\n"
            )

            for chunk in load_youtube_video_stream(request.url, user_id):
                try:
                    data = json.loads(chunk)
                    if data.get("status") == "completed" and "concepts" in data:
                        await conversation_service.update_conversation(
                            conversation_id=conversation_id, concepts=data["concepts"]
                        )
                except Exception:
                    pass
                yield chunk

        if existing_conversation:
            return StreamingResponse(
                video_processing_stream(existing_conversation.id, is_new=False),
                media_type="application/x-ndjson",
            )

        new_conversation_data = ConversationCreate(
            user_id=user_id, video_url=request.url
        )
        conversation = await conversation_service.create_conversation(
            new_conversation_data
        )

        return StreamingResponse(
            video_processing_stream(conversation.id, is_new=True),
            media_type="application/x-ndjson",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start video processing: {str(e)}"
        )


@api_router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(security_service.get_current_user),
):
    """Query the loaded video with a question and save to database for the authenticated user."""
    try:
        user_id = current_user.id

        user_message = MessageCreate(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=request.query,
            message_type="user",
        )
        await message_service.create_message(user_message)

        result = await query_video(request.query, user_id)

        assistant_message = MessageCreate(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=result["answer"],
            message_type="assistant",
            metadata={"timestamp": result["timestamp"]},
        )
        await message_service.create_message(assistant_message)

        return QueryResponse(answer=result["answer"], timestamp=result["timestamp"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        )


# --- Other Endpoints (can be protected as needed) ---


@app.get("/")
async def root():
    return {"message": "YouTube RAG API", "version": "1.0.0"}


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(api_router, prefix="/api", tags=["Application"])


# --- For running locally ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
