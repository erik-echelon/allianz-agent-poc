import os
import pickle
from typing import List, Dict, Any, Optional
import logging
import uuid
import asyncio
from openai import AsyncOpenAI
from langchain.schema import Document

# Configure logging
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = "vector_store"):
        """
        Initialize the vector store using OpenAI's vector stores API.
        """
        self.persist_directory = persist_directory
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.document_metadata = {}
        self.file_ids = {}
        self.vector_stores = {}

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Load existing metadata if available
        self._load_metadata()

    def _load_metadata(self):
        """
        Load document metadata from disk if it exists.
        """
        metadata_path = os.path.join(self.persist_directory, "metadata.pkl")
        file_ids_path = os.path.join(self.persist_directory, "file_ids.pkl")
        vector_stores_path = os.path.join(self.persist_directory, "vector_stores.pkl")

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "rb") as f:
                    self.document_metadata = pickle.load(f)
                logger.info("Loaded document metadata")
            except Exception as e:
                logger.error(f"Error loading metadata: {str(e)}")
                self.document_metadata = {}

        if os.path.exists(file_ids_path):
            try:
                with open(file_ids_path, "rb") as f:
                    self.file_ids = pickle.load(f)
                logger.info("Loaded file IDs")
            except Exception as e:
                logger.error(f"Error loading file IDs: {str(e)}")
                self.file_ids = {}

        if os.path.exists(vector_stores_path):
            try:
                with open(vector_stores_path, "rb") as f:
                    self.vector_stores = pickle.load(f)
                logger.info("Loaded vector store IDs")
            except Exception as e:
                logger.error(f"Error loading vector store IDs: {str(e)}")
                self.vector_stores = {}

    def _save_metadata(self):
        """
        Save document metadata to disk.
        """
        try:
            with open(os.path.join(self.persist_directory, "metadata.pkl"), "wb") as f:
                pickle.dump(self.document_metadata, f)

            with open(os.path.join(self.persist_directory, "file_ids.pkl"), "wb") as f:
                pickle.dump(self.file_ids, f)

            with open(
                os.path.join(self.persist_directory, "vector_stores.pkl"), "wb"
            ) as f:
                pickle.dump(self.vector_stores, f)

            logger.info(
                "Saved document metadata, file IDs, and vector store IDs to disk"
            )
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")

    async def _ensure_vector_store_exists(self):
        """
        Ensure a vector store exists or create a new one.
        Returns the vector store ID.
        """
        try:
            # Check if we have an existing vector store
            if not self.vector_stores:
                # Create a new vector store
                vector_store_name = f"vs_{uuid.uuid4().hex[:8]}"
                vector_store = await self.client.beta.vector_stores.create(
                    name=vector_store_name,
                    expires_after={"anchor": "last_active_at", "days": 30},
                )
                vector_store_id = vector_store.id
                self.vector_stores[vector_store_name] = vector_store_id
                logger.info(f"Created new vector store: {vector_store_id}")

                # Save the updated metadata
                self._save_metadata()

                return vector_store_id
            else:
                # Return the first available vector store
                vector_store_name = list(self.vector_stores.keys())[0]
                return self.vector_stores[vector_store_name]
        except Exception as e:
            logger.error(f"Error ensuring vector store exists: {str(e)}")
            raise e

    async def add_documents(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        metadata: Dict[str, Any] = None,
    ):
        """
        Add documents to the OpenAI vector store.
        """
        try:
            # First, upload the file to OpenAI
            temp_filename = f"{document_id}.txt"
            temp_filepath = os.path.join(self.persist_directory, temp_filename)

            # Combine all chunks into one string for the file
            combined_text = ""
            for i, doc in enumerate(documents):
                chunk_info = f"--- Chunk {i+1}/{len(documents)} ---\n"
                combined_text += chunk_info + doc.page_content + "\n\n"

            # Write to temp file
            with open(temp_filepath, "wb") as f:
                f.write(combined_text.encode("utf-8"))

            # Upload to OpenAI
            with open(temp_filepath, "rb") as f:
                file_response = await self.client.files.create(
                    file=f, purpose="assistants"
                )

            # Store file ID
            file_id = file_response.id
            self.file_ids[document_id] = file_id

            # Ensure we have a vector store
            vector_store_id = await self._ensure_vector_store_exists()

            # Add file to vector store
            try:
                # Create file batch and poll until complete
                with open(temp_filepath, "rb") as f:
                    file_batch = await self.client.beta.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=vector_store_id, files=[f]
                    )

                # Check file batch status
                if file_batch.status != "completed":
                    logger.error(
                        f"File batch processing did not complete successfully: {file_batch.status}"
                    )
                    raise Exception(
                        f"File batch processing failed: {file_batch.status}"
                    )

                logger.info(
                    f"Successfully added file to vector store: {file_batch.file_counts}"
                )
            except Exception as e:
                logger.error(
                    f"Error adding file to vector store using upload_and_poll: {str(e)}"
                )
                # Try alternate approach using file IDs
                try:
                    logger.info("Trying alternate approach with file IDs...")
                    file_batch = (
                        await self.client.beta.vector_stores.file_batches.create(
                            vector_store_id=vector_store_id, file_ids=[file_id]
                        )
                    )

                    # Poll for completion
                    max_attempts = 30
                    attempts = 0
                    while attempts < max_attempts:
                        batch_status = (
                            await self.client.beta.vector_stores.file_batches.retrieve(
                                vector_store_id=vector_store_id,
                                file_batch_id=file_batch.id,
                            )
                        )

                        if batch_status.status == "completed":
                            logger.info(f"Batch {file_batch.id} completed successfully")
                            break
                        elif batch_status.status in ["failed", "cancelled"]:
                            logger.error(
                                f"Batch {file_batch.id} failed with status: {batch_status.status}"
                            )
                            raise Exception(
                                f"File batch processing failed: {batch_status.status}"
                            )

                        await asyncio.sleep(2)
                        attempts += 1

                    if attempts >= max_attempts:
                        logger.warning(
                            f"Batch {file_batch.id} is still processing after {max_attempts} attempts"
                        )
                except Exception as inner_e:
                    logger.error(f"Error in alternate approach: {str(inner_e)}")
                    raise inner_e

            # Add metadata
            base_metadata = {
                "document_id": document_id,
                "filename": filename,
                "file_id": file_id,
                "vector_store_id": vector_store_id,
                "vector_store_name": next(
                    k for k, v in self.vector_stores.items() if v == vector_store_id
                ),
                "added_at": str(uuid.uuid4()),  # Using UUID as a timestamp proxy
                "num_chunks": len(documents),
            }

            if metadata:
                base_metadata.update(metadata)

            # Store document metadata
            self.document_metadata[document_id] = base_metadata

            # Clean up temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

            # Save metadata to disk
            self._save_metadata()

            logger.info(
                f"Added {len(documents)} documents to OpenAI vector store with ID {document_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise e

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the vector store.
        """
        return list(self.document_metadata.values())

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        """
        if document_id not in self.document_metadata:
            return False

        try:
            # Get file ID and vector store ID
            file_id = self.file_ids.get(document_id)
            vector_store_id = self.document_metadata[document_id].get("vector_store_id")

            if file_id and vector_store_id:
                # First try to remove the file from the vector store
                try:
                    await self.client.beta.vector_stores.files.delete(
                        vector_store_id=vector_store_id, file_id=file_id
                    )
                    logger.info(
                        f"Removed file {file_id} from vector store {vector_store_id}"
                    )
                except Exception as e:
                    logger.error(f"Error removing file from vector store: {str(e)}")

                # Then delete the file itself
                try:
                    await self.client.files.delete(file_id=file_id)
                    logger.info(f"Deleted file {file_id}")
                except Exception as e:
                    logger.error(f"Error deleting file from OpenAI: {str(e)}")

            # Remove from metadata and file IDs
            del self.document_metadata[document_id]
            if document_id in self.file_ids:
                del self.file_ids[document_id]

            # Save changes
            self._save_metadata()

            logger.info(f"Deleted document with ID {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    def get_vector_store_ids(self) -> List[str]:
        """
        Get list of available vector store IDs.
        """
        return list(self.vector_stores.values())

    async def get_vector_store_info(self) -> Dict[str, Any]:
        """
        Get information about the vector stores.
        """
        if not self.vector_stores:
            return {"status": "no_vector_stores", "vector_stores": {}}

        try:
            result = {"status": "ok", "vector_stores": {}}

            for name, vs_id in self.vector_stores.items():
                try:
                    # Get vector store info
                    vector_store = await self.client.beta.vector_stores.retrieve(
                        vector_store_id=vs_id
                    )

                    # Get file counts
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
                    result["vector_stores"][name] = {"id": vs_id, "error": str(e)}

            return result
        except Exception as e:
            logger.error(f"Error getting vector store info: {str(e)}")
            return {"status": "error", "error": str(e)}
