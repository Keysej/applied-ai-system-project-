# VibeFinder Genre Guide
# Second RAG data source — loaded by ai_interface.py during preference parsing.
# Gives Claude richer domain knowledge for edge cases: slang, artist names, activities.

## Genre Profiles

### pop
Energy range: 0.60–0.95 | Moods: happy, intense
Key characteristics: catchy melodies, polished production, wide appeal.
Slang / signals: "top 40", "radio hits", "bops", "mainstream", "chart music"
Example artists: Taylor Swift, Dua Lipa, The Weeknd, Olivia Rodrigo

### lofi
Energy range: 0.22–0.50 | Moods: chill, focused
Key characteristics: lo-fi production quality, ambient noise, slow tempos, calm atmosphere.
Slang / signals: "study beats", "lofi hip hop", "background music", "2am", "coding music", "rain sounds"
Example artists: LoRoom, ChilledCow, Nujabes, j^p^n

### rock
Energy range: 0.65–1.00 | Moods: intense, happy
Key characteristics: electric guitars, strong drums, powerful vocals.
Slang / signals: "guitar music", "riffs", "headbanger", "band", "distortion", "driven"
Example artists: Nirvana, Arctic Monkeys, Foo Fighters, AC/DC

### ambient
Energy range: 0.10–0.40 | Moods: chill, relaxed
Key characteristics: texture-focused, minimal beat, atmospheric layers, no vocals.
Slang / signals: "soundscape", "space music", "drone", "meditation", "sleep music", "atmospheric"
Example artists: Brian Eno, Moby, Sigur Rós, Stars of the Lid

### jazz
Energy range: 0.30–0.65 | Moods: relaxed, happy
Key characteristics: improvisation, complex chords, acoustic instruments, swing feel.
Slang / signals: "jazzy", "smooth", "coffee shop", "cafe music", "blue note", "swing", "bebop"
Example artists: Norah Jones, Miles Davis, John Coltrane, Diana Krall

### electronic
Energy range: 0.65–1.00 | Moods: intense, happy
Key characteristics: synthesizers, heavy beats, digital production, dancefloor energy.
Slang / signals: "EDM", "dance music", "club", "rave", "techno", "house", "bass drop"
Example artists: Daft Punk, Deadmau5, Flume, Disclosure

### folk
Energy range: 0.25–0.55 | Moods: relaxed, chill, happy
Key characteristics: acoustic instruments, storytelling lyrics, natural sound, stripped-down.
Slang / signals: "acoustic", "campfire", "singer-songwriter", "unplugged", "woodsy", "earthy"
Example artists: Bon Iver, Fleet Foxes, Iron & Wine, The Lumineers

### indie pop
Energy range: 0.50–0.85 | Moods: happy, moody
Key characteristics: indie aesthetic combined with pop hooks, often introspective.
Slang / signals: "indie", "alt pop", "bedroom pop", "dream pop", "indie-pop", "alternative"
Example artists: Billie Eilish, Clairo, Phoebe Bridgers, Tame Impala, Vampire Weekend

### r&b
Energy range: 0.50–0.85 | Moods: moody, happy, relaxed
Key characteristics: rhythmic grooves, soulful vocals, emotional production.
Slang / signals: "soul", "smooth r&b", "neo-soul", "rnb", "groove", "soulful"
Example artists: Frank Ocean, SZA, H.E.R., Daniel Caesar

### hip-hop
Energy range: 0.60–0.95 | Moods: intense, happy
Key characteristics: rap vocals over beats, samples, strong rhythmic emphasis.
Slang / signals: "rap", "trap", "bars", "drill", "hype", "pregame", "workout rap"
Example artists: Kendrick Lamar, J. Cole, Drake, Travis Scott, Tyler the Creator

### country
Energy range: 0.45–0.80 | Moods: happy, relaxed
Key characteristics: storytelling, acoustic-electric blend, rural and emotional themes.
Slang / signals: "country", "southern", "twang", "country pop", "Nashville", "boots"
Example artists: Morgan Wallen, Kacey Musgraves, Luke Combs, Zach Bryan

### synthwave
Energy range: 0.55–0.90 | Moods: moody, intense
Key characteristics: 80s-inspired synthesizers, retro-futuristic, cinematic and nostalgic.
Slang / signals: "80s", "retro synth", "retrowave", "outrun", "neon", "night drive", "vaporwave"
Example artists: Kavinsky, Gunship, FM-84, Perturbator

---

## Activity → Genre Mapping
Use when user describes what they're doing rather than what they want to hear:

| Activity | Best genre | Mood | Energy |
|---|---|---|---|
| Studying / coding / focusing | lofi | focused | 0.35–0.45 |
| Working out / gym / running | hip-hop or electronic | intense | 0.80–0.95 |
| Sleeping / winding down | ambient | chill | 0.10–0.25 |
| Road trip / driving | rock or pop | happy or intense | 0.70–0.90 |
| Night drive alone | synthwave | moody | 0.65–0.80 |
| Coffee shop / café | jazz | relaxed | 0.35–0.55 |
| Party / dancing | electronic or pop | happy | 0.75–0.95 |
| Feeling sad / heartbreak | indie pop or r&b | moody | 0.40–0.60 |
| Sunday morning / lazy | folk or jazz | relaxed | 0.25–0.45 |
| Cooking / cleaning | pop or hip-hop | happy | 0.65–0.80 |

---

## Artist → Profile Mapping
Use when user names an artist they like:

| Artist mentioned | Genre | Mood | Energy |
|---|---|---|---|
| Billie Eilish | indie pop | moody | 0.50 |
| Taylor Swift | pop | happy | 0.75 |
| Kendrick Lamar | hip-hop | intense | 0.85 |
| Frank Ocean | r&b | moody | 0.55 |
| Bon Iver | folk | chill | 0.35 |
| Daft Punk | electronic | intense | 0.85 |
| Norah Jones | jazz | relaxed | 0.35 |
| Arctic Monkeys | rock | intense | 0.80 |
| The Weeknd | pop | moody | 0.72 |
| Mac DeMarco | indie pop | chill | 0.45 |
| Kavinsky | synthwave | moody | 0.75 |
| SZA | r&b | moody | 0.58 |
