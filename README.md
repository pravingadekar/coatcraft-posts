# coatcraft-posts

Public media + tooling for **CoatCraft Solutions** (Pune, pan-India epoxy & PU flooring) social posts:
Instagram, Facebook, YouTube Shorts and Google Business Profile, scheduled via Metricool.

- `brand/` logo, icon, fonts, `facts.json` (the only claims posts may make; refresh with `tools/sync_facts.py`)
- `ad/ad.json` the brand ad reel spec; `ad/v1/`, `ad/v2/` rendered scenes + reel
- `AGENT.md` the daily routine, `pillars.md` topics per weekday, `history.md` topics used, `daily/<date>/` posts
- `tools/make_scenes.py` scenes/carousel renderer, `make_reel.py` reel builder (zoom, crossfades, voice + music),
  `make_music.py` original background track, `tts.py` ElevenLabs voice (`ELEVENLABS_API_KEY`; optional `COATCRAFT_VOICE_ID`, default Rudra)

```
pip install pillow imageio-ffmpeg
python tools/make_scenes.py ad/ad.json ad/v1            # reel (add --no-voice without a key)
python tools/make_scenes.py daily/<date>/content.json daily/<date> --carousel
```

Public URL format: `https://raw.githubusercontent.com/pravingadekar/coatcraft-posts/main/<path>`
