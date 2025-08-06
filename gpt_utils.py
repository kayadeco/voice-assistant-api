import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt_response(transcript):
    prompt = f"You heard: {transcript}. Give a helpful reply."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful voice assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message["content"]
