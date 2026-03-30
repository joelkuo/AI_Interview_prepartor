"""
Unit tests for ORM model helpers (property accessors, enum values).
No database I/O — pure Python object tests.
"""
import json
from app.models.rehearsal import Rehearsal, Slide, AnalysisStatus


class TestAnalysisStatus:
    def test_all_expected_values_exist(self):
        expected = {"pending", "transcribing", "analyzing_slides", "analyzing_speech",
                    "analyzing_alignment", "generating_summary", "complete", "failed"}
        actual = {s.value for s in AnalysisStatus}
        assert expected == actual

    def test_is_string_subclass(self):
        assert isinstance(AnalysisStatus.complete, str)
        assert AnalysisStatus.complete == "complete"


class TestRehearsalFeedbackProperty:
    def test_returns_none_when_no_json(self):
        r = Rehearsal()
        r.feedback_json = None
        assert r.feedback is None

    def test_deserializes_feedback_json(self):
        data = {"overall_score": 80, "slides": []}
        r = Rehearsal()
        r.feedback_json = json.dumps(data)
        assert r.feedback == data

    def test_feedback_is_dict(self):
        r = Rehearsal()
        r.feedback_json = '{"key": "value"}'
        assert isinstance(r.feedback, dict)


class TestSlideFeedbackProperty:
    def test_returns_none_when_no_json(self):
        s = Slide()
        s.feedback_json = None
        assert s.feedback is None

    def test_deserializes_feedback_json(self):
        data = {"score": 75, "issues": ["Too dense"]}
        s = Slide()
        s.feedback_json = json.dumps(data)
        assert s.feedback["score"] == 75
        assert s.feedback["issues"] == ["Too dense"]
