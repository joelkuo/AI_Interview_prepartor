"""
Functional tests for the analysis API.

POST /api/rehearsals/{id}/analyze      — triggers background analysis
GET  /api/rehearsals/{id}/results      — returns status + feedback
GET  /api/rehearsals/{id}/export       — returns markdown

The full analysis pipeline (Whisper, LLM calls) is patched so tests are
fast and deterministic.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from tests.conftest import (
    FAKE_SLIDE_FEEDBACK,
    FAKE_SPEECH_FEEDBACK,
    FAKE_ALIGNMENT_FEEDBACK,
    FAKE_OVERALL_FEEDBACK,
)

SLIDES = [{"slide_number": 1, "title": "Intro", "content": "Hello", "notes": ""}]

FAKE_TRANSCRIPT = {
    "text": "Hello everyone, welcome to the quarterly review.",
    "segments": [{"start": 0.0, "end": 5.0, "text": "Hello everyone"}],
    "duration": 30.0,
    "language": "en",
}


async def _setup_rehearsal_with_audio(client, tmp_path) -> int:
    """Create a rehearsal, write a dummy audio file, upload its path directly."""
    from app.core.config import settings
    import io

    # Create rehearsal
    r = await client.post("/api/rehearsals", json={"title": "Analysis Test", "slides": SLIDES})
    rid = r.json()["id"]

    # Write a fake audio file to tmp_path
    audio_file = tmp_path / f"rehearsal_{rid}_fake.wav"
    audio_file.write_bytes(b"\x00" * 1024)

    # Manually set audio_path via DB (bypass actual upload)
    from tests.conftest import _TestSessionLocal
    from app.models.rehearsal import Rehearsal
    from sqlalchemy import select
    async with _TestSessionLocal() as db:
        result = await db.execute(select(Rehearsal).where(Rehearsal.id == rid))
        rehearsal = result.scalar_one()
        rehearsal.audio_path = str(audio_file)
        await db.commit()

    return rid


def _patch_full_pipeline():
    """Context manager that patches all external calls in the analysis pipeline."""
    return [
        patch("app.api.analysis.transcription.transcribe_audio", new=AsyncMock(return_value=FAKE_TRANSCRIPT)),
        patch("app.api.analysis.slide_analyzer.analyze_all_slides", new=AsyncMock(return_value=[FAKE_SLIDE_FEEDBACK])),
        patch("app.api.analysis.speech_analyzer.analyze_speech", new=AsyncMock(return_value=FAKE_SPEECH_FEEDBACK)),
        patch("app.api.analysis.alignment_analyzer.analyze_alignment", new=AsyncMock(return_value=FAKE_ALIGNMENT_FEEDBACK)),
        patch("app.api.analysis.call_llm", new=AsyncMock(return_value=json.dumps(FAKE_OVERALL_FEEDBACK))),
    ]


@pytest.mark.asyncio
class TestStartAnalysis:
    async def test_returns_202_accepted(self, client, tmp_path):
        rid = await _setup_rehearsal_with_audio(client, tmp_path)
        response = await client.post(f"/api/rehearsals/{rid}/analyze")
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

    async def test_nonexistent_rehearsal_returns_404(self, client):
        response = await client.post("/api/rehearsals/99999/analyze")
        assert response.status_code == 404

    async def test_duplicate_trigger_while_in_progress_returns_409(self, client, tmp_path):
        from tests.conftest import _TestSessionLocal
        from app.models.rehearsal import Rehearsal, AnalysisStatus
        from sqlalchemy import select

        rid = await _setup_rehearsal_with_audio(client, tmp_path)

        # Manually put rehearsal into an in-progress state
        async with _TestSessionLocal() as db:
            result = await db.execute(select(Rehearsal).where(Rehearsal.id == rid))
            r = result.scalar_one()
            r.status = AnalysisStatus.transcribing
            await db.commit()

        response = await client.post(f"/api/rehearsals/{rid}/analyze")
        assert response.status_code == 409


@pytest.mark.asyncio
class TestGetResults:
    async def test_returns_pending_status_before_analysis(self, client):
        r = await client.post("/api/rehearsals", json={"title": "Pending", "slides": SLIDES})
        rid = r.json()["id"]
        response = await client.get(f"/api/rehearsals/{rid}/results")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    async def test_nonexistent_rehearsal_returns_404(self, client):
        response = await client.get("/api/rehearsals/99999/results")
        assert response.status_code == 404

    async def test_complete_results_contain_all_sections(self, client, tmp_path):
        """After a mocked full pipeline run, results should have all feedback sections."""
        from app.api.analysis import _run_analysis

        rid = await _setup_rehearsal_with_audio(client, tmp_path)

        patches = _patch_full_pipeline()
        for p in patches:
            p.start()
        try:
            await _run_analysis(rid)
        finally:
            for p in patches:
                p.stop()

        response = await client.get(f"/api/rehearsals/{rid}/results")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "complete"
        assert body["overall"]["overall_score"] == FAKE_OVERALL_FEEDBACK["overall_score"]
        assert body["speech"]["score"] == FAKE_SPEECH_FEEDBACK["score"]
        assert body["alignment"]["score"] == FAKE_ALIGNMENT_FEEDBACK["score"]
        assert len(body["slides"]) == 1
        assert body["transcript"] == FAKE_TRANSCRIPT["text"]

    async def test_results_rehearsal_id_matches(self, client, tmp_path):
        from app.api.analysis import _run_analysis

        rid = await _setup_rehearsal_with_audio(client, tmp_path)
        patches = _patch_full_pipeline()
        for p in patches:
            p.start()
        try:
            await _run_analysis(rid)
        finally:
            for p in patches:
                p.stop()

        body = (await client.get(f"/api/rehearsals/{rid}/results")).json()
        assert body["rehearsal_id"] == rid


@pytest.mark.asyncio
class TestAnalysisPipelineSteps:
    """Verify each step of _run_analysis updates the DB status correctly."""

    async def test_status_set_to_failed_on_missing_audio(self, client):
        """Rehearsal with no audio_path should fail gracefully."""
        r = await client.post("/api/rehearsals", json={"title": "No Audio", "slides": SLIDES})
        rid = r.json()["id"]

        from app.api.analysis import _run_analysis
        with pytest.raises(ValueError, match="No audio"):
            await _run_analysis(rid)

        body = (await client.get(f"/api/rehearsals/{rid}/results")).json()
        assert body["status"] == "failed"

    async def test_status_set_to_failed_on_transcription_error(self, client, tmp_path):
        rid = await _setup_rehearsal_with_audio(client, tmp_path)

        from app.api.analysis import _run_analysis
        with patch("app.api.analysis.transcription.transcribe_audio",
                   new=AsyncMock(side_effect=RuntimeError("whisper crash"))):
            with pytest.raises(RuntimeError):
                await _run_analysis(rid)

        body = (await client.get(f"/api/rehearsals/{rid}/results")).json()
        assert body["status"] == "failed"


@pytest.mark.asyncio
class TestExportEndpoint:
    async def test_export_incomplete_returns_400(self, client):
        r = await client.post("/api/rehearsals", json={"title": "Not Done", "slides": []})
        rid = r.json()["id"]
        response = await client.get(f"/api/rehearsals/{rid}/export")
        assert response.status_code == 400

    async def test_export_nonexistent_returns_404(self, client):
        response = await client.get("/api/rehearsals/99999/export")
        assert response.status_code == 404

    async def test_export_complete_returns_markdown(self, client, tmp_path):
        from app.api.analysis import _run_analysis

        rid = await _setup_rehearsal_with_audio(client, tmp_path)
        patches = _patch_full_pipeline()
        for p in patches:
            p.start()
        try:
            await _run_analysis(rid)
        finally:
            for p in patches:
                p.stop()

        response = await client.get(f"/api/rehearsals/{rid}/export")
        assert response.status_code == 200
        text = response.text
        assert "# Presentation Coaching Feedback" in text
        assert str(rid) in text

    async def test_export_content_type_is_markdown(self, client, tmp_path):
        from app.api.analysis import _run_analysis

        rid = await _setup_rehearsal_with_audio(client, tmp_path)
        patches = _patch_full_pipeline()
        for p in patches:
            p.start()
        try:
            await _run_analysis(rid)
        finally:
            for p in patches:
                p.stop()

        response = await client.get(f"/api/rehearsals/{rid}/export")
        assert "markdown" in response.headers.get("content-type", "")
