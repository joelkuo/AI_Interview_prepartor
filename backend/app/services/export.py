from datetime import datetime


def feedback_to_markdown(rehearsal_id: int, title: str, feedback: dict, transcript: str | None = None) -> str:
    lines = [f"# Presentation Coaching Feedback", f"", f"**Presentation:** {title}",
             f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
             f"**Rehearsal ID:** {rehearsal_id}", ""]

    overall = feedback.get("overall", {})
    if overall:
        score = overall.get("overall_score", "N/A")
        lines += [f"## Overall Score: {score}/100", "", f"_{overall.get('headline', '')}_", ""]

        strengths = overall.get("top_strengths", [])
        if strengths:
            lines += ["### Top Strengths", ""]
            for s in strengths:
                lines.append(f"- {s}")
            lines.append("")

        improvements = overall.get("top_improvements", [])
        if improvements:
            lines += ["### Areas for Improvement", ""]
            for i in improvements:
                lines.append(f"- {i}")
            lines.append("")

        next_steps = overall.get("next_steps", [])
        if next_steps:
            lines += ["### Next Steps", ""]
            for n in next_steps:
                lines.append(f"- {n}")
            lines.append("")

    speech = feedback.get("speech", {})
    if speech:
        lines += [f"## Speech Analysis (Score: {speech.get('score', 'N/A')}/100)", ""]
        lines.append(f"- **WPM:** {speech.get('wpm', 'N/A')}")
        lines.append(f"- **Filler words:** {speech.get('filler_word_count', 0)}")
        lines.append(f"- {speech.get('summary', '')}")
        lines.append("")

    slide_feedbacks = feedback.get("slides", [])
    if slide_feedbacks:
        lines += ["## Slide-by-Slide Feedback", ""]
        for sf in sorted(slide_feedbacks, key=lambda x: x.get("score", 100)):
            lines.append(f"### Slide {sf.get('slide_number')} — Score: {sf.get('score', 'N/A')}/100")
            lines.append(f"_{sf.get('summary', '')}_")
            issues = sf.get("issues", [])
            if issues:
                lines.append("")
                lines.append("**Issues:**")
                for i in issues:
                    lines.append(f"- {i}")
            suggestions = sf.get("suggestions", [])
            if suggestions:
                lines.append("")
                lines.append("**Suggestions:**")
                for s in suggestions:
                    lines.append(f"- {s}")
            lines.append("")

    if transcript:
        lines += ["## Transcript", "", transcript, ""]

    return "\n".join(lines)
