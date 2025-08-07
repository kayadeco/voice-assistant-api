from whisper_utils import transcribe_audio
from gpt_utils import get_gpt_response
from elevenlabs_utils import synthesize_speech
from flask import Flask, request, send_file, Response, render_template
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import os
import tempfile
import openai

# === In-Memory Conversation Tracker ===
conversation_memory = {}

# === Load env variables ===
load_dotenv()

def get_gpt_response_with_memory(session_id, user_input):
    memory = conversation_memory.get(session_id, [])

    memory.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Decotales' helpful voice assistant. You give polite, smart replies to interior queries."},
            *memory
        ]
    )

    reply = response['choices'][0]['message']['content']
    memory.append({"role": "assistant", "content": reply})

    conversation_memory[session_id] = memory
    return reply

# === App Setup ===
app = Flask(__name__)
CORS(app)

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")


# === Route 1: Text-to-Speech (/speak) ===
@app.route('/speak')
def speak():
    text = request.args.get('text')
    if not text:
        return "Missing 'text' parameter", 400

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    if response.status_code != 200:
        return f"Error from ElevenLabs API: {response.text}", 500

    with open("output.mp3", "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return send_file("output.mp3", mimetype="audio/mpeg")


# === Phase 1: Voice-to-Text Only (/listen) ===
@app.route('/listen', methods=['POST'])
def listen():
    audio_file = request.files.get('audio')
    if not audio_file:
        return "Missing audio file", 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    transcript = transcribe_audio(audio_path)
    return {"transcript": transcript}


# === Phase 2: Full Voice Interaction (/chat) ===
@app.route('/chat', methods=['POST'])
def chat():
    audio_file = request.files.get('audio')
    session_id = request.form.get('session_id', 'default_user')  # fallback if not provided

    if not audio_file:
        return "Missing audio file", 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    transcript = transcribe_audio(audio_path)
    reply = get_gpt_response_with_memory(session_id, transcript)
    output_path = synthesize_speech(reply)

    return send_file(output_path, mimetype="audio/mpeg")

# === Phase 3: Streamed Voice Output (/voicechat-stream) ===
@app.route('/voicechat-stream', methods=['POST'])
def voicechat_stream():
    if 'audio' not in request.files:
        return "Missing audio file", 400

    audio_file = request.files['audio']
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio_file.save(tmp.name)
        temp_audio_path = tmp.name

    with open(temp_audio_path, "rb") as file:
        transcript = openai.Audio.transcribe("whisper-1", file)
    user_text = transcript["text"]

    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful AI voice assistant."},
            {"role": "user", "content": user_text}
        ]
    )
    gpt_reply = gpt_response['choices'][0]['message']['content']

    def generate_audio():
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY
        }
        data = {
            "text": gpt_reply,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }

        with requests.post(url, headers=headers, json=data, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

    return Response(generate_audio(), mimetype="audio/mpeg")


# === Phase 4: UI (optional) ===
@app.route('/interface')
def interface():
    return render_template('index.html')


# === Home ===
@app.route('/')
def home():
    return "Welcome to Kaya Voice API – use /speak, /chat, /listen or /interface."


# === Run Server ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
