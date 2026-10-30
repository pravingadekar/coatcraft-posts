"""ElevenLabs text-to-speech: one MP3 per line of narration.

Needs ELEVENLABS_API_KEY in the environment; never hard-code the key. COATCRAFT_VOICE_ID overrides the default
male voice (Rudra).
"""
import json
import os
import urllib.request

MODEL = "eleven_multilingual_v2"
DEFAULT_VOICE = "gMRjEAcWCvjoyqIfZqlp"  # Rudra; a voice ID is not a secret


def available():
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def speak(text, out_path):
    voice = os.environ.get("COATCRAFT_VOICE_ID") or DEFAULT_VOICE
    body = json.dumps({
        "text": text,
        "model_id": MODEL,
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp, open(out_path, "wb") as f:
        f.write(resp.read())


def speak_all(lines, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, line in enumerate(lines, start=1):
        path = os.path.join(out_dir, f"voice{i}.mp3")
        speak(line, path)
        paths.append(path)
    return paths
