"""
Functional tests for the rehearsals CRUD API.

POST   /api/rehearsals
GET    /api/rehearsals
GET    /api/rehearsals/{id}
DELETE /api/rehearsals/{id}
"""
import pytest

SLIDES_PAYLOAD = [
    {"slide_number": 1, "title": "Intro", "content": "Welcome everyone.", "notes": "Smile!"},
    {"slide_number": 2, "title": "Results", "content": "Revenue up 20%.", "notes": ""},
    {"slide_number": 3, "title": "Next Steps", "content": "Action items.", "notes": "Be concise."},
]


@pytest.mark.asyncio
class TestCreateRehearsal:
    async def test_creates_and_returns_id(self, client):
        response = await client.post("/api/rehearsals", json={"title": "Q3 Review", "slides": SLIDES_PAYLOAD})
        assert response.status_code == 200
        body = response.json()
        assert body["id"] >= 1
        assert body["title"] == "Q3 Review"
        assert body["slide_count"] == 3
        assert body["status"] == "pending"

    async def test_default_title_used_when_omitted(self, client):
        response = await client.post("/api/rehearsals", json={"slides": SLIDES_PAYLOAD})
        assert response.status_code == 200
        assert response.json()["title"] == "Untitled Presentation"

    async def test_creates_with_zero_slides(self, client):
        response = await client.post("/api/rehearsals", json={"title": "Empty", "slides": []})
        assert response.status_code == 200
        assert response.json()["slide_count"] == 0

    async def test_missing_slides_key_returns_422(self, client):
        response = await client.post("/api/rehearsals", json={"title": "Bad"})
        assert response.status_code == 422

    async def test_slide_with_only_required_field(self, client):
        """slide_number is the only required field; others default to empty string."""
        response = await client.post(
            "/api/rehearsals",
            json={"title": "Minimal", "slides": [{"slide_number": 1}]},
        )
        assert response.status_code == 200
        assert response.json()["slide_count"] == 1


@pytest.mark.asyncio
class TestListRehearsals:
    async def test_empty_list_initially(self, client):
        response = await client.get("/api/rehearsals")
        assert response.status_code == 200
        body = response.json()
        assert "rehearsals" in body
        assert isinstance(body["rehearsals"], list)
        assert body["total"] == len(body["rehearsals"])

    async def test_created_rehearsal_appears_in_list(self, client):
        await client.post("/api/rehearsals", json={"title": "Listed", "slides": SLIDES_PAYLOAD})
        response = await client.get("/api/rehearsals")
        titles = [r["title"] for r in response.json()["rehearsals"]]
        assert "Listed" in titles

    async def test_multiple_rehearsals_all_returned(self, client):
        for i in range(3):
            await client.post("/api/rehearsals", json={"title": f"Session {i}", "slides": []})
        response = await client.get("/api/rehearsals")
        assert response.json()["total"] >= 3


@pytest.mark.asyncio
class TestGetRehearsal:
    async def test_get_existing_rehearsal(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Detail Test", "slides": SLIDES_PAYLOAD})
        rid = create.json()["id"]

        response = await client.get(f"/api/rehearsals/{rid}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == rid
        assert body["title"] == "Detail Test"
        assert len(body["slides"]) == 3

    async def test_slide_data_preserved(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Slide Check", "slides": SLIDES_PAYLOAD})
        rid = create.json()["id"]

        response = await client.get(f"/api/rehearsals/{rid}")
        slides = response.json()["slides"]
        first = next(s for s in slides if s["slide_number"] == 1)
        assert first["title"] == "Intro"
        assert first["content"] == "Welcome everyone."
        assert first["notes"] == "Smile!"

    async def test_get_nonexistent_returns_404(self, client):
        response = await client.get("/api/rehearsals/99999")
        assert response.status_code == 404

    async def test_initial_status_is_pending(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Status", "slides": []})
        rid = create.json()["id"]
        body = (await client.get(f"/api/rehearsals/{rid}")).json()
        assert body["status"] == "pending"

    async def test_audio_path_initially_null(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Audio", "slides": []})
        rid = create.json()["id"]
        body = (await client.get(f"/api/rehearsals/{rid}")).json()
        assert body["audio_path"] is None

    async def test_feedback_initially_null(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Feedback", "slides": []})
        rid = create.json()["id"]
        body = (await client.get(f"/api/rehearsals/{rid}")).json()
        assert body["feedback"] is None


@pytest.mark.asyncio
class TestDeleteRehearsal:
    async def test_delete_existing(self, client):
        create = await client.post("/api/rehearsals", json={"title": "To Delete", "slides": []})
        rid = create.json()["id"]

        delete_response = await client.delete(f"/api/rehearsals/{rid}")
        assert delete_response.status_code == 204

        get_response = await client.get(f"/api/rehearsals/{rid}")
        assert get_response.status_code == 404

    async def test_delete_removes_from_list(self, client):
        create = await client.post("/api/rehearsals", json={"title": "Gone", "slides": []})
        rid = create.json()["id"]
        await client.delete(f"/api/rehearsals/{rid}")

        list_response = await client.get("/api/rehearsals")
        ids = [r["id"] for r in list_response.json()["rehearsals"]]
        assert rid not in ids

    async def test_delete_nonexistent_returns_404(self, client):
        response = await client.delete("/api/rehearsals/99999")
        assert response.status_code == 404
