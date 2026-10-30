# Daily post routine (for the cloud agent)

Brand: **CoatCraft Solutions**: epoxy, PU and decorative flooring, Pune, Pan-India service.
Audience: factory, warehouse and facility owners/managers, architects, and home/showroom owners.
Language: Hinglish (Roman script) on slides and captions; Devanagari for the voiceover.
Every day: 1 carousel (6 slides) + 1 reel (5 scenes, male voice) to Instagram, Facebook and YouTube Shorts,
plus a Google Business Profile update once that network is connected.

## Steps (run once per day, ~8:30 AM IST, before the first slot at 10:00 AM)

1. `D=$(TZ=Asia/Kolkata date +%F)`. If `daily/$D/reel.mp4` already exists, skip to step 6.
2. Today's pillar is set by the weekday in `pillars.md`. Take the first queue item not yet in `history.md`, and
   the next location cluster from `seo.md` after the last `area:` in `history.md`. Append
   `$D | <pillar> | <topic> | area: <cluster>` to `history.md`.
3. Write `daily/$D/carousel.json` and `daily/$D/reel.json` in the shape of `daily/2026-10-31/` (scene kinds and
   fields are documented at the top of `tools/make_scenes.py`):
   - Carousel: exactly 6 scenes. 1 `hook` (question or problem, 2 `chips`, short `body` ending in a swipe cue),
     2-5 one idea each (`list` with 3 items, `grid` with 4-8 items, or `text`), 6 `cta` with a short title.
   - Reel: exactly 5 scenes (`hook`, three content scenes, `cta`) and `"narration"` with exactly 5 lines.
   - Titles under ~40 characters; mark 1-3 key words with `*stars*` (orange). List items under ~35 characters.
     Slide text: plain ASCII only, no emoji and no arrows (Poppins has no glyphs for them).
   - Narration: Devanagari, conversational, 1-2 short sentences per scene (~15-30 words), English trade words
     transliterated (इपॉक्सी, पीयू फ़्लोरिंग, वेयरहाउस), every number spelled as words (दो से पाँच दिन). Same facts as
     the scenes, nothing extra. The last line asks them to call/WhatsApp and says the number exactly as
     "सात सात चार पाँच आठ, आठ नौ एक एक एक", then "कोटक्राफ़्ट सॉल्यूशंस।"
4. Write `daily/$D/captions.md` in the format of `daily/2026-10-31/captions.md`: Instagram carousel, Instagram
   Reel, Facebook, YouTube Short (title under 100 characters, ending in `#shorts`), Google Business Profile
   (plain text under 1,400 characters, no hashtags). Every caption: hook, the key facts, a comment question
   (not on YouTube/GBP), and the contact block: "Call / WhatsApp: +91 77458 89111", "www.coatcraftsolutions.com",
   "Pune | Pan-India service". 6-14 relevant hashtags on Instagram, ~5 on Facebook and YouTube.
   Follow `seo.md` for every caption: keyword-led first line, the day's location cluster in a service-area line,
   the YouTube title formula, description and `tags`, and the longer GBP text. The CTA slide/scene and the
   narration stay as they are (no area names in the voiceover).
5. Render and check:
   ```
   python3 -m pip install -q -r requirements.txt   # if PIL fails with "_imaging": add --force-reinstall
   python3 tools/make_scenes.py daily/$D/carousel.json daily/$D --carousel
   python3 tools/make_scenes.py daily/$D/reel.json daily/$D
   ```
   The reel must print "with voice" (needs `ELEVENLABS_API_KEY` from the environment; never print it). If the
   voice step fails, retry once; if it still fails, add `--no-voice` so the post still goes out, and say so in
   your final message. Open every `slideN.png` and `sceneN.png` and look at them: no text overflowing the frame or
   running into the footer, orange words correct. Fix the JSON and re-render until clean.
   Commit (`Daily $D: <topic>`), `git pull --rebase origin main`, push to `main` (on a rejected push, pull --rebase
   and retry up to 3 times).
6. Confirm `https://raw.githubusercontent.com/pravingadekar/coatcraft-posts/main/daily/$D/slide1.png` and
   `.../reel.mp4` return HTTP 200 (retry for up to 2 minutes after the push).
7. Metricool: use ONLY the "Metricool CoatCraft" connector, brand/blogId `7752681` (label "coatcraftsolutions",
   owner coatcraftsolutions@gmail.com), timezone `Asia/Calcutta`. If getBrandSettings shows any other brand, do
   not post there. Call getScheduledPosts for $D first and do not create a post that already exists. Then create,
   autoPublish true, at these times on `$D` (Metricool best-time data for this brand, Oct 2026):
   | Time  | Post |
   |-------|------|
   | 10:00 | Instagram `REEL` with reel.mp4, `showReelOnFeed: true`, Instagram Reel caption |
   | 10:00 | Facebook `REEL` with reel.mp4, Facebook caption |
   | 11:00 | Google Business Profile (`gmb`, `gmbData.type: "publication"`), GBP text. Only if getBrandSettings shows `gbpData` in the brand's `networksData` (connected 2026-10-30); otherwise skip it |
   | 12:00 | Facebook `POST` with slide1..slide6 URLs, Facebook caption |
   | 16:00 | YouTube `short` with reel.mp4: title, `tags` from captions.md, `madeForKids: false`, `category: SCIENCE_TECHNOLOGY`, `privacy: public` |
   | 18:00 | Instagram `POST` with slide1..slide6 URLs (carousel), Instagram carousel caption |
   If the run is late and a slot has already passed, schedule that post 10 minutes from now instead.
   If createScheduledPost fails with "Failed to normalize media", the file was pushed too recently for Metricool
   to fetch it: wait 90 seconds (`sleep 90`) and retry, up to 5 times, before reporting failure.
   Media URLs: `https://raw.githubusercontent.com/pravingadekar/coatcraft-posts/main/daily/$D/<file>`.
8. Final message: the topic, which posts were scheduled at what time, and anything that failed.

## Content rules (never break)
- Company facts only from `brand/facts.json`: services, industries, thickness, expected life, install time,
  maintenance, warranty, contact details. Write life and warranty as ranges with "up to" and a footnote, as in
  the files ("8-15 saal tak life*", "up to 2 saal warranty*", "*sahi maintenance ke saath").
- General flooring education is fine, but no numbers that are not in facts.json.
- Never invent: project counts, years in business, client names or logos, prices, discounts, offers,
  "free site visit", rankings ("No. 1", "best in Pune"), certifications, testimonials. Do not knock competitors.
- Photos from `photos/` only, described only as `photos/notes.md` says; never show client names or faces.
- Do not touch any other repository.
