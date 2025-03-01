import asyncio
import json
import logging
import os
from typing import AsyncGenerator, List

from openai import AsyncOpenAI
from serpapi import GoogleSearch

from models import ChatMessage
from vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)


class OpenAIAgent:
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the OpenAI agent with a vector store.
        """
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = vector_store
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")

        # Default assistant instruction template
        self.instructions_template = """
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
        self.assistant_cache = {}

    async def perform_web_search(self, query: str) -> str:
        """
        Perform a web search using SerpAPI.
        """
        try:
            if not self.serpapi_key:
                logger.error("SERPAPI_API_KEY not set")
                return "Web search is not available (API key not configured)."

            logger.info(f"Searching web for: {query}")

            # Use SerpAPI to search the web
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": 5,
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Extract organic results
            organic_results = results.get("organic_results", [])

            if not organic_results:
                return "No relevant results found on the web."

            # Format the results
            formatted_results = "Here are some relevant results from the web:\n\n"

            for i, result in enumerate(organic_results[:5]):
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "No description")

                formatted_results += f"{i+1}. **{title}**\n"
                formatted_results += f"   {snippet}\n"
                formatted_results += f"   Source: {link}\n\n"

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching web: {str(e)}")
            return f"I encountered an error while searching the web: {str(e)}"

    async def handle_tool_calls(self, thread_id: str, run_id: str):
        """
        Handle tool calls from the assistant, particularly for web search.
        """
        try:
            # Wait for any required actions
            run_status = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )

            if run_status.status == "requires_action":
                tool_outputs = []

                # Process each required action
                for (
                    tool_call
                ) in run_status.required_action.submit_tool_outputs.tool_calls:
                    if tool_call.function.name == "search_web":
                        # Extract the query from the function arguments
                        arguments = json.loads(tool_call.function.arguments)
                        query = arguments.get("query", "")

                        # Perform the web search
                        search_results = await self.perform_web_search(query)

                        # Add the results to tool outputs
                        tool_outputs.append(
                            {"tool_call_id": tool_call.id, "output": search_results}
                        )

                # Submit the tool outputs back to the assistant
                await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
                )

                return True  # Indicate that tool calls were handled

            return False  # No tool calls to handle

        except Exception as e:
            logger.error(f"Error handling tool calls: {str(e)}")
            return False

    async def generate_response(
        self, messages: List[ChatMessage], search_web: bool = False
    ) -> str:
        """
        Generate a response from the OpenAI agent using Assistants API.
        """
        try:
            # Get all available vector store IDs
            vector_store_ids = self.vector_store.get_vector_store_ids()

            # Configure tools
            tools = [{"type": "file_search"}]

            # Add web search function if requested
            if search_web:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "search_web",
                            "description": "Search the web for current and factual information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query to look up on the web",
                                    }
                                },
                                "required": ["query"],
                            },
                        },
                    }
                )

            # Generate a cache key based on tools and vector store IDs
            cache_key = (
                f"{'-'.join(t.get('type') for t in tools)}-{'-'.join(vector_store_ids)}"
            )

            # Check if we have a cached assistant
            assistant_id = self.assistant_cache.get(cache_key)

            if not assistant_id:
                # Create a new assistant
                assistant = await self.client.beta.assistants.create(
                    name="Knowledgebase Assistant",
                    instructions=self.instructions_template.format(
                        additional_instructions="When you need current information, use the search_web function."
                    ),
                    tools=tools,
                    model="gpt-4o",
                    tool_resources=(
                        {"file_search": {"vector_store_ids": vector_store_ids}}
                        if vector_store_ids
                        else None
                    ),
                )
                # Cache the assistant ID
                self.assistant_cache[cache_key] = assistant.id
                assistant_id = assistant.id

            # Create a thread with all the messages
            thread = await self.client.beta.threads.create(
                messages=[
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                    if msg.role in ["user", "assistant"]
                ]
            )

            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant_id
            )

            # Poll for completion or required actions
            max_retries = 60  # 5 minutes with 5-second intervals
            retries = 0

            while retries < max_retries:
                run_status = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )

                if run_status.status == "completed":
                    break
                elif run_status.status == "requires_action":
                    # Handle any required actions (like web search)
                    handled = await self.handle_tool_calls(thread.id, run.id)
                    if handled:
                        logger.info("Successfully handled tool calls")
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run failed with status: {run_status.status}")
                    if hasattr(run_status, "last_error") and run_status.last_error:
                        logger.error(f"Error details: {run_status.last_error}")
                    return f"I encountered an error: {run_status.status}"

                await asyncio.sleep(5)
                retries += 1

            if retries >= max_retries:
                return "The request timed out. Please try again later."

            # Get the assistant's response
            messages_response = await self.client.beta.threads.messages.list(
                thread_id=thread.id, order="desc", limit=1
            )

            if not messages_response.data:
                return "No response was generated."

            # Extract the text content
            response_text = ""
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
                        citations = []

                        for i, annotation in enumerate(annotations):
                            # Replace the annotation text with a reference number
                            response_text = response_text.replace(
                                annotation.text, f"[{i+1}]"
                            )

                            # Build citation based on annotation type
                            if hasattr(annotation, "file_citation"):
                                file_id = annotation.file_citation.file_id
                                # Get file metadata if available
                                file_info = next(
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
        """
        try:
            # Get all available vector store IDs
            vector_store_ids = self.vector_store.get_vector_store_ids()

            # Configure tools
            tools = [{"type": "file_search"}]

            # Add web search if requested
            if search_web:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "search_web",
                            "description": "Search the web for current and factual information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query to look up on the web",
                                    }
                                },
                                "required": ["query"],
                            },
                        },
                    }
                )

            # Create a new assistant for this streaming session
            assistant = await self.client.beta.assistants.create(
                name="Streaming Assistant",
                instructions=self.instructions_template.format(
                    additional_instructions="When you need current information, use the search_web function."
                ),
                tools=tools,
                model="gpt-4o",
                tool_resources=(
                    {"file_search": {"vector_store_ids": vector_store_ids}}
                    if vector_store_ids
                    else None
                ),
            )

            # Create a thread with all the messages
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
            buffer = ""

            async for chunk in run:
                # Handle tool calls if needed
                if chunk.event == "thread.run.requires_action":
                    # Pause streaming to handle tool calls
                    yield "\n[Searching the web...]\n"

                    # Get the full run to handle tool calls
                    run_status = await self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run.id
                    )

                    # Handle the tool calls
                    await self.handle_tool_calls(thread.id, run.id)

                # Continue with normal message streaming
                elif chunk.event == "thread.message.delta" and hasattr(
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
                                    text_value = content_delta.text.value
                                    buffer += text_value
                                    yield text_value

            # Clean up the assistant after streaming is complete
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
        """
        try:
            # Create a specialized assistant with Canvas tool
            assistant = await self.client.beta.assistants.create(
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
            thread = await self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Create a visualization for me: {prompt}",
                    }
                ]
            )

            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant.id
            )

            # Poll for completion
            max_retries = 30
            retries = 0

            while retries < max_retries:
                run_status = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )

                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    logger.error(
                        f"Visualization run failed with status: {run_status.status}"
                    )
                    await self.client.beta.assistants.delete(assistant_id=assistant.id)
                    return f"I encountered an error creating the visualization: {run_status.status}"

                await asyncio.sleep(3)
                retries += 1

            # Get the visualization result
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread.id, order="desc", limit=1
            )

            result = ""
            for message in messages.data:
                for content in message.content:
                    if content.type == "image":
                        # Return image URL if available
                        result += f"![Visualization]({content.image.file_id})\n\n"
                    elif content.type == "text":
                        result += content.text.value + "\n\n"

            # Clean up the assistant
            await self.client.beta.assistants.delete(assistant_id=assistant.id)

            return result
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return f"I encountered an error while creating a visualization: {str(e)}"
