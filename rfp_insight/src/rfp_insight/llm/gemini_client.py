# src/rfp_insight/llm/gemini_client.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Type, TypeVar

from google import genai
from google.genai import types

T = TypeVar("T")


@dataclass
class GeminiClient:
    api_key: str

    def __post_init__(self) -> None:
        self.client = genai.Client(api_key=self.api_key)

    def generate_structured(
        self,
        model: str,
        system_instruction: str,
        user_prompt: str,
        full_text: str,
        schema: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """
        Generate structured output using Pydantic schema.
        """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=user_prompt),
                    types.Part(text="\n\n=== DOCUMENT START ===\n" + full_text + "\n=== DOCUMENT END ===\n"),
                ],
            )
        ]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,  # Pydantic model class
        )

        resp = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # GenAI SDK returns parsed object when schema is provided
        # Fallback: resp.text -> json parsing would be added if needed
        if getattr(resp, "parsed", None) is not None:
            return resp.parsed  # type: ignore[return-value]

        # If SDK doesn't parse automatically in some environments,
        # we keep a small fallback.
        import json
        return schema.model_validate(json.loads(resp.text))
