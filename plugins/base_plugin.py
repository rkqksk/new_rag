"""
Base Plugin Interface for RAG Enterprise Domain Experts

Provides common interface for domain-specific document processing plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class DocumentMetadata:
    """Extracted document metadata"""
    doc_type: str
    domain: str
    categories: List[str]
    confidence: float
    extracted_entities: Dict[str, Any]
    terminology: List[str]
    

@dataclass
class ProcessingResult:
    """Result of document processing"""
    success: bool
    metadata: Optional[DocumentMetadata]
    chunks: List[Dict[str, Any]]
    enriched_content: str
    errors: List[str]


class BaseDomainPlugin(ABC):
    """Base class for domain-specific RAG plugins"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()
        self._initialize()
    
    @abstractmethod
    def _default_config_path(self) -> Path:
        """Return default config directory path"""
        pass
    
    def _load_config(self) -> Dict[str, Any]:
        """Load all YAML configs from config directory"""
        config = {}
        if not self.config_path.exists():
            return config
            
        for yaml_file in self.config_path.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config[yaml_file.stem] = yaml.safe_load(f)
        return config
    
    def _initialize(self):
        """Initialize plugin-specific resources"""
        pass
    
    @abstractmethod
    def can_process(self, document: Dict[str, Any]) -> bool:
        """
        Check if this plugin can process the document
        
        Args:
            document: Document dict with 'content', 'filename', 'metadata'
            
        Returns:
            True if plugin can handle this document
        """
        pass
    
    @abstractmethod
    def classify_document(self, document: Dict[str, Any]) -> str:
        """
        Classify document into domain-specific type
        
        Args:
            document: Document to classify
            
        Returns:
            Document type string
        """
        pass
    
    @abstractmethod
    def extract_terminology(self, text: str) -> List[str]:
        """
        Extract domain-specific terminology from text
        
        Args:
            text: Text to process
            
        Returns:
            List of extracted terms
        """
        pass
    
    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract domain-specific entities (specs, parameters, etc)
        
        Args:
            text: Text to process
            
        Returns:
            Dict of extracted entities
        """
        pass
    
    @abstractmethod
    def enrich_content(self, text: str, metadata: DocumentMetadata) -> str:
        """
        Enrich content with domain knowledge for better retrieval
        
        Args:
            text: Original text
            metadata: Extracted metadata
            
        Returns:
            Enriched text
        """
        pass
    
    def process_document(self, document: Dict[str, Any]) -> ProcessingResult:
        """
        Main processing pipeline
        
        Args:
            document: Document to process
            
        Returns:
            ProcessingResult with metadata and chunks
        """
        try:
            # Check if can process
            if not self.can_process(document):
                return ProcessingResult(
                    success=False,
                    metadata=None,
                    chunks=[],
                    enriched_content="",
                    errors=["Plugin cannot process this document"]
                )
            
            content = document.get('content', '')
            
            # Classify document
            doc_type = self.classify_document(document)
            
            # Extract terminology
            terminology = self.extract_terminology(content)
            
            # Extract entities
            entities = self.extract_entities(content)
            
            # Create metadata
            metadata = DocumentMetadata(
                doc_type=doc_type,
                domain=self.get_domain_name(),
                categories=self.get_categories(doc_type),
                confidence=self.calculate_confidence(document, terminology, entities),
                extracted_entities=entities,
                terminology=terminology
            )
            
            # Enrich content
            enriched = self.enrich_content(content, metadata)
            
            # Create chunks with metadata
            chunks = self.create_chunks(enriched, metadata)
            
            return ProcessingResult(
                success=True,
                metadata=metadata,
                chunks=chunks,
                enriched_content=enriched,
                errors=[]
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                metadata=None,
                chunks=[],
                enriched_content="",
                errors=[str(e)]
            )
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Return domain name (e.g., 'manufacturing', 'packaging')"""
        pass
    
    @abstractmethod
    def get_categories(self, doc_type: str) -> List[str]:
        """Get categories for document type"""
        pass
    
    def calculate_confidence(
        self, 
        document: Dict[str, Any],
        terminology: List[str],
        entities: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for domain match"""
        score = 0.0
        
        # Terminology match
        if terminology:
            score += 0.4
        
        # Entity extraction success
        if entities:
            score += 0.3
        
        # Filename/metadata hints
        filename = document.get('filename', '').lower()
        domain_keywords = self.config.get('keywords', [])
        if any(kw in filename for kw in domain_keywords):
            score += 0.3
        
        return min(score, 1.0)
    
    def create_chunks(
        self, 
        content: str, 
        metadata: DocumentMetadata,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Create chunks with metadata
        
        Args:
            content: Content to chunk
            metadata: Document metadata
            chunk_size: Target chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'doc_type': metadata.doc_type,
                    'domain': metadata.domain,
                    'categories': metadata.categories,
                    'chunk_index': len(chunks),
                    'terminology': [t for t in metadata.terminology if t in chunk_text]
                }
            })
            
            start = end - overlap
        
        return chunks
