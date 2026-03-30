import json
import re
from typing import Any
import litellm
from app.core.config import settings

# Suppress litellm verbose logging
litellm.set_verbose = False


async def call_llm(prompt: str, task: str = "default", temperature: float = 0.3) -> str:
    """Call LLM via LiteLLM with task-based model routing."""
    model = settings.get_model_for_task(task)
    try:
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2000,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        fallback = settings.fallback_model
        if model == fallback:
            raise
        try:
            response = await litellm.acompletion(
                model=fallback,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content or ""
        except Exception:
            raise e


def extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)

    # Find the first { and last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)
