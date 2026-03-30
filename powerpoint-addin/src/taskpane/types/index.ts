export interface SlideData {
  slide_number: number;
  title: string;
  content: string;
  notes: string;
}

export interface RehearsalResponse {
  id: number;
  title: string;
  status: AnalysisStatus;
  created_at: string;
  slide_count: number;
}

export type AnalysisStatus =
  | "pending"
  | "transcribing"
  | "analyzing_slides"
  | "analyzing_speech"
  | "analyzing_alignment"
  | "generating_summary"
  | "complete"
  | "failed";

export interface SlideFeedback {
  slide_number: number;
  score: number;
  strengths: string[];
  issues: string[];
  suggestions: string[];
  summary: string;
}

export interface SpeechFeedback {
  score: number;
  wpm: number;
  filler_word_count: number;
  filler_words_detail: Record<string, number>;
  strengths: string[];
  issues: string[];
  suggestions: string[];
  summary: string;
}

export interface AlignmentFeedback {
  score: number;
  coverage_percentage: number;
  uncovered_points: string[];
  off_topic_segments: string[];
  strengths: string[];
  issues: string[];
  suggestions: string[];
  summary: string;
}

export interface OverallFeedback {
  overall_score: number;
  headline: string;
  top_strengths: string[];
  top_improvements: string[];
  next_steps: string[];
}

export interface AnalysisResult {
  rehearsal_id: number;
  status: AnalysisStatus;
  overall?: OverallFeedback;
  slides: SlideFeedback[];
  speech?: SpeechFeedback;
  alignment?: AlignmentFeedback;
  transcript?: string;
}

export type ActiveTab = "sync" | "record" | "results" | "history";
