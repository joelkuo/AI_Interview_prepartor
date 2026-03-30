import re
from app.core.prompts import SPEECH_ANALYSIS_PROMPT
from app.services.llm_client import call_llm, extract_json

FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "literally", "actually", "so", "right"]


def _count_filler_words(text: str) -> dict[str, int]:
    text_lower = text.lower()
    counts = {}
    for filler in FILLER_WORDS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        count = len(re.findall(pattern, text_lower))
        if count > 0:
            counts[filler] = count
    return counts


def _compute_stats(transcript_data: dict) -> dict:
    text = transcript_data.get("text", "")
    duration = transcript_data.get("duration", 0)
    words = text.split()
    word_count = len(words)
    wpm = (word_count / duration * 60) if duration > 0 else 0
    filler_words = _count_filler_words(text)
    filler_count = sum(filler_words.values())
    return {
        "word_count": word_count,
        "duration_seconds": duration,
        "wpm": wpm,
        "filler_words": filler_words,
        "filler_count": filler_count,
    }


async def analyze_speech(transcript_data: dict) -> dict:
    stats = _compute_stats(transcript_data)
    prompt = SPEECH_ANALYSIS_PROMPT.format(
        transcript=transcript_data.get("text", ""),
        duration_seconds=stats["duration_seconds"],
        word_count=stats["word_count"],
        wpm=stats["wpm"],
        filler_words=stats["filler_words"],
    )
    raw = await call_llm(prompt, task="speech_analysis")
    result = extract_json(raw)
    # Ensure stats are populated even if LLM skips them
    result.setdefault("wpm", round(stats["wpm"], 1))
    result.setdefault("filler_word_count", stats["filler_count"])
    result.setdefault("filler_words_detail", stats["filler_words"])
    return result
