"""
Compatibility wrapper around AnthropicProvider in llm_provider.py.
Ensures zero duplication while maintaining backwards compatibility.
"""
from typing import TypeVar, Type
from pydantic import BaseModel
from services.llm_provider import AnthropicProvider

T = TypeVar('T', bound=BaseModel)

class AnthropicService(AnthropicProvider):
    """
    Backward-compatible wrapper for AnthropicService that inherits from AnthropicProvider.
    """
    pass
