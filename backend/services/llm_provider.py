import json
import logging
import os
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, schema: type[T], max_retries: int = 1) -> tuple[T, dict]:
        """
        Generates a structured response matching the Pydantic schema.
        Returns a tuple of (parsed_model, usage_metrics).
        """

class AnthropicProvider(LLMProvider):
    def __init__(self):
        # We import here so that if the SDK isn't installed or configured, it doesn't break other providers
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"
        self.cost_input = 3.00
        self.cost_output = 15.00

    def _extract_json(self, text: str) -> str:
        if "```json" in text:
            return text.split("```json")[1].split("```", maxsplit=1)[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```", maxsplit=1)[0].strip()
        return text.strip()

    def generate_structured(self, prompt: str, schema: type[T], max_retries: int = 1) -> tuple[T, dict]:
        system_prompt = "You are a helpful assistant. Always output valid JSON strictly conforming to the requested schema. Do not include any other text."
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                content = response.content[0].text
                json_str = self._extract_json(content)
                data = json.loads(json_str)
                validated_data = schema(**data)
                
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = (input_tokens / 1_000_000) * self.cost_input + (output_tokens / 1_000_000) * self.cost_output
                
                return validated_data, {
                    "tokensUsed": input_tokens + output_tokens,
                    "estimatedCost": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Anthropic attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise
                prompt += f"\n\nERROR: The previous response failed validation. Please fix the following error and return only valid JSON:\n{e!s}"
                
        raise RuntimeError("Unexpected failure in AnthropicProvider")


class GeminiProvider(LLMProvider):
    def __init__(self):
        from google import genai
        from google.genai import types
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash"
        self.types = types

    def generate_structured(self, prompt: str, schema: type[T], max_retries: int = 1) -> tuple[T, dict]:
        system_prompt = "You are a helpful assistant. Always output valid JSON strictly conforming to the requested schema. Do not include any other text."
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )
                
                # Gemini structured output guarantees JSON conformity (mostly), but we validate anyway
                content = response.text
                data = json.loads(content)
                validated_data = schema(**data)
                
                # Usage metadata might not always be perfectly populated in free tier, but we try
                input_tokens = 0
                output_tokens = 0
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                    output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                
                # Gemini Flash free tier is free, so cost is 0
                return validated_data, {
                    "tokensUsed": input_tokens + output_tokens,
                    "estimatedCost": 0.0,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise
                prompt += f"\n\nERROR: The previous response failed validation. Please fix the following error and return only valid JSON:\n{e!s}"
                
        raise RuntimeError("Unexpected failure in GeminiProvider")


class MockProvider(LLMProvider):
    def generate_structured(self, prompt: str, schema: type[T], max_retries: int = 1) -> tuple[T, dict]:
        """
        Returns hardcoded mock data matching the requested schema.
        This allows the pipeline to be tested end-to-end without any API keys.
        """
        schema_name = schema.__name__
        
        if schema_name == "NotesProcessingResult":
            data = {
                "meeting_title": "Q3 Planning Session",
                "meeting_date": "2026-06-15",
                "summary": "Discussed Q3 goals and upcoming grant deadlines.",
                "decisions": ["Proceed with Hartley Foundation grant"],
                "action_items": [
                    {"task": "Confirm grant deadline", "owner": "Jose", "deadline": "2026-04-01"},
                    {"task": "Send budget update", "owner": "Maria", "deadline": "2026-06-20"},
                    {"task": "Draft newsletter", "owner": "Sarah", "deadline": "2026-06-30"},
                    {"task": "Update website", "owner": "Unassigned", "deadline": None},
                    {"task": "Review applications", "owner": "Unassigned", "deadline": None}
                ],
                "confidence": "high",
                "confidence_note": None
            }
        elif schema_name == "EmailSummarizerResult":
            data = {
                "summary": "Funders meeting rescheduled to next Thursday.",
                "action_items": ["Use the new reporting template", "Include volunteer hours"],
                "deadlines": "Next Thursday",
                "reply_urgency": "urgent",
                "reply_tone": "professional"
            }
        elif schema_name == "QAResult":
            if "hiring" in prompt.lower():
                data = {
                    "answer": "I couldn't find this in your uploaded notes. The question may be answered in documents that haven't been uploaded yet.",
                    "found": False,
                    "source_citation": None,
                    "matched_text": None
                }
            else:
                data = {
                    "answer": "The grant submission deadline is April 1.",
                    "found": True,
                    "source_citation": "source: sample_meeting_notes.txt \u00b7 chunk 2",
                    "matched_text": "Jose will reach out to the Hartley Foundation by this Friday to confirm the April 1 grant submission deadline."
                }
        else:
            # Fallback for unknown schemas
            data = {}
            
        validated_data = schema(**data)
        
        return validated_data, {
            "tokensUsed": 100,
            "estimatedCost": 0.0,
            "input_tokens": 50,
            "output_tokens": 50
        }


def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "mock":
        return MockProvider()
    else:
        logger.warning(f"Unknown provider '{provider_name}', falling back to mock")
        return MockProvider()
