import os
from unittest.mock import MagicMock, patch

from pydantic import BaseModel
from services.llm_provider import (
    AnthropicProvider,
    GeminiProvider,
    MockProvider,
    get_llm_provider,
)


class SampleSchema(BaseModel):
    name: str
    age: int

@patch("google.genai.Client")
@patch("anthropic.Anthropic")
def test_get_llm_provider_factory(mock_anthropic, mock_gemini):
    with patch.dict(os.environ, {"LLM_PROVIDER": "mock"}):
        assert isinstance(get_llm_provider(), MockProvider)
    with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
        assert isinstance(get_llm_provider(), AnthropicProvider)
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}):
        assert isinstance(get_llm_provider(), GeminiProvider)
    with patch.dict(os.environ, {"LLM_PROVIDER": "unknown_provider"}):
        assert isinstance(get_llm_provider(), MockProvider)

@patch("anthropic.Anthropic")
def test_anthropic_provider_generate_structured(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='```json\n{"name": "Alice", "age": 30}\n```')]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response

    provider = AnthropicProvider()
    provider.client = mock_client

    result, metrics = provider.generate_structured("test prompt", SampleSchema)
    assert result.name == "Alice"
    assert result.age == 30
    assert metrics["input_tokens"] == 100
    assert metrics["output_tokens"] == 50
    assert "estimatedCost" in metrics

@patch("anthropic.Anthropic")
def test_anthropic_provider_retry_on_invalid_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # First attempt returns invalid JSON, second returns valid JSON
    bad_resp = MagicMock()
    bad_resp.content = [MagicMock(text="not valid json")]
    bad_resp.usage.input_tokens = 10
    bad_resp.usage.output_tokens = 10

    good_resp = MagicMock()
    good_resp.content = [MagicMock(text='{"name": "Bob", "age": 25}')]
    good_resp.usage.input_tokens = 20
    good_resp.usage.output_tokens = 20

    mock_client.messages.create.side_effect = [bad_resp, good_resp]

    provider = AnthropicProvider()
    provider.client = mock_client

    result, _ = provider.generate_structured("test prompt", SampleSchema, max_retries=1)
    assert result.name == "Bob"
    assert result.age == 25
    assert mock_client.messages.create.call_count == 2

@patch("google.genai.Client")
def test_gemini_provider_generate_structured(mock_gemini_cls):
    mock_client = MagicMock()
    mock_gemini_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = '{"name": "Charlie", "age": 40}'
    mock_response.usage_metadata.prompt_token_count = 80
    mock_response.usage_metadata.candidates_token_count = 20
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider()
    provider.client = mock_client

    result, metrics = provider.generate_structured("test prompt", SampleSchema)
    assert result.name == "Charlie"
    assert result.age == 40
    assert metrics["input_tokens"] == 80
    assert metrics["output_tokens"] == 20
    assert metrics["estimatedCost"] == 0.0

@patch("google.genai.Client")
def test_gemini_provider_retry_on_validation_error(mock_gemini_cls):
    mock_client = MagicMock()
    mock_gemini_cls.return_value = mock_client

    # First attempt missing required age field, second valid
    bad_resp = MagicMock()
    bad_resp.text = '{"name": "David"}'

    good_resp = MagicMock()
    good_resp.text = '{"name": "David", "age": 50}'
    good_resp.usage_metadata.prompt_token_count = 10
    good_resp.usage_metadata.candidates_token_count = 10

    mock_client.models.generate_content.side_effect = [bad_resp, good_resp]

    provider = GeminiProvider()
    provider.client = mock_client

    result, _ = provider.generate_structured("test prompt", SampleSchema, max_retries=1)
    assert result.name == "David"
    assert result.age == 50
    assert mock_client.models.generate_content.call_count == 2
