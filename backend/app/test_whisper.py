from whisper_service import transcribe_audio


audio_file = "../../uploads/file_example_WAV_1MG.wav"

transcript = transcribe_audio(audio_file)

print("\nTRANSCRIPT:")
print(transcript)