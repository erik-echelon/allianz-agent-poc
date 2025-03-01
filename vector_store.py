import asyncio
import logging
import os
import pickle
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from langchain.schema import Document
from openai import AsyncOpenAI

# Configure logging for the vector store module
logger = logging.getLogger(__name__)


class VectorStore:
    """
    A class that manages document storage and retrieval using OpenAI's vector stores API.

    This class provides a persistent layer for storing document embeddings and metadata,
    allowing for efficient document management and retrieval. It handles the upload,
    storage, and deletion of documents in OpenAI's vector stores.
    """

    def __init__(self, persist_directory: str = "vector_store"):
        """
        Initialize the vector store using OpenAI's vector stores API.

        Args:
            persist_directory (str, optional): Directory to store persistent data.
                Defaults to "vector_store".
        """
        self.persist_directory: str = persist_directory
        self.client: AsyncOpenAI = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Store document metadata indexed by document_id
        self.document_metadata: Dict[str, Dict[str, Any]] = {}

        # Mapping from document_id to OpenAI file_id
        self.file_ids: Dict[str, str] = {}

        # Mapping from vector store names to their IDs
        self.vector_stores: Dict[str, str] = {}

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Load existing metadata if available
        self._load_metadata()

    def _load_metadata(self) -> None:
        """
        Load document metadata from disk if it exists.

        This method attempts to load three pickle files:
        - metadata.pkl: Contains document metadata
        - file_ids.pkl: Contains mapping of document IDs to file IDs
        - vector_stores.pkl: Contains mapping of vector store names to IDs

        If any file fails to load, the corresponding attribute is initialized as an empty dict.
        """
        metadata_path: str = os.path.join(self.persist_directory, "metadata.pkl")
        file_ids_path: str = os.path.join(self.persist_directory, "file_ids.pkl")
        vector_stores_path: str = os.path.join(
            self.persist_directory, "vector_stores.pkl"
        )

        # Load document metadata
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "rb") as f:
                    self.document_metadata = cast(
                        Dict[str, Dict[str, Any]], pickle.load(f)
                    )
                logger.info("Loaded document metadata from %s", metadata_path)
            except Exception as e:
                logger.error("Error loading metadata: %s", str(e))
                self.document_metadata = {}

        # Load file IDs mapping
        if os.path.exists(file_ids_path):
            try:
                with open(file_ids_path, "rb") as f:
                    self.file_ids = cast(Dict[str, str], pickle.load(f))
                logger.info("Loaded file IDs from %s", file_ids_path)
            except Exception as e:
                logger.error("Error loading file IDs: %s", str(e))
                self.file_ids = {}

        # Load vector stores mapping
        if os.path.exists(vector_stores_path):
            try:
                with open(vector_stores_path, "rb") as f:
                    self.vector_stores = cast(Dict[str, str], pickle.load(f))
                logger.info("Loaded vector store IDs from %s", vector_stores_path)
            except Exception as e:
                logger.error("Error loading vector store IDs: %s", str(e))
                self.vector_stores = {}

    def _save_metadata(self) -> None:
        """
        Save document metadata to disk.

        This method saves the current state of three attributes to pickle files:
        - document_metadata: Saved to metadata.pkl
        - file_ids: Saved to file_ids.pkl
        - vector_stores: Saved to vector_stores.pkl

        This ensures persistence across application restarts.
        """
        try:
            # Save document metadata
            metadata_path: str = os.path.join(self.persist_directory, "metadata.pkl")
            with open(metadata_path, "wb") as f:
                pickle.dump(self.document_metadata, f)

            # Save file IDs mapping
            file_ids_path: str = os.path.join(self.persist_directory, "file_ids.pkl")
            with open(file_ids_path, "wb") as f:
                pickle.dump(self.file_ids, f)

            # Save vector stores mapping
            vector_stores_path: str = os.path.join(
                self.persist_directory, "vector_stores.pkl"
            )
            with open(vector_stores_path, "wb") as f:
                pickle.dump(self.vector_stores, f)

            logger.info(
                "Saved document metadata, file IDs, and vector store IDs to disk"
            )
        except Exception as e:
            logger.error("Error saving metadata: %s", str(e))

    async def _ensure_vector_store_exists(self) -> str:
        """
        Ensure a vector store exists or create a new one.

        This method checks if there's an existing vector store and creates one if none exists.
        It automatically sets a 30-day expiration policy based on last activity.

        Returns:
            str: The ID of an available vector store.

        Raises:
            Exception: If creating or retrieving a vector store fails.
        """
        try:
            # Check if we have an existing vector store
            if not self.vector_stores:
                # Create a new vector store with a unique name
                vector_store_name: str = f"vs_{uuid.uuid4().hex[:8]}"

                # Create vector store with 30-day expiration after last activity
                vector_store = await self.client.beta.vector_stores.create(
                    name=vector_store_name,
                    expires_after={"anchor": "last_active_at", "days": 30},
                )
                vector_store_id: str = vector_store.id

                # Store the new vector store
                self.vector_stores[vector_store_name] = vector_store_id
                logger.info(
                    "Created new vector store: %s with ID %s",
                    vector_store_name,
                    vector_store_id,
                )

                # Save the updated metadata
                self._save_metadata()

                return vector_store_id
            else:
                # Return the first available vector store
                vector_store_name = list(self.vector_stores.keys())[0]
                vector_store_id = self.vector_stores[vector_store_name]
                logger.debug(
                    "Using existing vector store: %s with ID %s",
                    vector_store_name,
                    vector_store_id,
                )
                return vector_store_id
        except Exception as e:
            logger.error("Error ensuring vector store exists: %s", str(e))
            raise e

    async def add_documents(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add documents to the OpenAI vector store.

        This method:
        1. Combines document chunks into a single file
        2. Uploads the file to OpenAI
        3. Adds the file to a vector store
        4. Stores metadata for future reference

        Args:
            documents (List[Document]): List of Document objects to add.
            document_id (str): Unique identifier for the document.
            filename (str): Original filename of the document.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.

        Returns:
            bool: True if documents were added successfully.

        Raises:
            Exception: If there's an error during the document addition process.
        """
        try:
            # First, upload the file to OpenAI by creating a temporary file
            temp_filename: str = f"{document_id}.txt"
            temp_filepath: str = os.path.join(self.persist_directory, temp_filename)

            # Combine all chunks into one string for the file
            # Each chunk is labeled with its position in the sequence
            combined_text: str = ""
            for i, doc in enumerate(documents):
                chunk_info = f"--- Chunk {i+1}/{len(documents)} ---\n"
                combined_text += chunk_info + doc.page_content + "\n\n"

            # Write combined content to temporary file
            with open(temp_filepath, "wb") as f:
                f.write(combined_text.encode("utf-8"))

            # Upload temporary file to OpenAI
            with open(temp_filepath, "rb") as f:
                file_response = await self.client.files.create(
                    file=f, purpose="assistants"
                )

            # Store file ID mapping
            file_id: str = file_response.id
            self.file_ids[document_id] = file_id
            logger.info("Uploaded file to OpenAI with ID: %s", file_id)

            # Ensure we have a vector store available
            vector_store_id: str = await self._ensure_vector_store_exists()

            # Try to add file to vector store using the recommended upload_and_poll method
            try:
                # Create file batch and poll until complete
                with open(temp_filepath, "rb") as f:
                    file_batch = await self.client.beta.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=vector_store_id, files=[f]
                    )

                # Check file batch status
                if file_batch.status != "completed":
                    logger.error(
                        "File batch processing did not complete successfully: %s",
                        file_batch.status,
                    )
                    raise Exception(
                        f"File batch processing failed: {file_batch.status}"
                    )

                logger.info(
                    "Successfully added file to vector store: %s",
                    (
                        file_batch.file_counts
                        if hasattr(file_batch, "file_counts")
                        else "N/A"
                    ),
                )

            except Exception as e:
                # First approach failed, try alternate method
                logger.error(
                    "Error adding file to vector store using upload_and_poll: %s",
                    str(e),
                )

                # Try alternate approach using file IDs
                try:
                    logger.info("Trying alternate approach with file IDs...")

                    # Create file batch using the file ID we obtained earlier
                    file_batch = (
                        await self.client.beta.vector_stores.file_batches.create(
                            vector_store_id=vector_store_id, file_ids=[file_id]
                        )
                    )

                    # Poll for completion with timeout
                    max_attempts: int = 30
                    attempts: int = 0

                    while attempts < max_attempts:
                        # Check batch status
                        batch_status = (
                            await self.client.beta.vector_stores.file_batches.retrieve(
                                vector_store_id=vector_store_id,
                                file_batch_id=file_batch.id,
                            )
                        )

                        if batch_status.status == "completed":
                            logger.info(
                                "Batch %s completed successfully", file_batch.id
                            )
                            break
                        elif batch_status.status in ["failed", "cancelled"]:
                            logger.error(
                                "Batch %s failed with status: %s",
                                file_batch.id,
                                batch_status.status,
                            )
                            raise Exception(
                                f"File batch processing failed: {batch_status.status}"
                            )

                        # Wait before checking again
                        await asyncio.sleep(2)
                        attempts += 1

                    # Handle timeout case
                    if attempts >= max_attempts:
                        logger.warning(
                            "Batch %s is still processing after %s attempts",
                            file_batch.id,
                            max_attempts,
                        )

                except Exception as inner_e:
                    logger.error("Error in alternate approach: %s", str(inner_e))
                    raise inner_e

            # Prepare document metadata
            base_metadata: Dict[str, Any] = {
                "document_id": document_id,
                "filename": filename,
                "file_id": file_id,
                "vector_store_id": vector_store_id,
                "vector_store_name": next(
                    k for k, v in self.vector_stores.items() if v == vector_store_id
                ),
                "added_at": datetime.now().isoformat(),  # Use ISO format timestamp
                "num_chunks": len(documents),
            }

            # Add custom metadata if provided
            if metadata:
                base_metadata.update(metadata)

            # Store document metadata
            self.document_metadata[document_id] = base_metadata

            # Clean up temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                logger.debug("Cleaned up temporary file: %s", temp_filepath)

            # Save metadata to disk
            self._save_metadata()

            logger.info(
                "Added %s document chunks to OpenAI vector store with ID %s",
                len(documents),
                document_id,
            )
            return True

        except Exception as e:
            logger.error("Error adding documents: %s", str(e))
            raise e

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the vector store.

        Returns:
            List[Dict[str, Any]]: A list of document metadata dictionaries.
        """
        documents: List[Dict[str, Any]] = list(self.document_metadata.values())
        logger.debug("Returning %s documents from vector store", len(documents))
        return documents

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.

        This method:
        1. Removes the file from the vector store
        2. Deletes the file from OpenAI
        3. Updates local metadata

        Args:
            document_id (str): The ID of the document to delete.

        Returns:
            bool: True if the document was deleted successfully, False otherwise.
        """
        # Check if document exists in our metadata
        if document_id not in self.document_metadata:
            logger.warning("Document %s not found in metadata", document_id)
            return False

        try:
            # Get file ID and vector store ID
            file_id: Optional[str] = self.file_ids.get(document_id)
            vector_store_id: Optional[str] = self.document_metadata[document_id].get(
                "vector_store_id"
            )

            if file_id and vector_store_id:
                # First try to remove the file from the vector store
                try:
                    await self.client.beta.vector_stores.files.delete(
                        vector_store_id=vector_store_id, file_id=file_id
                    )
                    logger.info(
                        "Removed file %s from vector store %s", file_id, vector_store_id
                    )
                except Exception as e:
                    logger.error("Error removing file from vector store: %s", str(e))

                # Then delete the file itself from OpenAI
                try:
                    await self.client.files.delete(file_id=file_id)
                    logger.info("Deleted file %s from OpenAI", file_id)
                except Exception as e:
                    logger.error("Error deleting file from OpenAI: %s", str(e))

            # Remove from metadata and file IDs mappings
            del self.document_metadata[document_id]
            if document_id in self.file_ids:
                del self.file_ids[document_id]

            # Save changes to disk
            self._save_metadata()

            logger.info("Deleted document with ID %s", document_id)
            return True

        except Exception as e:
            logger.error("Error deleting document %s: %s", document_id, str(e))
            return False

    def get_vector_store_ids(self) -> List[str]:
        """
        Get list of available vector store IDs.

        Returns:
            List[str]: List of vector store IDs that can be used with the OpenAI API.
        """
        vector_store_ids: List[str] = list(self.vector_stores.values())
        logger.debug("Returning %s vector store IDs", len(vector_store_ids))
        return vector_store_ids

    async def get_vector_store_info(self) -> Dict[str, Any]:
        """
        Get information about the vector stores.

        This method retrieves details about each vector store, including:
        - Status
        - File counts
        - Creation timestamp

        Returns:
            Dict[str, Any]: A dictionary containing status and vector store information.
        """
        # If no vector stores exist, return early
        if not self.vector_stores:
            logger.info("No vector stores found")
            return {"status": "no_vector_stores", "vector_stores": {}}

        try:
            result: Dict[str, Any] = {"status": "ok", "vector_stores": {}}

            # Gather information about each vector store
            for name, vs_id in self.vector_stores.items():
                try:
                    # Retrieve vector store information from OpenAI
                    vector_store = await self.client.beta.vector_stores.retrieve(
                        vector_store_id=vs_id
                    )

                    # Extract relevant information
                    result["vector_stores"][name] = {
                        "id": vs_id,
                        "name": vector_store.name,
                        "status": vector_store.status,
                        "file_counts": (
                            vector_store.file_counts
                            if hasattr(vector_store, "file_counts")
                            else None
                        ),
                        "created_at": vector_store.created_at,
                    }

                except Exception as e:
                    # Record errors for individual vector stores
                    logger.error("Error retrieving vector store %s: %s", vs_id, str(e))
                    result["vector_stores"][name] = {"id": vs_id, "error": str(e)}

            return result

        except Exception as e:
            logger.error("Error getting vector store info: %s", str(e))
            return {"status": "error", "error": str(e)}
