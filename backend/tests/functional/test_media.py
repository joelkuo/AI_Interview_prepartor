"""
Functional tests for audio upload  POST /api/rehearsals/{id}/audio
"""
import io
import pytest


def _make_audio_file(size_bytes: int = 1024, filename: str = "test.webm") -> tuple:
    """Return (filename, file-like, content-type) for multipart upload."""
    content = b"\x00" * size_bytes
    return filename, io.BytesIO(content), "audio/webm"


@pytest.mark.asyncio
class TestAudioUpload:
    async def _create_rehearsal(self, client) -> int:
        r = await client.post("/api/rehearsals", json={"title": "Audio Test", "slides": []})
        return r.json()["id"]

    async def test_upload_webm_succeeds(self, client, tmp_path, monkeypatch):
        # Point media_dir to a temp directory so the file is actually written
        from app.core.config import settings
        monkeypatch.setattr(settings, "media_dir", tmp_path)

        rid = await self._create_rehearsal(client)
        fname, fobj, ctype = _make_audio_file(filename="speech.webm")

        response = await client.post(
            f"/api/rehearsals/{rid}/audio",
            files={"audio": (fname, fobj, ctype)},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["rehearsal_id"] == rid
        assert body["size_bytes"] == 1024

    async def test_upload_updates_audio_path(self, client, tmp_path, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "media_dir", tmp_path)

        rid = await self._create_rehearsal(client)
        fname, fobj, ctype = _make_audio_file(filename="speech.wav")

        await client.post(
            f"/api/rehearsals/{rid}/audio",
            files={"audio": (fname, fobj, ctype)},
        )
        detail = (await client.get(f"/api/rehearsals/{rid}")).json()
        assert detail["audio_path"] is not None

    async def test_upload_to_nonexistent_rehearsal_returns_404(self, client, tmp_path, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "media_dir", tmp_path)

        fname, fobj, ctype = _make_audio_file()
        response = await client.post(
            "/api/rehearsals/99999/audio",
            files={"audio": (fname, fobj, ctype)},
        )
        assert response.status_code == 404

    async def test_unsupported_file_type_returns_400(self, client, tmp_path, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "media_dir", tmp_path)

        rid = await self._create_rehearsal(client)
        response = await client.post(
            f"/api/rehearsals/{rid}/audio",
            files={"audio": ("file.pdf", io.BytesIO(b"pdf content"), "application/pdf")},
        )
        assert response.status_code == 400

    async def test_accepted_extensions(self, client, tmp_path, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "media_dir", tmp_path)

        for ext, ctype in [(".mp3", "audio/mpeg"), (".wav", "audio/wav"),
                           (".ogg", "audio/ogg"), (".m4a", "audio/mp4")]:
            rid = await self._create_rehearsal(client)
            _, fobj, _ = _make_audio_file()
            response = await client.post(
                f"/api/rehearsals/{rid}/audio",
                files={"audio": (f"audio{ext}", fobj, ctype)},
            )
            assert response.status_code == 200, f"Extension {ext} should be accepted"
