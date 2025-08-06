# elevenlabs_utils.py
import os
from elevenlabs import Voice, VoiceSettings, generate, save

def generate_speech(text, voice_id):
    audio = generate(
        text=text,
        voice=Voice(
            voice_id=voice_id,
            settings=VoiceSettings(stability=0.75, similarity_boost=0.75)
        )
    )
    save(audio, "output.mp3")
