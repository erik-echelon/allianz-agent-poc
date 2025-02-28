import io
import os
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import logging
from pypdf import PdfReader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from vector_store import VectorStore

# Configure logging for the utils module
logger = logging.getLogger(__name__)


def get_file_extension(filename: str) -> str:
    """
    Extract the file extension from a filename.

    Args:
        filename (str): The name of the file, including its extension.

    Returns:
        str: The lowercase file extension including the dot (e.g., ".pdf").

    Examples:
        >>> get_file_extension("document.PDF")
        ".pdf"
        >>> get_file_extension("data.csv")
        ".csv"
        >>> get_file_extension("readme")
        ""
    """
    _, extension = os.path.splitext(filename.lower())
    return extension


async def process_file(
    file_content: bytes,
    filename: str,
    document_id: str,
    metadata: Dict[str, Any],
    vector_store: VectorStore,
) -> None:
    """
    Process a file and add it to the vector store.

    This function:
    1. Extracts text from various file types (PDF, TXT, MD, CSV, JSON)
    2. Splits the text into manageable chunks
    3. Creates Document objects with metadata
    4. Adds the documents to the vector store

    Args:
        file_content (bytes): The binary content of the file.
        filename (str): The name of the file.
        document_id (str): A unique identifier for the document.
        metadata (Dict[str, Any]): Additional metadata to store with the document.
        vector_store (VectorStore): The vector store instance to add the document to.

    Returns:
        None

    Raises:
        Exception: Exceptions are caught and logged, not propagated.
    """
    try:
        # Determine file type based on extension
        file_extension: str = get_file_extension(filename)
        logger.debug(
            "Processing %s file: %s (ID: %s)", file_extension, filename, document_id
        )

        # Extract text based on file type - different handling for each supported format
        text: str = ""

        if file_extension == ".pdf":
            # PDF file handling
            pdf = PdfReader(io.BytesIO(file_content))
            for page_num, page in enumerate(pdf.pages):
                # Extract text from each page and concatenate
                page_text = page.extract_text() or ""  # Handle None returns
                text += page_text + f"\n\n[Page {page_num + 1}]\n\n"
            logger.debug("Extracted text from PDF with %d pages", len(pdf.pages))

        elif file_extension in (".txt", ".md"):
            # Plain text or Markdown file handling
            text = file_content.decode("utf-8")
            logger.debug("Decoded text file as UTF-8")

        elif file_extension == ".csv":
            # Simple CSV handling - more complex handling might be needed
            # For production, consider using pandas or dedicated CSV parsers
            text = file_content.decode("utf-8")
            logger.debug("Decoded CSV file as UTF-8")

        elif file_extension == ".json":
            # Simple JSON handling - treated as text
            # For production, consider parsing and structured handling
            text = file_content.decode("utf-8")
            logger.debug("Decoded JSON file as UTF-8")

        else:
            logger.warning("Unsupported file extension: %s", file_extension)
            return

        # Skip processing if no text was extracted
        if not text.strip():
            logger.warning("No text content extracted from %s", filename)
            return

        # Split text into chunks for better processing and retrieval
        text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Characters per chunk
            chunk_overlap=200,  # Overlap between chunks to maintain context
            length_function=len,  # Function to measure text length
        )
        chunks: List[str] = text_splitter.split_text(text)
        logger.info("Split %s into %d chunks", filename, len(chunks))

        # Create Document objects with metadata for each chunk
        documents: List[Document] = []
        for i, chunk in enumerate(chunks):
            # Combine provided metadata with chunk-specific metadata
            chunk_metadata: Dict[str, Any] = {
                "document_id": document_id,
                "filename": filename,
                "chunk": i,
                "chunk_total": len(chunks),
                "file_type": (
                    file_extension[1:]
                    if file_extension.startswith(".")
                    else file_extension
                ),
                **metadata,  # Include all user-provided metadata
            }

            # Create a Document object
            doc = Document(
                page_content=chunk,
                metadata=chunk_metadata,
            )
            documents.append(doc)

        # Add documents to vector store if we have any
        if documents:
            await vector_store.add_documents(documents, document_id, filename, metadata)
            logger.info(
                "Successfully processed %s with %d chunks added to vector store",
                filename,
                len(chunks),
            )
        else:
            logger.warning("No documents created from %s", filename)

    except Exception as e:
        # Log the error but don't propagate it - this is typically run as a background task
        logger.error("Error processing file %s: %s", filename, str(e), exc_info=True)
