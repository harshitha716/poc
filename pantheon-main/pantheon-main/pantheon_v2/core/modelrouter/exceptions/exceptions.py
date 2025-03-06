class ModelNotFoundError(ValueError):
    """Raised when a requested model is not found in the configurations."""

    pass


class GenerationError(RuntimeError):
    """Raised when an error occurs during response generation."""

    pass


class MaxTokensExceededError(Exception):
    """Raised when requested max_tokens exceeds model's capability"""

    pass


class EmbeddingError(Exception):
    """Error during embedding generation process"""

    pass
