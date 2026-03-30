SLIDE_ANALYSIS_PROMPT = """You are an expert presentation coach. Analyze the following slide content and provide structured feedback.

Slide {slide_number} of {total_slides}:
Title: {title}
Content: {content}
Speaker Notes: {notes}

Evaluate:
1. Clarity - Is the message clear and concise?
2. Content density - Is there too much or too little content?
3. Structure - Is the information well-organized?
4. Engagement - Will this slide engage the audience?

Return a JSON object with this exact structure:
{{
  "slide_number": {slide_number},
  "score": <0-100 integer>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "issues": ["<issue 1>", "<issue 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"],
  "summary": "<one sentence summary>"
}}"""

SPEECH_ANALYSIS_PROMPT = """You are an expert presentation speech coach. Analyze this speech transcript and provide feedback.

Transcript:
{transcript}

Speaking stats:
- Duration: {duration_seconds:.0f} seconds
- Word count: {word_count}
- WPM: {wpm:.0f}
- Filler words detected: {filler_words}

Evaluate:
1. Pace - Is the speaking rate appropriate (120-160 WPM ideal)?
2. Filler words - Are there too many filler words?
3. Clarity - Is the language clear and precise?
4. Engagement - Does the speech sound engaging?

Return a JSON object:
{{
  "score": <0-100 integer>,
  "wpm": {wpm:.0f},
  "filler_word_count": <integer>,
  "filler_words_detail": {{"um": <count>, "uh": <count>, "like": <count>, "you know": <count>}},
  "strengths": ["<strength 1>", "<strength 2>"],
  "issues": ["<issue 1>", "<issue 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"],
  "summary": "<one sentence summary>"
}}"""

ALIGNMENT_ANALYSIS_PROMPT = """You are an expert presentation coach analyzing how well a speaker's speech aligns with their slide content.

Slide Content Summary:
{slides_summary}

Speech Transcript:
{transcript}

Evaluate:
1. Coverage - Did the speaker cover all key slide points?
2. Deviation - Did the speaker go off-topic or skip important points?
3. Balance - Was appropriate time spent on each section?
4. Coherence - Did the narrative flow match the slide progression?

Return a JSON object:
{{
  "score": <0-100 integer>,
  "coverage_percentage": <0-100 integer>,
  "uncovered_points": ["<point 1>", "<point 2>"],
  "off_topic_segments": ["<segment 1>"],
  "strengths": ["<strength 1>", "<strength 2>"],
  "issues": ["<issue 1>", "<issue 2>"],
  "suggestions": ["<suggestion 1>", "<suggestion 2>"],
  "summary": "<one sentence summary>"
}}"""

OVERALL_FEEDBACK_PROMPT = """You are an expert presentation coach providing overall feedback based on these analysis results.

Slide Analysis Score: {slide_score}/100
Speech Analysis Score: {speech_score}/100
Alignment Analysis Score: {alignment_score}/100

Key Issues Found:
{all_issues}

Generate an encouraging but honest overall assessment.

Return a JSON object:
{{
  "overall_score": <weighted average 0-100>,
  "headline": "<one impactful headline summary>",
  "top_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "top_improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
  "next_steps": ["<action 1>", "<action 2>"]
}}"""
