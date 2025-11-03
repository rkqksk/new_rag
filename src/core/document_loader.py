from typing import List, Dict, Any
from pathlib import Path
from langchain.document_loaders import (
    PDFPlumberLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)

class FlexibleDocumentLoader:
    """
    Flexible document loader supporting multiple file types
    """
    LOADER_MAP = {
        '.pdf': PDFPlumberLoader,
        '.txt': TextLoader,
        '.csv': CSVLoader,
        '.md': UnstructuredMarkdownLoader
    }

    @classmethod
    def load_documents(cls, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Load documents from multiple file paths with type-specific loaders

        Args:
            file_paths: List of file paths to load

        Returns:
            List of loaded document dictionaries
        """
        loaded_documents = []

        for file_path in file_paths:
            path = Path(file_path)

            # Validate file existence
            if not path.exists():
                print(f"Warning: File not found - {file_path}")
                continue

            # Select appropriate loader
            loader_class = cls.LOADER_MAP.get(path.suffix.lower())

            if not loader_class:
                print(f"Unsupported file type: {path.suffix}")
                continue

            try:
                # Load document
                loader = loader_class(str(path))
                documents = loader.load()

                loaded_documents.extend(documents)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        return loaded_documents

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        Return list of supported file extensions

        Returns:
            List of supported file extensions
        """
        return list(cls.LOADER_MAP.keys())