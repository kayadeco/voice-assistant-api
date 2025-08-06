from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVEN_API_KEY")
)

def synthesize_speech(text, voice_id="Oq0cIHWGcnbOGozOQv0t"):  # replace with your voice ID
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="mp3_44100_128"
    )
    return audio
