import os
from pathlib import Path

import whisperx
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline


# --------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

AUDIO_FILE = (
    Path(__file__).resolve().parents[2]
    / "uploads"
    / "ES2002a.Mix-Headset.wav"
)

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
WHISPER_MODEL = "tiny.en"


# --------------------------------------------------
# CHECK FILE
# --------------------------------------------------

if not AUDIO_FILE.exists():
    raise FileNotFoundError(
        f"Audio file not found:\n{AUDIO_FILE}"
    )


# --------------------------------------------------
# CHECK HUGGING FACE TOKEN
# --------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN was not found in the environment."
    )


print("=" * 70)
print("MEETMIND AI - WHISPERX DIARIZATION TEST")
print("=" * 70)

print("\nAudio file:")
print(AUDIO_FILE)

print("\nDevice:", DEVICE)
print("Compute type:", COMPUTE_TYPE)
print("Whisper model:", WHISPER_MODEL)

print("\nHugging Face token loaded:", bool(HF_TOKEN))


# --------------------------------------------------
# LOAD AUDIO
# --------------------------------------------------

print("\nLoading audio...")

audio = whisperx.load_audio(
    str(AUDIO_FILE)
)

print("Audio loaded successfully.")


# --------------------------------------------------
# LOAD WHISPERX ASR MODEL
# --------------------------------------------------

print("\nLoading WhisperX transcription model...")
print("This may take some time the first time.")

model = whisperx.load_model(
    WHISPER_MODEL,
    DEVICE,
    compute_type=COMPUTE_TYPE
)

print("WhisperX model loaded.")


# --------------------------------------------------
# TRANSCRIBE
# --------------------------------------------------

print("\nStarting transcription...")

result = model.transcribe(
    audio,
    batch_size=4,
    language="en"
)

print("Transcription completed.")


# --------------------------------------------------
# DISPLAY RAW TRANSCRIPTION
# --------------------------------------------------

print("\n")
print("=" * 70)
print("INITIAL TRANSCRIPT")
print("=" * 70)

for segment in result["segments"]:

    start = segment["start"]
    end = segment["end"]
    text = segment["text"].strip()

    print(
        f"[{start:7.2f}s - {end:7.2f}s] {text}"
    )


# --------------------------------------------------
# LOAD DIARIZATION MODEL
# --------------------------------------------------

print("\n")
print("=" * 70)
print("LOADING SPEAKER DIARIZATION MODEL")
print("=" * 70)

print(
    "Model: pyannote/speaker-diarization-community-1"
)

diarize_model = DiarizationPipeline(
    token=HF_TOKEN,
    device=DEVICE
)

print("Diarization model loaded.")


# --------------------------------------------------
# RUN DIARIZATION
# --------------------------------------------------

print("\nStarting speaker diarization...")

diarize_segments = diarize_model(
    audio,
    min_speakers=2,
    max_speakers=8
)

print("Speaker diarization completed.")


# --------------------------------------------------
# ASSIGN SPEAKERS TO TRANSCRIPT
# --------------------------------------------------

print("\nAssigning speakers to transcript...")

result = whisperx.assign_word_speakers(
    diarize_segments,
    result
)

print("Speaker assignment completed.")


# --------------------------------------------------
# DISPLAY SPEAKER-LABELED TRANSCRIPT
# --------------------------------------------------

print("\n")
print("=" * 70)
print("SPEAKER-LABELED TRANSCRIPT")
print("=" * 70)

detected_speakers = set()

for segment in result["segments"]:

    start = segment["start"]
    end = segment["end"]

    text = segment["text"].strip()

    speaker = segment.get(
        "speaker",
        "UNKNOWN"
    )

    detected_speakers.add(speaker)

    print(
        f"[{start:7.2f}s - {end:7.2f}s] "
        f"{speaker}: {text}"
    )


# --------------------------------------------------
# SPEAKER SUMMARY
# --------------------------------------------------

print("\n")
print("=" * 70)
print("DIARIZATION RESULT")
print("=" * 70)

valid_speakers = sorted(
    speaker
    for speaker in detected_speakers
    if speaker != "UNKNOWN"
)

print(
    "\nDetected speaker labels:"
)

for speaker in valid_speakers:
    print(
        f"  - {speaker}"
    )

print(
    f"\nTotal detected speakers: "
    f"{len(valid_speakers)}"
)

print("\n")
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)