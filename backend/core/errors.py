"""
Domain Error Taxonomy for ClarityDesk.
Maps internal domain failures to explicit, predictable exception types
instead of generic catch-all Exception blocks.
"""

class ClarityDeskError(Exception):
    """Base exception for all ClarityDesk domain errors."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class RetrievalError(ClarityDeskError):
    """Raised when document retrieval or similarity search fails."""
    def __init__(self, message: str = "Failed to retrieve relevant document context"):
        super().__init__(message, status_code=500, error_code="RETRIEVAL_ERROR")

class EmbeddingError(ClarityDeskError):
    """Raised when embedding model inference fails."""
    def __init__(self, message: str = "Embedding generation failed"):
        super().__init__(message, status_code=500, error_code="EMBEDDING_ERROR")

class ProviderTimeoutError(ClarityDeskError):
    """Raised when an external LLM provider times out."""
    def __init__(self, provider: str, message: str = "LLM provider timed out"):
        super().__init__(
            f"{provider} timeout: {message}",
            status_code=504,
            error_code="PROVIDER_TIMEOUT"
        )

class ProviderUnavailableError(ClarityDeskError):
    """Raised when an external LLM provider returns a service unavailable or authentication error."""
    def __init__(self, provider: str, message: str = "LLM provider is currently unavailable"):
        super().__init__(
            f"{provider} unavailable: {message}",
            status_code=503,
            error_code="PROVIDER_UNAVAILABLE"
        )

class DocumentProcessingError(ClarityDeskError):
    """Raised when PDF/DOCX parsing or text extraction fails."""
    def __init__(self, filename: str, reason: str):
        super().__init__(
            f"Failed to process document '{filename}': {reason}",
            status_code=422,
            error_code="DOCUMENT_PROCESSING_ERROR"
        )
