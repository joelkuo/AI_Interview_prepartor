"""
Unit tests for app.services.slide_analyzer
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.slide_analyzer import analyze_slide, analyze_all_slides

FAKE_SLIDE_RESPONSE = """{
    "slide_number": 1,
    "score": 82,
    "strengths": ["Clear title"],
    "issues": ["Dense text"],
    "suggestions": ["Use bullet points"],
    "summary": "Decent slide, reduce text density."
}"""


@pytest.mark.asyncio
class TestAnalyzeSlide:
    async def test_returns_expected_fields(self):
        with patch("app.services.slide_analyzer.call_llm", new=AsyncMock(return_value=FAKE_SLIDE_RESPONSE)):
            result = await analyze_slide(1, 5, "Intro", "Content here", "Notes here")
        assert result["score"] == 82
        assert result["slide_number"] == 1
        assert "strengths" in result
        assert "issues" in result
        assert "suggestions" in result

    async def test_slide_number_always_set(self):
        """slide_number must be overwritten even if LLM returns a different value."""
        wrong_num = FAKE_SLIDE_RESPONSE.replace('"slide_number": 1', '"slide_number": 99')
        with patch("app.services.slide_analyzer.call_llm", new=AsyncMock(return_value=wrong_num)):
            result = await analyze_slide(3, 5, "Slide 3", "", "")
        assert result["slide_number"] == 3

    async def test_empty_content_handled(self):
        with patch("app.services.slide_analyzer.call_llm", new=AsyncMock(return_value=FAKE_SLIDE_RESPONSE)):
            result = await analyze_slide(1, 1, "", "", "")
        assert "score" in result

    async def test_prompts_include_no_title_placeholder(self):
        """When title is empty the prompt should substitute '(no title)'."""
        captured = {}

        async def capture_prompt(prompt, **kwargs):
            captured["prompt"] = prompt
            return FAKE_SLIDE_RESPONSE

        with patch("app.services.slide_analyzer.call_llm", side_effect=capture_prompt):
            await analyze_slide(1, 1, "", "some content", "")
        assert "(no title)" in captured["prompt"]


@pytest.mark.asyncio
class TestAnalyzeAllSlides:
    async def test_returns_result_for_each_slide(self):
        slides = [
            {"slide_number": 1, "title": "S1", "content": "c1", "notes": ""},
            {"slide_number": 2, "title": "S2", "content": "c2", "notes": ""},
            {"slide_number": 3, "title": "S3", "content": "c3", "notes": ""},
        ]

        call_n = {"n": 0}

        async def fake_llm(prompt, **kwargs):
            call_n["n"] += 1
            n = call_n["n"]
            return f'{{"slide_number": {n}, "score": {70 + n}, "strengths": [], "issues": [], "suggestions": [], "summary": "ok"}}'

        with patch("app.services.slide_analyzer.call_llm", side_effect=fake_llm):
            results = await analyze_all_slides(slides)

        assert len(results) == 3
        assert results[0]["slide_number"] == 1
        assert results[1]["slide_number"] == 2
        assert results[2]["slide_number"] == 3

    async def test_empty_slides_list_returns_empty(self):
        with patch("app.services.slide_analyzer.call_llm", new=AsyncMock(return_value=FAKE_SLIDE_RESPONSE)):
            results = await analyze_all_slides([])
        assert results == []
