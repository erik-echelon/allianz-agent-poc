import os
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import uvicorn
import logging
from dotenv import load_dotenv

from models import ChatMessage, ChatRequest, DocumentResponse
from agent import OpenAIAgent
from vector_store import VectorStore
from utils import process_file, get_file_extension

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="OpenAI Agent API")

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store
vector_store = VectorStore()

# Initialize OpenAI agent
agent = OpenAIAgent(vector_store)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@app.get("/")
async def root():
    return {"message": "OpenAI Agent API is running"}


@app.post("/chat", response_model=ChatMessage)
async def chat(request: ChatRequest):
    """
    Process a chat message and get a response from the OpenAI agent.
    """
    try:
        response = await agent.generate_response(request.messages, request.search_web)
        return {"role": "assistant", "content": response}
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for streaming chat with the OpenAI agent.
    """
    await websocket.accept()
    active_connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)

            messages = request_data.get("messages", [])
            search_web = request_data.get("search_web", False)

            async for chunk in agent.generate_streaming_response(messages, search_web):
                await websocket.send_text(
                    json.dumps({"type": "chunk", "content": chunk})
                )

            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
    finally:
        if client_id in active_connections:
            del active_connections[client_id]


@app.post("/stream-chat")
async def stream_chat(request: ChatRequest):
    """
    Stream a chat response from the OpenAI agent using HTTP streaming.
    """
    try:
        return StreamingResponse(
            agent.generate_streaming_response(request.messages, request.search_web),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error generating streaming response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-document", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
):
    """
    Upload a document to the vector store.
    """
    try:
        if document_id is None:
            document_id = str(uuid.uuid4())

        file_extension = get_file_extension(file.filename)
        supported_extensions = [".pdf", ".txt", ".md", ".csv", ".json"]

        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(supported_extensions)}",
            )

        # Process file in the background
        file_content = await file.read()
        background_tasks.add_task(
            process_file,
            file_content,
            file.filename,
            document_id,
            json.loads(metadata),
            vector_store,
        )

        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processing",
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=List[Dict[str, Any]])
async def list_documents():
    """
    List all documents in the vector store.
    """
    try:
        documents = vector_store.list_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the vector store.
    """
    try:
        success = await vector_store.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vector-stores")
async def get_vector_stores():
    """
    Get information about the vector stores.
    """
    try:
        info = await vector_store.get_vector_store_info()
        return info
    except Exception as e:
        logger.error(f"Error getting vector store info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-visualization")
async def create_visualization(prompt: str):
    """
    Create a visualization using Canvas.
    """
    try:
        result = await agent.create_visualization(prompt)
        return {"visualization": result}
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
