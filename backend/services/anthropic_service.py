import os
import json
import logging
from typing import TypeVar, Type, Any
from pydantic import BaseModel, ValidationError
from anthropic import Anthropic

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

# Claude 3.5 Sonnet pricing (as of mid-2024, adjust if needed)
COST_PER_1M_INPUT_TOKENS = 3.00
COST_PER_1M_OUTPUT_TOKENS = 15.00

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
    return input_cost + output_cost

class AnthropicService:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"

    def _extract_json(self, text: str) -> str:
        # Simple extraction logic for JSON blocks if wrapped in markdown
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def generate_structured(self, prompt: str, schema: Type[T], max_retries: int = 1) -> tuple[T, dict]:
        """
        Generates a structured response matching the Pydantic schema.
        Returns a tuple of (parsed_model, usage_metrics).
        """
        system_prompt = "You are a helpful assistant. Always output valid JSON strictly conforming to the requested schema. Do not include any other text."
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                content = response.content[0].text
                json_str = self._extract_json(content)
                
                # Parse JSON
                data = json.loads(json_str)
                
                # Validate with Pydantic
                validated_data = schema(**data)
                
                # Calculate cost
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = estimate_cost(input_tokens, output_tokens)
                
                usage_metrics = {
                    "tokensUsed": input_tokens + output_tokens,
                    "estimatedCost": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
                
                return validated_data, usage_metrics
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise e
                # Adjust prompt for retry
                prompt += f"\n\nERROR: The previous response failed validation. Please fix the following error and return only valid JSON:\n{str(e)}"
                
        raise RuntimeError("Unexpected failure in generate_structured")
