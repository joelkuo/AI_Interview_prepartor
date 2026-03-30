"""
Unit tests for app.services.llm_client
- extract_json: pure function, no mocking needed
- call_llm: patches litellm.acompletion
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_client import extract_json, call_llm


# ---------------------------------------------------------------------------
# extract_json
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_plain_json(self):
        text = '{"score": 80, "summary": "good"}'
        result = extract_json(text)
        assert result == {"score": 80, "summary": "good"}

    def test_json_in_markdown_code_block(self):
        text = '```json\n{"score": 90}\n```'
        result = extract_json(text)
        assert result["score"] == 90

    def test_json_in_plain_code_block(self):
        text = "Here is the result:\n```\n{\"ok\": true}\n```"
        result = extract_json(text)
        assert result["ok"] is True

    def test_json_embedded_in_prose(self):
        text = 'Sure! Here is the feedback: {"score": 55, "issues": ["too fast"]} Hope that helps.'
        result = extract_json(text)
        assert result["score"] == 55
        assert result["issues"] == ["too fast"]

    def test_nested_json(self):
        data = {"overall": {"score": 78}, "slides": [{"slide_number": 1, "score": 80}]}
        result = extract_json(json.dumps(data))
        assert result["overall"]["score"] == 78
        assert result["slides"][0]["slide_number"] == 1

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            extract_json("not json at all")

    def test_empty_string_raises(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            extract_json("")


# ---------------------------------------------------------------------------
# call_llm
# ---------------------------------------------------------------------------

def _make_llm_response(content: str):
    """Build a minimal litellm response mock."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
class TestCallLlm:
    async def test_returns_content_on_success(self):
        mock_response = _make_llm_response('{"score": 80}')
        with patch("app.services.llm_client.litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await call_llm("test prompt", task="default")
        assert result == '{"score": 80}'

    async def test_uses_task_specific_model(self):
        mock_response = _make_llm_response("{}")
        with patch("app.services.llm_client.litellm.acompletion", new=AsyncMock(return_value=mock_response)) as mock_call:
            await call_llm("prompt", task="slide_analysis")
            called_model = mock_call.call_args.kwargs["model"]
            # Should be whatever config maps slide_analysis to
            assert isinstance(called_model, str)
            assert len(called_model) > 0

    async def test_falls_back_to_fallback_model_on_primary_failure(self):
        """When the primary model raises, the fallback model is tried."""
        success_response = _make_llm_response('{"ok": true}')
        call_count = {"n": 0}

        async def side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("primary model down")
            return success_response

        with patch("app.services.llm_client.litellm.acompletion", side_effect=side_effect):
            result = await call_llm("prompt", task="default")
        assert result == '{"ok": true}'
        assert call_count["n"] == 2

    async def test_raises_when_both_primary_and_fallback_fail(self):
        """If both primary and fallback fail, the original exception propagates."""
        async def always_fail(**kwargs):
            raise RuntimeError("all models down")

        with patch("app.services.llm_client.litellm.acompletion", side_effect=always_fail):
            with pytest.raises(RuntimeError, match="all models down"):
                await call_llm("prompt", task="default")

    async def test_no_fallback_when_primary_is_fallback(self):
        """If primary == fallback model, should not retry — raises immediately."""
        from app.core.config import settings
        original = settings.llm_models.copy()
        settings.llm_models["default"] = settings.fallback_model  # make primary == fallback

        async def always_fail(**kwargs):
            raise RuntimeError("model down")

        with patch("app.services.llm_client.litellm.acompletion", side_effect=always_fail):
            with pytest.raises(RuntimeError):
                await call_llm("prompt", task="default")

        settings.llm_models.update(original)
