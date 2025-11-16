"""
Conversation Manager - Core orchestrator for context-aware search
Coordinates intent analysis, state management, and conversation history
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .intent_analyzer import IntentAnalyzer
from .states import (
    ConversationContext,
    IntentType,
    get_next_state,
)


class ConversationManager:
    """Manages conversation state and context for product search"""

    def __init__(
        self, ollama_url: str = "http://localhost:11434", qdrant_url: str = "http://localhost:6333"
    ):
        self.intent_analyzer = IntentAnalyzer(ollama_url=ollama_url)
        self.qdrant_url = qdrant_url

        # In-memory session storage (later: migrate to Redis/Database)
        self.sessions: Dict[str, ConversationContext] = {}

    async def process_query(
        self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query with full context awareness

        Args:
            query: User's query
            session_id: Session identifier (auto-generated if None)
            user_id: User identifier (optional)

        Returns:
            {
                "session_id": str,
                "intent": IntentType,
                "criteria": SearchCriteria,
                "state": ConversationState,
                "should_search_new": bool,
                "should_filter_previous": bool,
                "previous_results": List[Dict],
                "context_info": Dict
            }
        """
        # Get or create session
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self.sessions.get(session_id)
        if not context:
            context = ConversationContext(session_id=session_id, user_id=user_id)
            self.sessions[session_id] = context

        # Analyze intent using LLM
        analysis = await self.intent_analyzer.analyze_intent(query, context)

        intent = analysis["intent"]
        criteria = analysis["criteria"]
        confidence = analysis["confidence"]

        # Determine next state
        current_state = context.state
        next_state = get_next_state(current_state, intent)

        if not next_state:
            # No valid transition - stay in current state
            next_state = current_state

        # Update context
        context.queries.append(query)
        context.intents.append(intent)
        context.turn_count += 1
        context.updated_at = datetime.now()

        # Determine action based on intent
        should_search_new = intent in [IntentType.NEW_SEARCH, IntentType.REFINE_SEARCH]

        should_filter_previous = intent == IntentType.FILTER_PREVIOUS
        should_recommend_accessory = intent == IntentType.RECOMMEND_ACCESSORY

        # Move current to previous if starting new search
        if should_search_new and context.current_results:
            context.previous_query = context.current_query
            context.previous_results = context.current_results
            context.current_results = []

        # Update current query
        context.current_query = query
        context.current_criteria = criteria
        context.state = next_state

        # CRITICAL FIX: For filtering, use current_results (not previous_results)
        # because current_results contains the active search results from the previous turn
        filter_from_results = context.current_results if should_filter_previous else []

        # Prepare response
        response = {
            "session_id": session_id,
            "intent": intent.value,
            "criteria": criteria.dict(),
            "state": next_state.value,
            "previous_state": current_state.value,
            "should_search_new": should_search_new,
            "should_filter_previous": should_filter_previous,
            "should_recommend_accessory": should_recommend_accessory,
            "previous_results": filter_from_results,  # FIXED: Use current_results for filtering
            "current_bottles": context.current_results if should_recommend_accessory else [],
            "confidence": confidence,
            "explanation": analysis.get("explanation", ""),
            "context_info": {
                "turn_count": context.turn_count,
                "query_history": context.queries[-5:],  # Last 5 queries
                "current_results_count": len(context.current_results),
                "previous_results_count": len(context.previous_results),
            },
        }

        return response

    async def update_results(self, session_id: str, results: List[Dict[str, Any]]):
        """Update search results for session

        Args:
            session_id: Session identifier
            results: Search results to store
        """
        context = self.sessions.get(session_id)
        if context:
            context.current_results = results
            context.updated_at = datetime.now()

    async def save_to_qdrant(
        self,
        session_id: str,
        query: str,
        intent: str,
        results: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ):
        """Save conversation turn to Qdrant for long-term memory

        Args:
            session_id: Session identifier
            query: User query
            intent: Detected intent
            results: Search results
            user_id: User identifier
        """
        try:
            # Generate embedding for query
            embedding = await self._generate_embedding(query)

            if not embedding:
                return

            # Prepare point for Qdrant
            point = {
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "query": query,
                    "intent": intent,
                    "result_count": len(results),
                    "result_ids": [r.get("product_id") for r in results[:10]],
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation_turn",
                },
            }

            # Save to Qdrant
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.put(
                    f"{self.qdrant_url}/collections/conversation_history/points",
                    json={"points": [point]},
                )

        except Exception as e:
            print(f"Failed to save to Qdrant: {e}")

    async def retrieve_similar_conversations(
        self, query: str, user_id: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past conversations from Qdrant

        Args:
            query: Current query
            user_id: User identifier (for filtering)
            limit: Number of similar conversations

        Returns:
            List of similar conversation turns
        """
        try:
            embedding = await self._generate_embedding(query)
            if not embedding:
                return []

            # Build filter
            filter_clause = {}
            if user_id:
                filter_clause = {"user_id": user_id}

            # Search Qdrant
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/conversation_history/points/search",
                    json={
                        "vector": embedding,
                        "limit": limit,
                        "with_payload": True,
                        "filter": filter_clause if filter_clause else None,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", [])

        except Exception as e:
            print(f"Failed to retrieve from Qdrant: {e}")

        return []

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Ollama

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.intent_analyzer.ollama_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")

        except Exception as e:
            print(f"Embedding generation error: {e}")

        return None

    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for session"""
        return self.sessions.get(session_id)

    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
