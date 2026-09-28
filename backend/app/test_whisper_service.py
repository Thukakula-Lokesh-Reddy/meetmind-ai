from whisper_service import transcribe_audio


AUDIO_FILE = (
    r"C:\Users\LOKESH REDDY\OneDrive - Alliance University"
    r"\Desktop\AI MEETING TRACKER"
    r"\uploads\Eg_Meeting.mp4"
)


print("=" * 70)
print("MEETMIND AI - WHISPER SERVICE TEST")
print("=" * 70)

print("\nAudio:")
print(AUDIO_FILE)

print("\nStarting transcription...\n")

transcript = transcribe_audio(
    AUDIO_FILE
)

print("\n")
print("=" * 70)
print("SPEAKER-LABELLED TRANSCRIPT")
print("=" * 70)

print(transcript)

print("\n")
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)