"""
Unit tests for app.services.export.feedback_to_markdown

Pure function — no mocking required.
"""
from app.services.export import feedback_to_markdown

FULL_FEEDBACK = {
    "overall": {
        "overall_score": 76,
        "headline": "Strong presentation with room to improve.",
        "top_strengths": ["Engaging opening", "Clear structure"],
        "top_improvements": ["Reduce filler words", "Add visuals"],
        "next_steps": ["Practice once more", "Record again"],
    },
    "speech": {
        "score": 75,
        "wpm": 142.0,
        "filler_word_count": 5,
        "summary": "Good pace, watch the filler words.",
    },
    "slides": [
        {
            "slide_number": 2,
            "score": 55,
            "summary": "Too much text.",
            "issues": ["Wall of text"],
            "suggestions": ["Split into two slides"],
        },
        {
            "slide_number": 1,
            "score": 88,
            "summary": "Great opener.",
            "issues": [],
            "suggestions": [],
        },
    ],
}


class TestFeedbackToMarkdown:
    def test_includes_title_and_id(self):
        md = feedback_to_markdown(42, "My Deck", FULL_FEEDBACK)
        assert "My Deck" in md
        assert "42" in md

    def test_overall_score_present(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "76" in md
        assert "Strong presentation with room to improve." in md

    def test_strengths_section(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "Engaging opening" in md
        assert "Clear structure" in md

    def test_improvements_section(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "Reduce filler words" in md
        assert "Add visuals" in md

    def test_next_steps_section(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "Practice once more" in md

    def test_speech_section(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "Speech Analysis" in md
        assert "142" in md  # WPM
        assert "5" in md    # filler count

    def test_slides_sorted_worst_first(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        # Slide 2 (score 55) should appear before Slide 1 (score 88)
        pos_slide2 = md.index("Slide 2")
        pos_slide1 = md.index("Slide 1")
        assert pos_slide2 < pos_slide1

    def test_slide_issues_and_suggestions_present(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert "Wall of text" in md
        assert "Split into two slides" in md

    def test_transcript_appended_when_provided(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK, transcript="Hello world this is a test.")
        assert "Transcript" in md
        assert "Hello world this is a test." in md

    def test_no_transcript_section_when_none(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK, transcript=None)
        assert "## Transcript" not in md

    def test_empty_feedback_does_not_crash(self):
        md = feedback_to_markdown(1, "Empty", {})
        assert "Empty" in md
        assert isinstance(md, str)

    def test_returns_string(self):
        md = feedback_to_markdown(1, "T", FULL_FEEDBACK)
        assert isinstance(md, str)
        assert len(md) > 100

    def test_markdown_heading_structure(self):
        md = feedback_to_markdown(1, "Test", FULL_FEEDBACK)
        assert md.startswith("# Presentation Coaching Feedback")
        assert "## Overall Score" in md
        assert "## Speech Analysis" in md
        assert "## Slide-by-Slide Feedback" in md
