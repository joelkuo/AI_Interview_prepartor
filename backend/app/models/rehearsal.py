import json
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    transcribing = "transcribing"
    analyzing_slides = "analyzing_slides"
    analyzing_speech = "analyzing_speech"
    analyzing_alignment = "analyzing_alignment"
    generating_summary = "generating_summary"
    complete = "complete"
    failed = "failed"


class Rehearsal(Base):
    __tablename__ = "rehearsals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="Untitled Presentation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default=AnalysisStatus.pending)
    audio_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    slides: Mapped[list["Slide"]] = relationship("Slide", back_populates="rehearsal", cascade="all, delete-orphan")

    @property
    def feedback(self):
        if self.feedback_json:
            return json.loads(self.feedback_json)
        return None


class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rehearsal_id: Mapped[int] = mapped_column(Integer, ForeignKey("rehearsals.id"), index=True)
    slide_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(1000), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    feedback_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    rehearsal: Mapped["Rehearsal"] = relationship("Rehearsal", back_populates="slides")

    @property
    def feedback(self):
        if self.feedback_json:
            return json.loads(self.feedback_json)
        return None
