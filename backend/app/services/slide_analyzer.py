from app.core.prompts import SLIDE_ANALYSIS_PROMPT
from app.services.llm_client import call_llm, extract_json


async def analyze_slide(slide_number: int, total_slides: int, title: str, content: str, notes: str) -> dict:
    prompt = SLIDE_ANALYSIS_PROMPT.format(
        slide_number=slide_number,
        total_slides=total_slides,
        title=title or "(no title)",
        content=content or "(no content)",
        notes=notes or "(no notes)",
    )
    raw = await call_llm(prompt, task="slide_analysis")
    result = extract_json(raw)
    result["slide_number"] = slide_number
    return result


async def analyze_all_slides(slides: list[dict]) -> list[dict]:
    """Analyze all slides, running sequentially to avoid rate limits."""
    results = []
    total = len(slides)
    for slide in slides:
        result = await analyze_slide(
            slide_number=slide.get("slide_number", 0),
            total_slides=total,
            title=slide.get("title", ""),
            content=slide.get("content", ""),
            notes=slide.get("notes", ""),
        )
        results.append(result)
    return results
