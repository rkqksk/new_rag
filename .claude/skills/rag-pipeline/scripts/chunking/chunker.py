"""
Intelligent Chunking Module for RAG Pipeline

Provides multiple chunking strategies for document processing.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize chunking strategy.

        Args:
            chunk_size: Target size for chunks (characters)
            overlap: Overlap between consecutive chunks (characters)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    @abstractmethod
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with 'text' and 'metadata' keys
        """
        pass


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking - preserves paragraph boundaries"""

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk by paragraphs, respecting semantic boundaries"""
        # Split by paragraphs (double newlines)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding paragraph exceeds chunk size and we have content, save chunk
            if current_chunk and len(current_chunk) + len(para) > self.chunk_size:
                chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))

                # Start new chunk with overlap
                if self.overlap > 0:
                    overlap_text = current_chunk[-self.overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))

        return chunks

    def _create_chunk(self, text: str, metadata: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Create chunk dictionary with metadata"""
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata['chunk_index'] = index
        chunk_metadata['chunk_size'] = len(text)
        chunk_metadata['chunk_strategy'] = 'semantic'

        return {
            'text': text.strip(),
            'metadata': chunk_metadata
        }


class SentenceChunker(ChunkingStrategy):
    """Sentence-based chunking - preserves sentence boundaries"""

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk by sentences, respecting sentence boundaries"""
        # Split by sentences (simple regex)
        sentences = re.split(r'([.!?]+[\s\n]+)', text)

        # Reconstruct sentences with their punctuation
        complete_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                complete_sentences.append(sentences[i] + sentences[i + 1])
            else:
                complete_sentences.append(sentences[i])

        if len(sentences) % 2 == 1:
            complete_sentences.append(sentences[-1])

        chunks = []
        current_chunk = ""

        for sentence in complete_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding sentence exceeds chunk size, save chunk
            if current_chunk and len(current_chunk) + len(sentence) > self.chunk_size:
                chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))

                # Start new chunk with overlap
                if self.overlap > 0:
                    overlap_text = current_chunk[-self.overlap:]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))

        return chunks

    def _create_chunk(self, text: str, metadata: Optional[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Create chunk dictionary with metadata"""
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata['chunk_index'] = index
        chunk_metadata['chunk_size'] = len(text)
        chunk_metadata['chunk_strategy'] = 'sentence'

        return {
            'text': text.strip(),
            'metadata': chunk_metadata
        }


class RecursiveChunker(ChunkingStrategy):
    """Recursive character splitting - tries multiple separators hierarchically"""

    def __init__(self, chunk_size: int = 512, overlap: int = 50, separators: Optional[List[str]] = None):
        super().__init__(chunk_size, overlap)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk recursively using separator hierarchy"""
        return self._recursive_split(text, self.separators, metadata)

    def _recursive_split(self, text: str, separators: List[str], metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively split text using separators"""
        if not separators:
            # Base case: no separators left, split by character
            return self._split_by_char(text, metadata)

        separator = separators[0]
        remaining_separators = separators[1:]

        if not separator:
            # Empty separator means split by character
            return self._split_by_char(text, metadata)

        # Split by current separator
        splits = text.split(separator)

        chunks = []
        current_chunk = ""

        for split in splits:
            if not split:
                continue

            # If split is too large, recursively split it
            if len(split) > self.chunk_size:
                if current_chunk:
                    chunks.extend(self._finalize_chunks([current_chunk], metadata, len(chunks)))
                    current_chunk = ""

                sub_chunks = self._recursive_split(split, remaining_separators, metadata)
                chunks.extend(sub_chunks)
                continue

            # If adding split exceeds chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(separator) + len(split) > self.chunk_size:
                chunks.extend(self._finalize_chunks([current_chunk], metadata, len(chunks)))

                # Start new chunk with overlap
                if self.overlap > 0 and len(current_chunk) > self.overlap:
                    current_chunk = current_chunk[-self.overlap:] + separator + split
                else:
                    current_chunk = split
            else:
                # Add split to current chunk
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split

        # Add final chunk
        if current_chunk:
            chunks.extend(self._finalize_chunks([current_chunk], metadata, len(chunks)))

        return chunks

    def _split_by_char(self, text: str, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split text by characters when no separators work"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = len(chunks)
            chunk_metadata['chunk_size'] = len(chunk_text)
            chunk_metadata['chunk_strategy'] = 'recursive'

            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })

            start = end - self.overlap if self.overlap > 0 else end

        return chunks

    def _finalize_chunks(self, texts: List[str], metadata: Optional[Dict[str, Any]], start_index: int) -> List[Dict[str, Any]]:
        """Convert text list to chunk dictionaries"""
        chunks = []
        for i, text in enumerate(texts):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = start_index + i
            chunk_metadata['chunk_size'] = len(text)
            chunk_metadata['chunk_strategy'] = 'recursive'

            chunks.append({
                'text': text.strip(),
                'metadata': chunk_metadata
            })

        return chunks


class SlidingWindowChunker(ChunkingStrategy):
    """Sliding window chunking - fixed-size chunks with overlap"""

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Chunk using sliding window with fixed overlap"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = len(chunks)
            chunk_metadata['chunk_size'] = len(chunk_text)
            chunk_metadata['chunk_strategy'] = 'sliding_window'
            chunk_metadata['window_start'] = start
            chunk_metadata['window_end'] = end

            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })

            # Move window forward
            start += (self.chunk_size - self.overlap)

        return chunks


# Chunker factory
def get_chunker(strategy: str = 'semantic', chunk_size: int = 512, overlap: int = 50, **kwargs) -> ChunkingStrategy:
    """
    Get chunking strategy instance.

    Args:
        strategy: Chunking strategy ('semantic', 'sentence', 'recursive', 'sliding_window')
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        **kwargs: Additional strategy-specific parameters

    Returns:
        ChunkingStrategy instance
    """
    strategies = {
        'semantic': SemanticChunker,
        'sentence': SentenceChunker,
        'recursive': RecursiveChunker,
        'sliding_window': SlidingWindowChunker
    }

    if strategy not in strategies:
        logger.warning(f"Unknown strategy '{strategy}', using 'semantic'")
        strategy = 'semantic'

    chunker_class = strategies[strategy]

    if strategy == 'recursive' and 'separators' in kwargs:
        return chunker_class(chunk_size, overlap, separators=kwargs['separators'])
    else:
        return chunker_class(chunk_size, overlap)
