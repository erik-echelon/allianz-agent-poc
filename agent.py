import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.beta.threads import Run

from models import ChatMessage
from vector_store import VectorStore

# Configure logging for the OpenAIAgent module
logger = logging.getLogger(__name__)


class OpenAIAgent:
    """
    A class that interfaces with OpenAI's Assistant API to generate responses,
    handle streaming, and create visualizations.

    This agent integrates with a vector store for knowledge retrieval and supports
    web searching capabilities.
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize the OpenAI agent with a vector store.

        Args:
            vector_store (VectorStore): The vector store to use for document retrieval.
        """
        # Initialize OpenAI client using API key from environment variables
        self.client: AsyncOpenAI = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store: VectorStore = vector_store

        # Default assistant instruction template with placeholders for additional instructions
        self.instructions_template: str = """
        You are a helpful AI assistant with the following capabilities:
        1. Access to a knowledge base through vector stores
        2. Ability to search the web for current information
        3. Access to Canvas for visualizations

        Use these tools when appropriate to provide accurate and helpful responses.
        
        When searching the web, clearly indicate when information comes from external sources.
        When creating visualizations, use Canvas to make them clear and informative.
        
        {additional_instructions}
        """

        # Cache for assistants to avoid recreating them
        # Key: cache_key (string based on tools and vector stores)
        # Value: assistant_id (string)
        self.assistant_cache: Dict[str, str] = {}

    async def generate_response(
        self, messages: List[ChatMessage], search_web: bool = False
    ) -> str:
        """
        Generate a response from the OpenAI agent using Assistants API.

        This method creates or retrieves an assistant from cache, creates a thread,
        and processes the response including handling citations and annotations.

        Args:
            messages (List[ChatMessage]): List of messages in the conversation.
            search_web (bool, optional): Whether to enable web search. Defaults to False.

        Returns:
            str: The generated response text.

        Raises:
            Exception: If there's an error generating the response.
        """
        try:
            # Get all available vector store IDs from the connected vector store
            vector_store_ids: List[str] = self.vector_store.get_vector_store_ids()

            # Configure tools based on requested capabilities
            tools: List[Dict[str, str]] = [{"type": "file_search"}]
            if search_web:
                tools.append({"type": "web_search"})

            # Generate a cache key based on enabled tools and available vector stores
            # This allows reuse of assistants with the same configuration
            cache_key: str = (
                f"{'-'.join(t['type'] for t in tools)}-{'-'.join(vector_store_ids)}"
            )

            # Check if we have a cached assistant with this configuration
            assistant_id: Optional[str] = self.assistant_cache.get(cache_key)

            # If no cached assistant exists, create a new one
            if not assistant_id:
                # Create a new assistant with the specified tools and vector stores
                assistant = await self.client.beta.assistants.create(
                    name="Knowledgebase Assistant",
                    instructions=self.instructions_template.format(
                        additional_instructions=""
                    ),
                    tools=tools,
                    model="gpt-4o",
                    tool_resources=(
                        {"file_search": {"vector_store_ids": vector_store_ids}}
                        if vector_store_ids
                        else None
                    ),
                )
                # Cache the assistant ID for future reuse
                self.assistant_cache[cache_key] = assistant.id
                assistant_id = assistant.id

            # Create a thread with all the messages from the conversation
            # Filter to include only user and assistant messages
            thread = await self.client.beta.threads.create(
                messages=[
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                    if msg.role in ["user", "assistant"]
                ]
            )

            # Run the assistant on the thread
            run: Run = await self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant_id
            )

            # Poll for completion with a timeout
            max_retries: int = 60  # 5 minutes with 5-second intervals
            retries: int = 0

            # Wait for the run to complete, checking status periodically
            while retries < max_retries:
                run_status: Run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )

                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run failed with status: {run_status.status}")
                    if hasattr(run_status, "last_error") and run_status.last_error:
                        logger.error(f"Error details: {run_status.last_error}")
                    return f"I encountered an error: {run_status.status}"

                # Wait before checking again
                await asyncio.sleep(5)
                retries += 1

            # Handle timeout case
            if retries >= max_retries:
                return "The request timed out. Please try again later."

            # Get the assistant's response (most recent message)
            messages_response = await self.client.beta.threads.messages.list(
                thread_id=thread.id, order="desc", limit=1
            )

            # Check if we received any messages
            if not messages_response.data:
                return "No response was generated."

            # Extract and process the text content
            response_text: str = ""

            # Process each content block in the message
            for content in messages_response.data[0].content:
                if content.type == "text":
                    response_text += content.text.value

                    # Process annotations (citations to files)
                    if (
                        hasattr(content.text, "annotations")
                        and content.text.annotations
                    ):
                        # Replace annotations with formatted citations
                        annotations = content.text.annotations
                        citations: List[str] = []

                        # Process each annotation
                        for i, annotation in enumerate(annotations):
                            # Replace the annotation text with a reference number
                            response_text = response_text.replace(
                                annotation.text, f"[{i+1}]"
                            )

                            # Build citation based on annotation type
                            if hasattr(annotation, "file_citation"):
                                file_id: str = annotation.file_citation.file_id
                                # Get file metadata if available
                                file_info: Dict[str, Any] = next(
                                    (
                                        doc
                                        for doc in self.vector_store.list_documents()
                                        if doc.get("file_id") == file_id
                                    ),
                                    {"filename": "Unknown document"},
                                )
                                citations.append(
                                    f"[{i+1}] {file_info.get('filename', 'Unknown document')}"
                                )

                        # Add citations at the end if we have any
                        if citations:
                            response_text += "\n\nReferences:\n" + "\n".join(citations)

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

    async def generate_streaming_response(
        self, messages: List[ChatMessage], search_web: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the OpenAI agent using Assistants API.

        This method creates a new assistant for each streaming session,
        sends the response in chunks as they become available, and cleans up
        after the stream is complete.

        Args:
            messages (List[ChatMessage]): List of messages in the conversation.
            search_web (bool, optional): Whether to enable web search. Defaults to False.

        Yields:
            str: Chunks of the generated response as they become available.
        """
        try:
            # Get all available vector store IDs
            vector_store_ids: List[str] = self.vector_store.get_vector_store_ids()

            # Configure tools based on requested capabilities
            tools: List[Dict[str, str]] = [{"type": "file_search"}]
            if search_web:
                tools.append({"type": "web_search"})

            # Create a new assistant for this streaming session
            # Note: We don't cache streaming assistants to ensure fresh responses
            assistant = await self.client.beta.assistants.create(
                name="Streaming Assistant",
                instructions=self.instructions_template.format(
                    additional_instructions=""
                ),
                tools=tools,
                model="gpt-4o",
                tool_resources=(
                    {"file_search": {"vector_store_ids": vector_store_ids}}
                    if vector_store_ids
                    else None
                ),
            )

            # Create a thread with all the messages from the conversation
            thread = await self.client.beta.threads.create(
                messages=[
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                    if msg.role in ["user", "assistant"]
                ]
            )

            # Run the assistant with streaming enabled
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant.id, stream=True
            )

            # Process the streaming response
            buffer: str = ""

            # Iterate through chunks as they arrive
            async for chunk in run:
                if chunk.event == "thread.message.delta" and hasattr(
                    chunk.data, "delta"
                ):
                    if (
                        hasattr(chunk.data.delta, "content")
                        and chunk.data.delta.content
                    ):
                        for content_delta in chunk.data.delta.content:
                            if content_delta.type == "text" and hasattr(
                                content_delta, "text"
                            ):
                                if hasattr(content_delta.text, "value"):
                                    text_value: str = content_delta.text.value
                                    buffer += text_value
                                    yield text_value

            # Clean up the assistant after streaming is complete
            # This prevents accumulating unused assistants
            try:
                await self.client.beta.assistants.delete(assistant_id=assistant.id)
            except Exception as delete_error:
                logger.error(f"Error deleting assistant: {str(delete_error)}")

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            yield f"Error: {str(e)}"

    async def create_visualization(self, prompt: str) -> str:
        """
        Create a visualization using Canvas via Assistant.

        This method creates a specialized visualization assistant with the DALL-E tool,
        processes the request, and returns the generated visualization.

        Args:
            prompt (str): The description of the visualization to create.

        Returns:
            str: Markdown text containing the visualization image URL and any accompanying text.
        """
        try:
            # Create a specialized assistant with Canvas tool (DALL-E)
            visualization_assistant = await self.client.beta.assistants.create(
                name="Visualization Assistant",
                instructions=f"Create a clear visualization based on this request: {prompt}",
                tools=[{"type": "file_search"}, {"type": "dalle"}],
                model="gpt-4o",
                tool_resources=(
                    {
                        "file_search": {
                            "vector_store_ids": self.vector_store.get_vector_store_ids()
                        }
                    }
                    if self.vector_store.get_vector_store_ids()
                    else None
                ),
            )

            # Create a thread with the visualization request
            visualization_thread = await self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Create a visualization for me: {prompt}",
                    }
                ]
            )

            # Run the assistant
            visualization_run: Run = await self.client.beta.threads.runs.create(
                thread_id=visualization_thread.id,
                assistant_id=visualization_assistant.id,
            )

            # Poll for completion with a timeout
            max_retries: int = 30
            retries: int = 0

            # Wait for the visualization to complete
            while retries < max_retries:
                run_status: Run = await self.client.beta.threads.runs.retrieve(
                    thread_id=visualization_thread.id, run_id=visualization_run.id
                )

                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    logger.error(
                        f"Visualization run failed with status: {run_status.status}"
                    )
                    # Clean up the assistant on failure
                    await self.client.beta.assistants.delete(
                        assistant_id=visualization_assistant.id
                    )
                    return f"I encountered an error creating the visualization: {run_status.status}"

                # Wait before checking again
                await asyncio.sleep(3)
                retries += 1

            # Get the visualization result from the most recent message
            messages = await self.client.beta.threads.messages.list(
                thread_id=visualization_thread.id, order="desc", limit=1
            )

            # Process the content to extract images and text
            result: str = ""
            for message in messages.data:
                for content in message.content:
                    if content.type == "image":
                        # Return image URL as markdown if available
                        result += f"![Visualization]({content.image.file_id})\n\n"
                    elif content.type == "text":
                        # Add any explanatory text
                        result += content.text.value + "\n\n"

            # Clean up the assistant
            await self.client.beta.assistants.delete(
                assistant_id=visualization_assistant.id
            )

            return result
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return f"I encountered an error while creating a visualization: {str(e)}"
