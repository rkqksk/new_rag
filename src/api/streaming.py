"""
Streaming Response Support
Server-Sent Events (SSE) for real-time chat
"""

import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)


class StreamingResponse:
    """
    SSE (Server-Sent Events) streaming for real-time responses

    Features:
    - Token-by-token streaming
    - Progress updates
    - Error handling
    - Connection management
    """

    @staticmethod
    async def stream_tokens(
        text: str,
        chunk_size: int = 10,
        delay: float = 0.01
    ) -> AsyncGenerator[str, None]:
        """
        Stream text token by token

        Args:
            text: Full text to stream
            chunk_size: Characters per chunk
            delay: Delay between chunks (seconds)

        Yields:
            Text chunks in SSE format
        """
        # Split into chunks
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]

            # Format as SSE
            sse_data = f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            yield sse_data

            # Delay for smooth streaming
            await asyncio.sleep(delay)

        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    @staticmethod
    async def stream_search_results(
        search_results: list,
        delay: float = 0.05
    ) -> AsyncGenerator[str, None]:
        """
        Stream search results one by one

        Args:
            search_results: List of search results
            delay: Delay between results

        Yields:
            Results in SSE format
        """
        for i, result in enumerate(search_results):
            # Format result
            result_data = {
                'type': 'search_result',
                'rank': i + 1,
                'product_id': result.product_id if hasattr(result, 'product_id') else result.id,
                'score': result.score,
                'payload': result.payload
            }

            sse_data = f"data: {json.dumps(result_data)}\n\n"
            yield sse_data

            await asyncio.sleep(delay)

        # Done
        yield f"data: {json.dumps({'type': 'search_done', 'total': len(search_results)})}\n\n"

    @staticmethod
    async def stream_progress(
        steps: list,
        delay: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """
        Stream progress updates

        Args:
            steps: List of step descriptions
            delay: Delay between steps

        Yields:
            Progress in SSE format
        """
        total = len(steps)

        for i, step in enumerate(steps):
            progress_data = {
                'type': 'progress',
                'step': i + 1,
                'total': total,
                'message': step,
                'percentage': int((i + 1) / total * 100)
            }

            sse_data = f"data: {json.dumps(progress_data)}\n\n"
            yield sse_data

            await asyncio.sleep(delay)

    @staticmethod
    async def stream_error(error_message: str) -> AsyncGenerator[str, None]:
        """
        Stream error message

        Args:
            error_message: Error description

        Yields:
            Error in SSE format
        """
        error_data = {
            'type': 'error',
            'message': error_message
        }

        yield f"data: {json.dumps(error_data)}\n\n"

    @staticmethod
    async def stream_complete_response(
        query: str,
        search_results: list,
        answer: str,
        chunk_size: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Stream complete RAG response

        Workflow:
        1. Echo query
        2. Stream search progress
        3. Stream search results
        4. Stream answer token by token

        Args:
            query: User query
            search_results: Search results
            answer: Generated answer
            chunk_size: Token chunk size

        Yields:
            Complete response in SSE format
        """
        # 1. Echo query
        query_data = {'type': 'query', 'content': query}
        yield f"data: {json.dumps(query_data)}\n\n"
        await asyncio.sleep(0.05)

        # 2. Search progress
        progress_data = {'type': 'progress', 'message': 'Searching...'}
        yield f"data: {json.dumps(progress_data)}\n\n"
        await asyncio.sleep(0.1)

        # 3. Stream search results
        async for chunk in StreamingResponse.stream_search_results(search_results, delay=0.05):
            yield chunk

        # 4. Answer progress
        progress_data = {'type': 'progress', 'message': 'Generating answer...'}
        yield f"data: {json.dumps(progress_data)}\n\n"
        await asyncio.sleep(0.1)

        # 5. Stream answer
        async for chunk in StreamingResponse.stream_tokens(answer, chunk_size=chunk_size, delay=0.01):
            yield chunk


# FastAPI integration example
"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
from src.api.streaming import StreamingResponse

app = FastAPI()

@app.get("/stream")
async def stream_endpoint(query: str):
    # Your RAG logic here
    search_results = ...  # Search results
    answer = ...  # Generated answer

    return FastAPIStreamingResponse(
        StreamingResponse.stream_complete_response(
            query=query,
            search_results=search_results,
            answer=answer
        ),
        media_type="text/event-stream"
    )
"""
