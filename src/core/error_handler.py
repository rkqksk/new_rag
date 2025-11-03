import logging
import traceback
from typing import Any, Optional, Dict

class RAGError(Exception):
    """Base exception for RAG pipeline errors"""
    def __init__(self, message: str, error_type: str = "UnknownError"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

class ErrorHandler:
    """Comprehensive error handling and logging utility"""

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_file: Optional[str] = "rag_pipeline.log"
    ):
        """
        Initialize error handler with logging configuration

        Args:
            log_level: Logging level (default: INFO)
            log_file: Path to log file (optional)
        """
        # Configure logging
        self.logger = logging.getLogger("RAGPipeline")
        self.logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = 'error'
    ) -> Dict[str, Any]:
        """
        Comprehensive error logging with structured output

        Args:
            error: Exception object
            context: Additional context for error
            severity: Error severity level

        Returns:
            Structured error information
        """
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }

        log_method = getattr(self.logger, severity, self.logger.error)
        log_method(
            f"{error_info['error_type']}: {error_info['error_message']}\n"
            f"Context: {error_info['context']}\n"
            f"Traceback:\n{error_info['traceback']}"
        )

        return error_info

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = 'error'
    ) -> bool:
        """
        Error handling with optional retry or fallback mechanisms

        Args:
            error: Exception object
            context: Additional error context
            severity: Error severity level

        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            # Log the error
            error_info = self.log_error(error, context, severity)

            # You can add custom error handling logic here
            # For example, retry mechanisms, fallback strategies, etc.

            return True
        except Exception as handler_error:
            # Fallback error logging if primary error handler fails
            self.logger.critical(
                f"Error handler failed: {handler_error}\n"
                f"Original Error: {error}"
            )
            return False

    def create_error_event(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGError:
        """
        Create a standardized RAG error event

        Args:
            error_type: Type of error
            message: Error description
            context: Additional context

        Returns:
            RAGError instance
        """
        return RAGError(
            message=message,
            error_type=error_type
        )