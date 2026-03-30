"""
Shared fixtures for the entire test suite.

Uses an in-memory SQLite database so tests are fully isolated and require
no filesystem state.  LLM and Whisper calls are always patched at the
module level so tests never hit real external services.
"""
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory database engine (one per test session)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables once before any test runs."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session():
    """Yield a fresh async DB session per test, rolled back afterwards."""
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession):
    """
    HTTP test client wired to the FastAPI app with the test DB injected.
    Each test gets its own isolated DB session.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reusable fake LLM response builders
# ---------------------------------------------------------------------------

FAKE_SLIDE_FEEDBACK = {
    "slide_number": 1,
    "score": 82,
    "strengths": ["Clear title", "Concise bullet points"],
    "issues": ["Missing visual aid"],
    "suggestions": ["Add a chart to illustrate the trend"],
    "summary": "Well-structured slide with minor improvement opportunity.",
}

FAKE_SPEECH_FEEDBACK = {
    "score": 75,
    "wpm": 145.0,
    "filler_word_count": 3,
    "filler_words_detail": {"um": 2, "like": 1},
    "strengths": ["Good pace", "Clear enunciation"],
    "issues": ["Some filler words"],
    "suggestions": ["Pause instead of using filler words"],
    "summary": "Solid delivery with manageable filler word count.",
}

FAKE_ALIGNMENT_FEEDBACK = {
    "score": 70,
    "coverage_percentage": 85,
    "uncovered_points": ["Q4 forecast"],
    "off_topic_segments": [],
    "strengths": ["Covered most key points"],
    "issues": ["Skipped Q4 forecast slide"],
    "suggestions": ["Briefly mention Q4 numbers"],
    "summary": "Good overall alignment with one missed section.",
}

FAKE_OVERALL_FEEDBACK = {
    "overall_score": 76,
    "headline": "Strong presentation with a few areas to polish.",
    "top_strengths": ["Engaging opening", "Clear structure", "Good pace"],
    "top_improvements": ["Reduce filler words", "Add visuals to slide 2"],
    "next_steps": ["Practice the Q4 section", "Record another rehearsal"],
}
