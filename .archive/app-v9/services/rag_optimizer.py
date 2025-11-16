"""
RAG Optimization Suite (v6.0.0)
================================

Advanced RAG techniques for improving retrieval and generation quality.

Features:
1. Query Expansion: Expand queries with synonyms and related terms
2. Query Rewriting: Rewrite ambiguous queries for better retrieval
3. Contextual Compression: Compress retrieved context to fit LLM window
4. Citation Tracking: Track and attribute sources in generated answers
5. Answer Verification: Verify answer accuracy against retrieved context

Techniques:
- HyDE (Hypothetical Document Embeddings)
- Multi-query generation
- Query decomposition
- Context ranking and filtering
- Fact extraction and verification

Version: v6.0.0
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# ============================================================================
# Query Optimization
# ============================================================================


class QueryOptimizer:
    """
    Optimize search queries for better retrieval

    Techniques:
    - Query expansion with synonyms
    - Query rewriting for clarity
    - Multi-query generation
    - HyDE (Hypothetical Document Embeddings)
    """

    def __init__(self, model: Optional[SentenceTransformer] = None):
        """
        Initialize query optimizer

        Args:
            model: Sentence transformer model for embeddings
        """
        self.model = model
        logger.info("QueryOptimizer initialized")

    def expand_query(self, query: str, domain: str = "packaging") -> List[str]:
        """
        Expand query with synonyms and related terms

        Args:
            query: Original query
            domain: Domain context (packaging, manufacturing, etc.)

        Returns:
            List of expanded queries
        """
        expanded_queries = [query]

        # Domain-specific expansions
        if domain == "packaging":
            # Material synonyms
            if "PET" in query.upper():
                expanded_queries.append(query.replace("PET", "폴리에틸렌 테레프탈레이트"))
            if "PP" in query.upper():
                expanded_queries.append(query.replace("PP", "폴리프로필렌"))
            if "PE" in query.upper():
                expanded_queries.append(query.replace("PE", "폴리에틸렌"))

            # Container synonyms
            if "용기" in query:
                expanded_queries.append(query.replace("용기", "병"))
                expanded_queries.append(query.replace("용기", "컨테이너"))
            if "병" in query:
                expanded_queries.append(query.replace("병", "용기"))

            # Capacity variations
            capacity_match = re.search(r"(\d+)\s*(ml|ML|mL)", query)
            if capacity_match:
                value = capacity_match.group(1)
                # Add cc variation
                expanded_queries.append(query.replace(capacity_match.group(0), f"{value}cc"))

        logger.info(f"Expanded query into {len(expanded_queries)} variants")
        return expanded_queries

    def rewrite_query(self, query: str, context: str = "") -> str:
        """
        Rewrite ambiguous query for better retrieval

        Args:
            query: Original query
            context: Conversation context (if available)

        Returns:
            Rewritten query
        """
        # Remove filler words
        filler_words = ["좀", "약간", "대충", "한", "그런", "이런"]
        rewritten = query
        for filler in filler_words:
            rewritten = rewritten.replace(filler, "").strip()

        # Add context if available
        if context:
            # Extract key entities from context
            # Simple keyword extraction (can be enhanced with NER)
            rewritten = f"{context} {rewritten}"

        # Normalize spacing
        rewritten = " ".join(rewritten.split())

        logger.info(f"Query rewritten: '{query}' → '{rewritten}'")
        return rewritten

    def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate multiple query variations for better coverage

        Args:
            query: Original query
            num_queries: Number of queries to generate

        Returns:
            List of query variations
        """
        queries = [query]

        # Add expanded queries
        expanded = self.expand_query(query)
        queries.extend(expanded[:num_queries - 1])

        # Add question variations
        if not query.endswith("?"):
            queries.append(f"{query}?")

        # Add more specific queries
        if "용기" in query:
            queries.append(f"{query} 제품")
            queries.append(f"{query} 사양")

        # Deduplicate and limit
        queries = list(dict.fromkeys(queries))[:num_queries]

        logger.info(f"Generated {len(queries)} query variations")
        return queries

    def apply_hyde(self, query: str) -> str:
        """
        Apply HyDE (Hypothetical Document Embeddings)

        Generate a hypothetical answer to the query, then use it for retrieval

        Args:
            query: Original query

        Returns:
            Hypothetical document text
        """
        # Simple template-based HyDE (can be enhanced with LLM)
        if "PET" in query.upper() or "PP" in query.upper():
            material = "PET" if "PET" in query.upper() else "PP"
            capacity_match = re.search(r"(\d+)\s*ml", query, re.IGNORECASE)
            capacity = capacity_match.group(1) if capacity_match else "100"

            hypothetical = f"""
            {material} 재질의 {capacity}ml 용기 제품입니다.
            투명한 {material} 소재로 제작되었으며,
            화장품, 음료, 식품 포장에 적합합니다.
            MOQ는 1000개이며, 다양한 캡 옵션이 제공됩니다.
            """.strip()

            logger.info("Applied HyDE: generated hypothetical document")
            return hypothetical

        return query


