# AI story ad: "Floor ki problem → CoatCraft solution" (v1)

Dramatized scene with AI-generated visuals (Gemini Omni Flash with reference images in refs/, 9:16, ~10 s per shot; built by build.py). No real client, no real company names.
Spoken facts only from brand/facts.json. On-screen disclosure in the edit: "Dramatized scene · AI-generated visuals".

## Characters (paste this block into every prompt where they appear, word for word)
- **OWNER**: Indian man, about 45, medium-brown skin, short black hair greying at the temples, neat moustache,
  light-blue full-sleeve formal shirt, dark trousers, white safety helmet, slightly heavy build, speaks Hindi.
- **ENGINEER**: Indian man, about 35, wheatish skin, short black hair, trimmed beard, white safety helmet,
  bright orange high-visibility safety jacket over a navy polo shirt, holds a tablet, calm and confident,
  speaks Hindi.
- **SETTING**: a large Indian manufacturing plant in Maharashtra (MIDC), steel roof trusses, daylight from high
  windows, yellow forklift, metal racks; realistic, documentary style, natural colours.

Every prompt ends with: "Photorealistic, shot on a cinema camera, natural lighting, realistic skin and hands,
vertical 9:16. No on-screen text, no subtitles, no logos, no brand names."

## Shots

**1. Problem (8 s)**
Medium shot. [SETTING] The concrete floor is badly cracked, with potholes and grey dust; a yellow forklift rolls past
and kicks up dust. [OWNER] stands in the dust, points at the cracks, frustrated, and says in Hindi:
"Har mahine floor toot jaata hai... dhool se machines bhi kharab ho rahi hain."
Ambient factory noise, forklift beeping.

**2. Inspection (8 s)**
Low angle close-up. [ENGINEER] crouches beside a deep crack, runs his gloved finger along it, looks up at the owner
and says in Hindi: "Sir, forklift ka load heavy hai, isliye ye normal floor tik nahi raha."
[OWNER] partly visible standing behind him. Same cracked floor and dust as before.

**3. The question (8 s)**
Two-shot, both standing on the cracked floor. [OWNER] asks in Hindi: "To solution kya hai? Aur kaam kitne din band
rahega?" [ENGINEER] shows the tablet and answers in Hindi: "Industrial Epoxy ya PU Concrete. Area ke hisaab se do se
paanch din mein ready."

**4. The work (8 s, no dialogue)**
Montage-style continuous shot in the same plant: workers in orange safety jackets and helmets grind the floor with a
diamond grinder, then pour and spread a grey self-levelling epoxy coating with a pin roller and a squeegee; glossy wet
surface. Sounds of grinder and rolling.

**5. The result (8 s)**
Wide shot. The same plant now has a seamless, glossy light-grey epoxy floor with yellow walkway lines, clean and
reflective; the yellow forklift glides smoothly. [OWNER] walks in, looks down at his reflection, smiles, and says in
Hindi: "Ab floor seamless hai... aur safai bhi bilkul aasaan."

**6. Call to action (8 s)**
Medium close-up on the new glossy floor. [ENGINEER] looks into the camera, friendly, and says in Hindi:
"Apne floor ki problem batayein... CoatCraft Solutions."

**7. End card (4 s, made in the edit)**
`tools/make_scenes.py` kind `cta`: "Apne floor ka *free consult*" is NOT allowed (no offers). Use
"Apne floor ka *solution* paayein" + phone, website, "Pune | Pan-India service".

## Edit
Order 1-6 + end card, 0.3 s cuts or short crossfades, original music ducked under the dialogue, CoatCraft logo bug
top-left, lower third on shot 2: "CoatCraft Solutions · Site Engineer", disclosure line bottom (small, all shots).
Exports: `ad/ai-story/v1/reel.mp4` (9:16) and `reel_16x9.mp4`.
