import os
from pathlib import Path

import whisperx
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline


load_dotenv()


# ------------------------------------------------------------
# WhisperX configuration
# ------------------------------------------------------------

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
MODEL_NAME = "base.en"


# ------------------------------------------------------------
# Hugging Face token
# ------------------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN")


if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN was not found in the environment."
    )


# ------------------------------------------------------------
# Load WhisperX model once when the application starts
# ------------------------------------------------------------

print("Loading WhisperX transcription model...")

whisper_model = whisperx.load_model(
    MODEL_NAME,
    DEVICE,
    compute_type=COMPUTE_TYPE
)

print("WhisperX transcription model loaded.")


# ------------------------------------------------------------
# Load speaker diarization model once
# ------------------------------------------------------------

print("Loading speaker diarization model...")

diarization_model = DiarizationPipeline(
    token=HF_TOKEN,
    device=DEVICE
)

print("Speaker diarization model loaded.")


# ------------------------------------------------------------
# Transcription + speaker diarization
# ------------------------------------------------------------

def transcribe_audio(file_path: str) -> str:

    audio_path = Path(file_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    print(
        f"Starting WhisperX processing: "
        f"{audio_path.name}"
    )

    # --------------------------------------------------------
    # Load audio
    # --------------------------------------------------------

    audio = whisperx.load_audio(
        str(audio_path)
    )

    # --------------------------------------------------------
    # Speech-to-text
    # --------------------------------------------------------

    result = whisper_model.transcribe(
        audio,
        batch_size=4,
        language="en"
    )

    print("WhisperX transcription completed.")

    # --------------------------------------------------------
    # Speaker diarization
    #
    # We intentionally do not force a fixed number of speakers.
    # WhisperX/pyannote will determine the speaker clusters.
    # --------------------------------------------------------

    diarize_segments = diarization_model(
        audio,
        min_speakers=2,
        max_speakers=8
    )

    print("Speaker diarization completed.")

    # --------------------------------------------------------
    # Assign speaker labels to transcript segments
    # --------------------------------------------------------

    result = whisperx.assign_word_speakers(
        diarize_segments,
        result
    )

    print("Speaker assignment completed.")

    # --------------------------------------------------------
    # Build speaker-labelled transcript
    # --------------------------------------------------------

    transcript_lines = []

    for segment in result["segments"]:

        text = segment.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        speaker = segment.get(
            "speaker",
            "UNKNOWN"
        )

        transcript_lines.append(
            f"{speaker}: {text}"
        )

    # --------------------------------------------------------
    # Final transcript
    # --------------------------------------------------------

    transcript = "\n".join(
        transcript_lines
    )

    if not transcript.strip():
        raise RuntimeError(
            "WhisperX produced an empty transcript."
        )

    print(
        "WhisperX processing completed successfully."
    )

    return transcript