# ============================================================================
# Context Compression
# ============================================================================


class ContextCompressor:
    """
    Compress retrieved context to fit LLM window

    Techniques:
    - Relevance ranking
    - Redundancy removal
    - Sentence selection
    - Token budget management
    """

    def __init__(self, model: Optional[SentenceTransformer] = None, max_tokens: int = 2000):
        """
        Initialize context compressor

        Args:
            model: Sentence transformer for relevance scoring
            max_tokens: Maximum tokens in compressed context
        """
        self.model = model
        self.max_tokens = max_tokens
        logger.info(f"ContextCompressor initialized (max_tokens={max_tokens})")

    def compress(
        self, query: str, documents: List[Dict[str, Any]], target_ratio: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Compress documents by selecting most relevant sentences

        Args:
            query: Search query
            documents: List of retrieved documents
            target_ratio: Target compression ratio (0-1)

        Returns:
            Compressed documents
        """
        compressed_docs = []

        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue

            # Split into sentences
            sentences = self._split_sentences(text)

            # Score sentence relevance
            scores = self._score_sentences(query, sentences)

            # Select top sentences
            num_keep = max(1, int(len(sentences) * target_ratio))
            top_indices = np.argsort(scores)[-num_keep:]
            top_indices = sorted(top_indices)  # Maintain order

            # Reconstruct compressed text
            compressed_text = " ".join([sentences[i] for i in top_indices])

            compressed_doc = doc.copy()
            compressed_doc["text"] = compressed_text
            compressed_doc["compression_ratio"] = len(compressed_text) / len(text)
            compressed_docs.append(compressed_doc)

        logger.info(f"Compressed {len(documents)} documents")
        return compressed_docs

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be enhanced with nltk/spacy)
        sentences = re.split(r"[.!?。！？]\s*", text)
        return [s.strip() for s in sentences if s.strip()]

    def _score_sentences(self, query: str, sentences: List[str]) -> np.ndarray:
        """
        Score sentence relevance to query

        Returns:
            Array of relevance scores
        """
        if not self.model:
            # Fallback: keyword matching
            query_words = set(query.lower().split())
            scores = []
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words & sentence_words)
                scores.append(overlap)
            return np.array(scores)

        # Semantic similarity scoring
        query_embedding = self.model.encode([query])[0]
        sentence_embeddings = self.model.encode(sentences)

        # Cosine similarity
        scores = np.dot(sentence_embeddings, query_embedding)
        return scores

    def remove_redundancy(self, documents: List[Dict[str, Any]], threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        Remove redundant documents based on similarity

        Args:
            documents: List of documents
            threshold: Similarity threshold for redundancy

        Returns:
            De-duplicated documents
        """
        if not self.model or len(documents) <= 1:
            return documents

        # Encode documents
        texts = [doc.get("text", "") for doc in documents]
        embeddings = self.model.encode(texts)

        # Compute similarity matrix
        similarity_matrix = np.dot(embeddings, embeddings.T)

        # Select non-redundant documents
        selected = [0]  # Always keep first document
        for i in range(1, len(documents)):
            # Check if similar to any selected document
            max_sim = max(similarity_matrix[i][j] for j in selected)
            if max_sim < threshold:
                selected.append(i)

        filtered_docs = [documents[i] for i in selected]
        logger.info(f"Removed {len(documents) - len(filtered_docs)} redundant documents")
        return filtered_docs


# ============================================================================
# Citation Tracking
# ============================================================================


class CitationTracker:
    """
    Track and attribute sources in generated answers

    Features:
    - Extract facts from source documents
    - Match facts to generated statements
    - Generate inline citations
    - Create bibliography
    """

    def __init__(self):
        """Initialize citation tracker"""
        logger.info("CitationTracker initialized")

    def add_citations(
        self, answer: str, sources: List[Dict[str, Any]], citation_style: str = "inline"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Add citations to generated answer

        Args:
            answer: Generated answer text
            sources: Source documents
            citation_style: Citation style (inline, footnote, endnote)

        Returns:
            Tuple of (cited_answer, bibliography)
        """
        # Split answer into sentences
        sentences = self._split_sentences(answer)

        # Match sentences to sources
        cited_sentences = []
        bibliography = []

        for i, sentence in enumerate(sentences):
            # Find best matching source
            best_source = self._find_best_source(sentence, sources)

            if best_source and citation_style == "inline":
                # Add inline citation
                source_id = len(bibliography) + 1
                cited_sentence = f"{sentence} [{source_id}]"
                cited_sentences.append(cited_sentence)

                # Add to bibliography
                if best_source not in bibliography:
                    bibliography.append(best_source)
            else:
                cited_sentences.append(sentence)

        cited_answer = " ".join(cited_sentences)

        logger.info(f"Added {len(bibliography)} citations to answer")
        return cited_answer, bibliography

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r"[.!?。！？]\s*", text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_best_source(self, sentence: str, sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find best matching source for sentence

        Args:
            sentence: Sentence to match
            sources: Source documents

        Returns:
            Best matching source or None
        """
        # Simple keyword matching (can be enhanced with embeddings)
        sentence_words = set(sentence.lower().split())

        best_source = None
        best_overlap = 0

        for source in sources:
            source_text = source.get("text", "")
            source_words = set(source_text.lower().split())

            overlap = len(sentence_words & source_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_source = source

        # Only return source if significant overlap
        return best_source if best_overlap >= 3 else None


# ============================================================================
# Answer Verification
# ============================================================================


class AnswerVerifier:
    """
    Verify answer accuracy against retrieved context

    Checks:
    - Factual consistency
    - Context grounding
    - Hallucination detection
    - Confidence scoring
    """

    def __init__(self, model: Optional[SentenceTransformer] = None):
        """
        Initialize answer verifier

        Args:
            model: Sentence transformer for similarity
        """
        self.model = model
        logger.info("AnswerVerifier initialized")

    def verify(
        self, answer: str, sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify answer against sources

        Args:
            answer: Generated answer
            sources: Source documents

        Returns:
            Verification result with confidence scores
        """
        # Split answer into facts
        facts = self._extract_facts(answer)

        # Verify each fact
        verified_facts = []
        for fact in facts:
            is_verified = self._verify_fact(fact, sources)
            verified_facts.append({
                "fact": fact,
                "verified": is_verified,
            })

        # Compute overall confidence
        if verified_facts:
            confidence = sum(f["verified"] for f in verified_facts) / len(verified_facts)
        else:
            confidence = 0.0

        # Detect hallucinations
        hallucinated_facts = [f["fact"] for f in verified_facts if not f["verified"]]

        result = {
            "confidence": confidence,
            "verified_facts": len([f for f in verified_facts if f["verified"]]),
            "total_facts": len(verified_facts),
            "hallucinations": hallucinated_facts,
            "is_reliable": confidence >= 0.7,
        }

        logger.info(f"Answer verified: confidence={confidence:.2f}, facts={len(verified_facts)}")
        return result

    def _extract_facts(self, text: str) -> List[str]:
        """
        Extract factual statements from text

        Returns:
            List of facts
        """
        # Simple sentence-based extraction
        # In production, use NER and fact extraction models
        sentences = re.split(r"[.!?。！？]\s*", text)
        facts = [s.strip() for s in sentences if s.strip()]
        return facts

    def _verify_fact(self, fact: str, sources: List[Dict[str, Any]]) -> bool:
        """
        Verify single fact against sources

        Args:
            fact: Fact to verify
            sources: Source documents

        Returns:
            True if fact is supported by sources
        """
        fact_words = set(fact.lower().split())

        for source in sources:
            source_text = source.get("text", "")
            source_words = set(source_text.lower().split())

            # Check word overlap
            overlap = len(fact_words & source_words)
            overlap_ratio = overlap / len(fact_words) if fact_words else 0

            # If significant overlap, consider verified
            if overlap_ratio >= 0.5:
                return True

        return False


# ============================================================================
# RAG Optimizer (Main Class)
# ============================================================================


class RAGOptimizer:
    """
    Complete RAG optimization pipeline

    Combines all optimization techniques:
    - Query optimization
    - Context compression
    - Citation tracking
    - Answer verification
    """

    def __init__(self, model: Optional[SentenceTransformer] = None):
        """
        Initialize RAG optimizer

        Args:
            model: Sentence transformer model
        """
        self.model = model
        self.query_optimizer = QueryOptimizer(model)
        self.context_compressor = ContextCompressor(model)
        self.citation_tracker = CitationTracker()
        self.answer_verifier = AnswerVerifier(model)

        logger.info("✅ RAGOptimizer initialized with all components")

    def optimize_query(self, query: str, strategy: str = "expand") -> List[str]:
        """
        Optimize query using specified strategy

        Args:
            query: Original query
            strategy: Optimization strategy (expand, rewrite, multi, hyde)

        Returns:
            Optimized queries
        """
        if strategy == "expand":
            return self.query_optimizer.expand_query(query)
        elif strategy == "rewrite":
            return [self.query_optimizer.rewrite_query(query)]
        elif strategy == "multi":
            return self.query_optimizer.generate_multi_queries(query)
        elif strategy == "hyde":
            return [self.query_optimizer.apply_hyde(query)]
        else:
            return [query]

    def compress_context(
        self, query: str, documents: List[Dict[str, Any]], target_ratio: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Compress context documents"""
        return self.context_compressor.compress(query, documents, target_ratio)

    def add_citations(
        self, answer: str, sources: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Add citations to answer"""
        return self.citation_tracker.add_citations(answer, sources)

    def verify_answer(
        self, answer: str, sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify answer accuracy"""
        return self.answer_verifier.verify(answer, sources)


# ============================================================================
# Convenience Functions
# ============================================================================


def optimize_rag_pipeline(
    query: str,
    documents: List[Dict[str, Any]],
    answer: str,
    model: Optional[SentenceTransformer] = None,
) -> Dict[str, Any]:
    """
    Complete RAG optimization pipeline

    Args:
        query: Search query
        documents: Retrieved documents
        answer: Generated answer
        model: Sentence transformer model

    Returns:
        Optimized RAG result
    """
    optimizer = RAGOptimizer(model)

    # Optimize query
    optimized_queries = optimizer.optimize_query(query, strategy="multi")

    # Compress context
    compressed_docs = optimizer.compress_context(query, documents, target_ratio=0.5)

    # Add citations
    cited_answer, bibliography = optimizer.add_citations(answer, compressed_docs)

    # Verify answer
    verification = optimizer.verify_answer(answer, compressed_docs)

    return {
        "original_query": query,
        "optimized_queries": optimized_queries,
        "compressed_documents": compressed_docs,
        "cited_answer": cited_answer,
        "bibliography": bibliography,
        "verification": verification,
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example query
    query = "50ml PET 용기"

    # Example documents
    documents = [
        {
            "text": "50ml PET 투명 용기입니다. 화장품 포장에 적합합니다. MOQ 1000개입니다.",
            "metadata": {"product_id": "001", "product_name": "50ml PET 용기"},
        },
        {
            "text": "100ml PP 용기입니다. 식품 포장에 사용됩니다.",
            "metadata": {"product_id": "002", "product_name": "100ml PP 용기"},
        },
    ]

    # Example answer
    answer = "50ml PET 용기는 화장품 포장에 적합합니다. MOQ는 1000개입니다."

    # Optimize RAG pipeline
    result = optimize_rag_pipeline(query, documents, answer)

    print(f"Optimized queries: {result['optimized_queries']}")
    print(f"Cited answer: {result['cited_answer']}")
    print(f"Verification: {result['verification']}")
