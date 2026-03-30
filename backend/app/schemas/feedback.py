from pydantic import BaseModel


class SlideFeedback(BaseModel):
    slide_number: int
    score: int
    strengths: list[str]
    issues: list[str]
    suggestions: list[str]
    summary: str


class SpeechFeedback(BaseModel):
    score: int
    wpm: float
    filler_word_count: int
    filler_words_detail: dict[str, int]
    strengths: list[str]
    issues: list[str]
    suggestions: list[str]
    summary: str


class AlignmentFeedback(BaseModel):
    score: int
    coverage_percentage: int
    uncovered_points: list[str]
    off_topic_segments: list[str]
    strengths: list[str]
    issues: list[str]
    suggestions: list[str]
    summary: str


class OverallFeedback(BaseModel):
    overall_score: int
    headline: str
    top_strengths: list[str]
    top_improvements: list[str]
    next_steps: list[str]


class AnalysisResult(BaseModel):
    rehearsal_id: int
    status: str
    overall: OverallFeedback | None = None
    slides: list[SlideFeedback] = []
    speech: SpeechFeedback | None = None
    alignment: AlignmentFeedback | None = None
    transcript: str | None = None
