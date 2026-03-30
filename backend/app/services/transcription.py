import asyncio
from pathlib import Path
from app.core.config import settings

_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _whisper_model


def _convert_to_wav(input_path: Path) -> Path:
    """Convert audio file to WAV using pydub."""
    from pydub import AudioSegment
    wav_path = input_path.with_suffix(".wav")
    audio = AudioSegment.from_file(str(input_path))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(wav_path), format="wav")
    return wav_path


def _transcribe_sync(audio_path: Path) -> dict:
    """Run faster-whisper transcription synchronously."""
    # Convert to WAV if not already
    if audio_path.suffix.lower() not in (".wav",):
        wav_path = _convert_to_wav(audio_path)
    else:
        wav_path = audio_path

    model = _get_whisper_model()
    segments, info = model.transcribe(str(wav_path), beam_size=5)

    segment_list = []
    full_text_parts = []
    for seg in segments:
        segment_list.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())

    # Cleanup converted file if we created it
    if wav_path != audio_path and wav_path.exists():
        wav_path.unlink()

    return {
        "text": " ".join(full_text_parts),
        "segments": segment_list,
        "duration": info.duration,
        "language": info.language,
    }


async def transcribe_audio(audio_path: Path) -> dict:
    """Async wrapper for transcription."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_path)
