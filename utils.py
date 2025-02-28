import io
import os
from typing import Dict, Any, List
import logging
from pypdf import PdfReader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.
    """
    _, extension = os.path.splitext(filename.lower())
    return extension


async def process_file(
    file_content: bytes,
    filename: str,
    document_id: str,
    metadata: Dict[str, Any],
    vector_store: VectorStore,
):
    """
    Process a file and add it to the vector store.
    """
    try:
        # Get file extension
        file_extension = get_file_extension(filename)

        # Extract text based on file type
        text = ""
        if file_extension == ".pdf":
            pdf = PdfReader(io.BytesIO(file_content))
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        elif file_extension == ".txt" or file_extension == ".md":
            text = file_content.decode("utf-8")
        elif file_extension == ".csv":
            # Simple CSV handling - more complex handling might be needed
            text = file_content.decode("utf-8")
        elif file_extension == ".json":
            # Simple JSON handling
            text = file_content.decode("utf-8")
        else:
            logger.warning(f"Unsupported file extension: {file_extension}")
            return

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # Create documents
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk": i,
                    **metadata,
                },
            )
            documents.append(doc)

        # Add to vector store
        await vector_store.add_documents(documents, document_id, filename, metadata)

        logger.info(f"Processed file {filename} with {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
