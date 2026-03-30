import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.models.rehearsal import Rehearsal, Slide, AnalysisStatus
from app.schemas.feedback import AnalysisResult
from app.services import transcription, speech_analyzer, slide_analyzer, alignment_analyzer
from app.services.llm_client import call_llm, extract_json
from app.services.export import feedback_to_markdown
from app.core.prompts import OVERALL_FEEDBACK_PROMPT

router = APIRouter(prefix="/api/rehearsals", tags=["analysis"])


async def _update_status(rehearsal_id: int, status: str, error: str | None = None):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
        r = result.scalar_one_or_none()
        if r:
            r.status = status
            if error:
                r.error_message = error
            await db.commit()


async def _run_analysis(rehearsal_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
        rehearsal = result.scalar_one_or_none()
        if not rehearsal:
            return

        slides_result = await db.execute(
            select(Slide).where(Slide.rehearsal_id == rehearsal_id).order_by(Slide.slide_number)
        )
        slides = slides_result.scalars().all()
        slides_data = [{"slide_number": s.slide_number, "title": s.title, "content": s.content, "notes": s.notes}
                       for s in slides]

    try:
        # Step 1: Transcription
        await _update_status(rehearsal_id, AnalysisStatus.transcribing)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
            rehearsal = result.scalar_one()

        if not rehearsal.audio_path:
            raise ValueError("No audio uploaded for this rehearsal")

        audio_path = Path(rehearsal.audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        transcript_data = await transcription.transcribe_audio(audio_path)
        transcript_text = transcript_data.get("text", "")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
            r = result.scalar_one()
            r.transcript = transcript_text
            await db.commit()

        # Step 2: Slide analysis
        await _update_status(rehearsal_id, AnalysisStatus.analyzing_slides)
        slide_results = await slide_analyzer.analyze_all_slides(slides_data)

        async with AsyncSessionLocal() as db:
            for slide_result in slide_results:
                slide_num = slide_result.get("slide_number")
                result = await db.execute(
                    select(Slide).where(Slide.rehearsal_id == rehearsal_id, Slide.slide_number == slide_num)
                )
                slide_obj = result.scalar_one_or_none()
                if slide_obj:
                    slide_obj.feedback_json = json.dumps(slide_result)
            await db.commit()

        # Step 3: Speech analysis
        await _update_status(rehearsal_id, AnalysisStatus.analyzing_speech)
        speech_result = await speech_analyzer.analyze_speech(transcript_data)

        # Step 4: Alignment analysis
        await _update_status(rehearsal_id, AnalysisStatus.analyzing_alignment)
        alignment_result = await alignment_analyzer.analyze_alignment(slides_data, transcript_data)

        # Step 5: Overall summary
        await _update_status(rehearsal_id, AnalysisStatus.generating_summary)
        slide_score = round(sum(s.get("score", 0) for s in slide_results) / max(len(slide_results), 1))
        all_issues = []
        for s in slide_results:
            all_issues.extend(s.get("issues", []))
        all_issues.extend(speech_result.get("issues", []))
        all_issues.extend(alignment_result.get("issues", []))

        overall_prompt = OVERALL_FEEDBACK_PROMPT.format(
            slide_score=slide_score,
            speech_score=speech_result.get("score", 0),
            alignment_score=alignment_result.get("score", 0),
            all_issues="\n".join(f"- {i}" for i in all_issues[:15]),
        )
        overall_raw = await call_llm(overall_prompt, task="default")
        overall_result = extract_json(overall_raw)

        # Store full feedback
        full_feedback = {
            "overall": overall_result,
            "speech": speech_result,
            "alignment": alignment_result,
            "slides": slide_results,
        }

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
            r = result.scalar_one()
            r.feedback_json = json.dumps(full_feedback)
            r.status = AnalysisStatus.complete
            await db.commit()

    except Exception as e:
        await _update_status(rehearsal_id, AnalysisStatus.failed, str(e))
        raise


@router.post("/{rehearsal_id}/analyze", status_code=202)
async def start_analysis(
    rehearsal_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")

    if rehearsal.status in (AnalysisStatus.transcribing, AnalysisStatus.analyzing_slides,
                             AnalysisStatus.analyzing_speech, AnalysisStatus.analyzing_alignment,
                             AnalysisStatus.generating_summary):
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    background_tasks.add_task(_run_analysis, rehearsal_id)
    return {"rehearsal_id": rehearsal_id, "status": "accepted", "message": "Analysis started"}


@router.get("/{rehearsal_id}/results", response_model=AnalysisResult)
async def get_results(rehearsal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")

    feedback = rehearsal.feedback or {}
    return AnalysisResult(
        rehearsal_id=rehearsal_id,
        status=rehearsal.status,
        overall=feedback.get("overall"),
        slides=feedback.get("slides", []),
        speech=feedback.get("speech"),
        alignment=feedback.get("alignment"),
        transcript=rehearsal.transcript,
    )


@router.get("/{rehearsal_id}/export", response_class=PlainTextResponse)
async def export_feedback(rehearsal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")
    if rehearsal.status != AnalysisStatus.complete:
        raise HTTPException(status_code=400, detail="Analysis not complete yet")

    md = feedback_to_markdown(rehearsal_id, rehearsal.title, rehearsal.feedback or {}, rehearsal.transcript)
    return PlainTextResponse(content=md, media_type="text/markdown")
