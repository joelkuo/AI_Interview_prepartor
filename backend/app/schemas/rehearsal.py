from datetime import datetime
from typing import Any
from pydantic import BaseModel


class SlideData(BaseModel):
    slide_number: int
    title: str = ""
    content: str = ""
    notes: str = ""


class CreateRehearsalRequest(BaseModel):
    title: str = "Untitled Presentation"
    slides: list[SlideData]


class RehearsalResponse(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    slide_count: int

    model_config = {"from_attributes": True}


class RehearsalDetailResponse(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    audio_path: str | None
    transcript: str | None
    feedback: dict[str, Any] | None
    error_message: str | None
    slides: list[SlideData]

    model_config = {"from_attributes": True}


class RehearsalListResponse(BaseModel):
    rehearsals: list[RehearsalResponse]
    total: int
