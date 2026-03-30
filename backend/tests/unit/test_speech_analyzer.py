"""
Unit tests for app.services.speech_analyzer

_count_filler_words and _compute_stats are pure functions tested directly.
analyze_speech patches call_llm to avoid real LLM calls.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.speech_analyzer import (
    _count_filler_words,
    _compute_stats,
    analyze_speech,
)


# ---------------------------------------------------------------------------
# _count_filler_words
# ---------------------------------------------------------------------------

class TestCountFillerWords:
    def test_detects_basic_fillers(self):
        text = "Um so I was like you know basically done"
        counts = _count_filler_words(text)
        assert counts.get("um") == 1
        assert counts.get("so") == 1
        assert counts.get("like") == 1
        assert counts.get("you know") == 1
        assert counts.get("basically") == 1

    def test_case_insensitive(self):
        counts = _count_filler_words("UM UH Like BASICALLY")
        assert counts.get("um") == 1
        assert counts.get("uh") == 1
        assert counts.get("like") == 1
        assert counts.get("basically") == 1

    def test_no_fillers_returns_empty(self):
        counts = _count_filler_words("The quarterly results exceeded projections.")
        assert counts == {}

    def test_multiple_occurrences(self):
        counts = _count_filler_words("um the um thing is um clear")
        assert counts.get("um") == 3

    def test_word_boundary_not_partial_match(self):
        # "like" inside "likewise" must NOT be counted
        counts = _count_filler_words("likewise the umbrella")
        assert counts.get("like") is None

    def test_empty_string(self):
        assert _count_filler_words("") == {}


# ---------------------------------------------------------------------------
# _compute_stats
# ---------------------------------------------------------------------------

class TestComputeStats:
    def test_wpm_calculation(self):
        # 120 words in 60 seconds = 120 WPM
        words = " ".join(["word"] * 120)
        stats = _compute_stats({"text": words, "duration": 60.0})
        assert stats["wpm"] == pytest.approx(120.0)
        assert stats["word_count"] == 120

    def test_zero_duration_gives_zero_wpm(self):
        stats = _compute_stats({"text": "hello world", "duration": 0})
        assert stats["wpm"] == 0

    def test_filler_count_aggregated(self):
        stats = _compute_stats({"text": "um uh um like", "duration": 10.0})
        assert stats["filler_count"] == 4

    def test_empty_text(self):
        stats = _compute_stats({"text": "", "duration": 30.0})
        assert stats["word_count"] == 0
        assert stats["wpm"] == 0
        assert stats["filler_count"] == 0

    def test_duration_stored(self):
        stats = _compute_stats({"text": "hello", "duration": 42.5})
        assert stats["duration_seconds"] == 42.5


# ---------------------------------------------------------------------------
# analyze_speech  (LLM mocked)
# ---------------------------------------------------------------------------

FAKE_LLM_RESPONSE = """{
    "score": 78,
    "wpm": 145.0,
    "filler_word_count": 2,
    "filler_words_detail": {"um": 2},
    "strengths": ["Good pace"],
    "issues": ["Some filler words"],
    "suggestions": ["Pause instead of filler words"],
    "summary": "Solid delivery."
}"""


@pytest.mark.asyncio
class TestAnalyzeSpeech:
    async def test_returns_llm_score(self):
        with patch("app.services.speech_analyzer.call_llm", new=AsyncMock(return_value=FAKE_LLM_RESPONSE)):
            result = await analyze_speech({"text": "Hello world um", "duration": 5.0})
        assert result["score"] == 78

    async def test_populates_missing_wpm_from_stats(self):
        """If LLM omits wpm, it should be back-filled from local calculation."""
        llm_without_wpm = '{"score": 70, "strengths": [], "issues": [], "suggestions": [], "summary": "ok"}'
        words = " ".join(["word"] * 60)
        with patch("app.services.speech_analyzer.call_llm", new=AsyncMock(return_value=llm_without_wpm)):
            result = await analyze_speech({"text": words, "duration": 60.0})
        assert result["wpm"] == pytest.approx(60.0, rel=0.1)

    async def test_populates_missing_filler_count_from_stats(self):
        llm_no_fillers = '{"score": 80, "strengths": [], "issues": [], "suggestions": [], "summary": "ok"}'
        with patch("app.services.speech_analyzer.call_llm", new=AsyncMock(return_value=llm_no_fillers)):
            result = await analyze_speech({"text": "um uh um", "duration": 10.0})
        assert result["filler_word_count"] == 3

    async def test_handles_json_in_markdown_block(self):
        wrapped = f"```json\n{FAKE_LLM_RESPONSE}\n```"
        with patch("app.services.speech_analyzer.call_llm", new=AsyncMock(return_value=wrapped)):
            result = await analyze_speech({"text": "test", "duration": 5.0})
        assert result["score"] == 78

    async def test_empty_transcript(self):
        with patch("app.services.speech_analyzer.call_llm", new=AsyncMock(return_value=FAKE_LLM_RESPONSE)):
            result = await analyze_speech({"text": "", "duration": 0.0})
        assert "score" in result
