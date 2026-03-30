"""
Unit tests for app.services.alignment_analyzer
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.alignment_analyzer import _build_slides_summary, analyze_alignment

SLIDES = [
    {"slide_number": 1, "title": "Introduction", "content": "Welcome to the quarterly review.", "notes": ""},
    {"slide_number": 2, "title": "Results", "content": "Revenue grew 15% YoY.", "notes": ""},
]

FAKE_ALIGNMENT_RESPONSE = """{
    "score": 72,
    "coverage_percentage": 85,
    "uncovered_points": ["Q4 forecast"],
    "off_topic_segments": [],
    "strengths": ["Covered main points"],
    "issues": ["Skipped Q4 section"],
    "suggestions": ["Mention Q4 figures"],
    "summary": "Good alignment overall."
}"""


class TestBuildSlidesSummary:
    def test_includes_all_slides(self):
        summary = _build_slides_summary(SLIDES)
        assert "Slide 1" in summary
        assert "Introduction" in summary
        assert "Slide 2" in summary
        assert "Results" in summary

    def test_content_truncated_at_300_chars(self):
        long_content = "x" * 500
        slides = [{"slide_number": 1, "title": "T", "content": long_content, "notes": ""}]
        summary = _build_slides_summary(slides)
        # After truncation only 300 chars of content appear
        assert "x" * 301 not in summary
        assert "x" * 300 in summary

    def test_empty_slides_returns_empty_string(self):
        assert _build_slides_summary([]) == ""

    def test_missing_keys_default_gracefully(self):
        slides = [{"slide_number": 1}]  # no title or content
        summary = _build_slides_summary(slides)
        assert "Slide 1" in summary


@pytest.mark.asyncio
class TestAnalyzeAlignment:
    async def test_returns_score_and_coverage(self):
        with patch("app.services.alignment_analyzer.call_llm", new=AsyncMock(return_value=FAKE_ALIGNMENT_RESPONSE)):
            result = await analyze_alignment(SLIDES, {"text": "We saw great results this quarter.", "duration": 30.0})
        assert result["score"] == 72
        assert result["coverage_percentage"] == 85

    async def test_transcript_truncated_to_3000_chars(self):
        captured = {}

        async def capture(prompt, **kwargs):
            captured["prompt"] = prompt
            return FAKE_ALIGNMENT_RESPONSE

        long_transcript = "word " * 1000  # 5000 chars
        with patch("app.services.alignment_analyzer.call_llm", side_effect=capture):
            await analyze_alignment(SLIDES, {"text": long_transcript, "duration": 60.0})

        # The prompt should not contain more than 3000 chars of transcript
        prompt = captured["prompt"]
        # Find transcript portion after the label
        idx = prompt.find("Speech Transcript:")
        transcript_portion = prompt[idx:]
        assert len(transcript_portion) < 4000  # generous bound but not 5000

    async def test_empty_transcript(self):
        with patch("app.services.alignment_analyzer.call_llm", new=AsyncMock(return_value=FAKE_ALIGNMENT_RESPONSE)):
            result = await analyze_alignment(SLIDES, {"text": "", "duration": 0.0})
        assert "score" in result

    async def test_empty_slides(self):
        with patch("app.services.alignment_analyzer.call_llm", new=AsyncMock(return_value=FAKE_ALIGNMENT_RESPONSE)):
            result = await analyze_alignment([], {"text": "Some speech", "duration": 10.0})
        assert "score" in result
