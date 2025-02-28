# allianz-agent-poc
POC of Insurance agent for Allianz


# OpenAI Assistant FastAPI Application

A powerful FastAPI application that integrates with OpenAI's Assistants API to create an intelligent chat system with vector store capabilities, web search, and visualization tools.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Usage Guide](#usage-guide)
  - [Managing Documents](#managing-documents)
  - [Chat Interactions](#chat-interactions)
  - [Visualizations](#visualizations)
- [API Reference](#api-reference)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

This application creates a robust backend that leverages OpenAI's latest Assistants API to provide intelligent responses based on:

1. Your uploaded documents (using vector stores for semantic search)
2. Web search results (using SerpAPI)
3. Visualization capabilities (using OpenAI's DALL-E)

It provides both synchronous and streaming API endpoints, WebSocket support, and comprehensive document management functionality, all packaged in a clean FastAPI structure.

## Features

- **Document Management**:
  - Upload various file types (PDF, TXT, MD, CSV, JSON)
  - Automatic chunking and processing of documents
  - Storage in OpenAI's vector stores for semantic search
  - Document listing and deletion capabilities

- **Intelligent Chat**:
  - Contextual responses based on uploaded documents
  - Integration with web search for up-to-date information
  - Support for conversation history
  - Multiple response formats (synchronous, HTTP streaming, WebSockets)

- **Visualization**:
  - Create visualizations using OpenAI's DALL-E integration
  - Generate charts, diagrams, and other visual aids based on prompts

- **Advanced Features**:
  - Automatic citation of sources from documents
  - Intelligent assistant caching for performance
  - Background processing of document uploads
  - Robust error handling and logging

## Architecture

The application is structured around several key components:

- **FastAPI Application** (`main.py`): Defines all API endpoints and coordinates between components
- **OpenAI Agent** (`agent.py`): Manages interactions with OpenAI's Assistants API
- **Vector Store** (`vector_store.py`): Handles document storage and integration with OpenAI's vector stores
- **Utilities** (`utils.py`): Provides file processing and text extraction functions
- **Data Models** (`models.py`): Defines Pydantic models for request/response validation

## Setup and Installation

### Prerequisites

- Python 3.8+
- OpenAI API key with access to the Assistants API
- SerpAPI key (for web search functionality)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd openai-assistant-fastapi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment variables**:
   Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SERPAPI_API_KEY=your_serpapi_api_key
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```
   The server will start at http://localhost:8000

## Usage Guide

### Managing Documents

#### Uploading Documents

You can upload documents through the `/upload-document` endpoint:

```bash
# Using curl
curl -X POST -F "file=@/path/to/your/document.pdf" http://localhost:8000/upload-document
```

The system will:
1. Process the document in the background
2. Extract text from the document
3. Split it into chunks
4. Add it to the OpenAI vector store
5. Return a document ID that you can reference later

#### Listing Documents

To see all uploaded documents:

```bash
curl http://localhost:8000/documents
```

#### Deleting Documents

To remove a document from the system:

```bash
curl -X DELETE http://localhost:8000/documents/{document_id}
```

### Chat Interactions

You can interact with the assistant through three different endpoints:

#### Standard Chat

For simple question-answer interactions:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What information can you find about X in my documents?"}],"search_web":false}' \
  http://localhost:8000/chat
```

#### Streaming Chat (HTTP)

For real-time streaming responses via HTTP:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Analyze the data in my documents"}],"search_web":false}' \
  http://localhost:8000/stream-chat
```

#### WebSocket Chat

For interactive streaming responses:

```javascript
// JavaScript example
const socket = new WebSocket('ws://localhost:8000/ws/chat/user123');

socket.onopen = () => {
  socket.send(JSON.stringify({
    messages: [{role: "user", content: "What trends do you see in my financial documents?"}],
    search_web: true
  }));
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "chunk") {
    console.log(data.content); // Display streaming response
  } else if (data.type === "end") {
    console.log("Response complete");
  }
};
```

### Visualizations

To generate visualizations based on your documents:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"prompt":"Create a chart showing the key metrics from my financial documents"}' \
  http://localhost:8000/create-visualization
```

## API Reference

### Document Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload-document` | POST | Upload a document to the vector store |
| `/documents` | GET | List all uploaded documents |
| `/documents/{document_id}` | DELETE | Delete a specific document |
| `/vector-stores` | GET | Get information about vector stores |

### Chat Interactions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Get a response from the assistant |
| `/stream-chat` | POST | Stream a response using HTTP streaming |
| `/ws/chat/{client_id}` | WebSocket | Stream a response using WebSockets |

### Visualizations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create-visualization` | POST | Generate a visualization using DALL-E |

## Advanced Usage

### Enabling Web Search

To allow the assistant to search the web for supplementary information, set the `search_web` parameter to `true`:

```json
{
  "messages": [
    {"role": "user", "content": "Compare the information in my documents with current market trends"}
  ],
  "search_web": true
}
```

### Conversation Context

The assistant maintains conversation context across multiple messages. To continue a conversation, include previous messages:

```json
{
  "messages": [
    {"role": "user", "content": "What are the key financial metrics in my documents?"},
    {"role": "assistant", "content": "Based on your documents, the key financial metrics are..."},
    {"role": "user", "content": "How have these metrics changed over time?"}
  ],
  "search_web": false
}
```

### Custom Metadata

When uploading documents, you can include custom metadata:

```bash
curl -X POST -F "file=@document.pdf" -F "metadata={\"category\":\"finance\",\"year\":2023}" http://localhost:8000/upload-document
```

## Troubleshooting

### Common Issues

1. **Vector Store Processing Failed**:
   - Check your OpenAI API key has proper permissions
   - Ensure file size is within limits (512MB per file)
   - Try re-uploading the document

2. **Response Generation Errors**:
   - Check API keys are valid
   - Ensure you've uploaded documents if you're asking about document content
   - Check for rate limiting issues

3. **File Format Issues**:
   - Ensure your files are in supported formats (PDF, TXT, MD, CSV, JSON)
   - For PDFs, ensure they contain extractable text (not just scanned images)

### Logs

Check the application logs for detailed information about errors:

```bash
grep ERROR app.log
```

---

## Acknowledgements

This project uses OpenAI's Assistants API and SerpAPI for web search capabilities.