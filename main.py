import os
import json
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator, Iterator, Union
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

# Load environment variables from .env file
load_dotenv()

# Configure logging settings for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with metadata
app = FastAPI(title="OpenAI Agent API")

# Configure Cross-Origin Resource Sharing (CORS)
# This allows the API to be accessed from different domains
cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store for document storage and retrieval
vector_store: VectorStore = VectorStore()

# Initialize OpenAI agent with the vector store
agent: OpenAIAgent = OpenAIAgent(vector_store)

# Dictionary to store active WebSocket connections
# Key: client_id, Value: WebSocket connection
active_connections: Dict[str, WebSocket] = {}


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint to verify API is running.

    Returns:
        Dict[str, str]: A simple message indicating the API is operational.
    """
    return {"message": "OpenAI Agent API is running"}


@app.post("/chat", response_model=ChatMessage)
async def chat(request: ChatRequest) -> ChatMessage:
    """
    Process a chat message and get a response from the OpenAI agent.

    Args:
        request (ChatRequest): The chat request containing messages and search preferences.

    Returns:
        ChatMessage: The response from the assistant.

    Raises:
        HTTPException: If there's an error generating the response.
    """
    try:
        response: str = await agent.generate_response(
            request.messages, request.search_web
        )
        return {"role": "assistant", "content": response}
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str) -> None:
    """
    WebSocket endpoint for streaming chat with the OpenAI agent.

    Establishes a persistent connection for real-time streaming of chat responses.

    Args:
        websocket (WebSocket): The WebSocket connection.
        client_id (str): Unique identifier for the client.
    """
    await websocket.accept()
    active_connections[client_id] = websocket

    try:
        while True:
            # Receive message from client
            data: str = await websocket.receive_text()
            request_data: Dict[str, Any] = json.loads(data)

            messages: List[Dict[str, str]] = request_data.get("messages", [])
            search_web: bool = request_data.get("search_web", False)

            # Stream response chunks to the client
            async for chunk in agent.generate_streaming_response(messages, search_web):
                await websocket.send_text(
                    json.dumps({"type": "chunk", "content": chunk})
                )

            # Signal end of response
            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
    finally:
        # Clean up connection when done
        if client_id in active_connections:
            del active_connections[client_id]


@app.post("/stream-chat")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """
    Stream a chat response from the OpenAI agent using HTTP streaming.

    This endpoint provides an alternative to WebSockets for clients
    that support HTTP streaming.

    Args:
        request (ChatRequest): The chat request containing messages and search preferences.

    Returns:
        StreamingResponse: A streaming HTTP response with the generated content.

    Raises:
        HTTPException: If there's an error generating the streaming response.
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
) -> DocumentResponse:
    """
    Upload a document to the vector store for later retrieval and processing.

    Processes the document in the background to avoid blocking the request.

    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks handler.
        file (UploadFile): The file to upload.
        document_id (Optional[str]): Custom ID for the document. If not provided, a UUID will be generated.
        metadata (Optional[str]): JSON string containing metadata for the document.

    Returns:
        DocumentResponse: Information about the uploaded document and its processing status.

    Raises:
        HTTPException: If the file type is unsupported or there's an error uploading the document.
    """
    try:
        # Generate document ID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())

        # Validate file extension
        file_extension: str = get_file_extension(file.filename)
        supported_extensions: List[str] = [".pdf", ".txt", ".md", ".csv", ".json"]

        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(supported_extensions)}",
            )

        # Process file in the background to avoid blocking the request
        file_content: bytes = await file.read()
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
async def list_documents() -> List[Dict[str, Any]]:
    """
    List all documents stored in the vector store.

    Returns:
        List[Dict[str, Any]]: A list of document metadata.

    Raises:
        HTTPException: If there's an error retrieving the document list.
    """
    try:
        documents: List[Dict[str, Any]] = vector_store.list_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> Dict[str, str]:
    """
    Delete a document from the vector store.

    Args:
        document_id (str): The ID of the document to delete.

    Returns:
        Dict[str, str]: Status message indicating successful deletion.

    Raises:
        HTTPException: If the document is not found or there's an error deleting it.
    """
    try:
        success: bool = await vector_store.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vector-stores")
async def get_vector_stores() -> Dict[str, Any]:
    """
    Get information about the vector stores.

    Returns:
        Dict[str, Any]: Metadata and statistics about the vector stores.

    Raises:
        HTTPException: If there's an error retrieving vector store information.
    """
    try:
        info: Dict[str, Any] = await vector_store.get_vector_store_info()
        return info
    except Exception as e:
        logger.error(f"Error getting vector store info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-visualization")
async def create_visualization(prompt: str) -> Dict[str, str]:
    """
    Create a visualization using Canvas based on a text prompt.

    Args:
        prompt (str): The description of the visualization to create.

    Returns:
        Dict[str, str]: The generated visualization data.

    Raises:
        HTTPException: If there's an error creating the visualization.
    """
    try:
        result: str = await agent.create_visualization(prompt)
        return {"visualization": result}
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn server when script is executed directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
