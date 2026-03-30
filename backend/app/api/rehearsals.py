import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.rehearsal import Rehearsal, Slide
from app.schemas.rehearsal import (
    CreateRehearsalRequest,
    RehearsalResponse,
    RehearsalDetailResponse,
    RehearsalListResponse,
    SlideData,
)

router = APIRouter(prefix="/api/rehearsals", tags=["rehearsals"])


@router.post("", response_model=RehearsalResponse)
async def create_rehearsal(body: CreateRehearsalRequest, db: AsyncSession = Depends(get_db)):
    rehearsal = Rehearsal(title=body.title)
    db.add(rehearsal)
    await db.flush()

    for slide_data in body.slides:
        slide = Slide(
            rehearsal_id=rehearsal.id,
            slide_number=slide_data.slide_number,
            title=slide_data.title,
            content=slide_data.content,
            notes=slide_data.notes,
        )
        db.add(slide)

    await db.commit()
    await db.refresh(rehearsal)

    return RehearsalResponse(
        id=rehearsal.id,
        title=rehearsal.title,
        status=rehearsal.status,
        created_at=rehearsal.created_at,
        slide_count=len(body.slides),
    )


@router.get("", response_model=RehearsalListResponse)
async def list_rehearsals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rehearsal).order_by(Rehearsal.created_at.desc()))
    rehearsals = result.scalars().all()

    items = []
    for r in rehearsals:
        slides_result = await db.execute(select(Slide).where(Slide.rehearsal_id == r.id))
        slide_count = len(slides_result.scalars().all())
        items.append(RehearsalResponse(
            id=r.id,
            title=r.title,
            status=r.status,
            created_at=r.created_at,
            slide_count=slide_count,
        ))

    return RehearsalListResponse(rehearsals=items, total=len(items))


@router.get("/{rehearsal_id}", response_model=RehearsalDetailResponse)
async def get_rehearsal(rehearsal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")

    slides_result = await db.execute(
        select(Slide).where(Slide.rehearsal_id == rehearsal_id).order_by(Slide.slide_number)
    )
    slides = slides_result.scalars().all()

    return RehearsalDetailResponse(
        id=rehearsal.id,
        title=rehearsal.title,
        status=rehearsal.status,
        created_at=rehearsal.created_at,
        updated_at=rehearsal.updated_at,
        audio_path=rehearsal.audio_path,
        transcript=rehearsal.transcript,
        feedback=rehearsal.feedback,
        error_message=rehearsal.error_message,
        slides=[SlideData(
            slide_number=s.slide_number,
            title=s.title,
            content=s.content,
            notes=s.notes,
        ) for s in slides],
    )


@router.delete("/{rehearsal_id}", status_code=204)
async def delete_rehearsal(rehearsal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rehearsal).where(Rehearsal.id == rehearsal_id))
    rehearsal = result.scalar_one_or_none()
    if not rehearsal:
        raise HTTPException(status_code=404, detail="Rehearsal not found")
    await db.delete(rehearsal)
    await db.commit()
