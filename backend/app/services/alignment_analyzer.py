from app.core.prompts import ALIGNMENT_ANALYSIS_PROMPT
from app.services.llm_client import call_llm, extract_json


def _build_slides_summary(slides: list[dict]) -> str:
    lines = []
    for slide in slides:
        num = slide.get("slide_number", "?")
        title = slide.get("title", "")
        content = slide.get("content", "")[:300]
        lines.append(f"Slide {num}: {title}\n{content}")
    return "\n\n".join(lines)


async def analyze_alignment(slides: list[dict], transcript_data: dict) -> dict:
    slides_summary = _build_slides_summary(slides)
    transcript = transcript_data.get("text", "")

    prompt = ALIGNMENT_ANALYSIS_PROMPT.format(
        slides_summary=slides_summary,
        transcript=transcript[:3000],  # Limit to avoid token overflow
    )
    raw = await call_llm(prompt, task="alignment_analysis")
    return extract_json(raw)
