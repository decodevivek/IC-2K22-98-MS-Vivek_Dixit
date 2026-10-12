import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    raise ValueError("ELEVENLABS_API_KEY not found in .env file")

client = ElevenLabs(api_key=api_key)

text = input("Enter text to convert to speech:\n> ")

audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # George (default voice)
    model_id="eleven_multilingual_v2",
    text=text
)

with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("✅ Speech generated successfully!")
print("Saved as: output.mp3")