# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

**What it predicts / suggests:** Given a user's stated taste preferences (favorite genre, preferred mood, target energy level, and whether they like acoustic music), VibeFinder ranks all songs in a small catalog and returns the top 5 most relevant suggestions, along with a plain-English explanation of why each song was chosen.

It does **not** learn from listening history or behavior. Every recommendation is purely based on how well a song's attributes match the user's stated preferences at the moment of the request.

---

## 3. How the Model Works

VibeFinder looks at four things about each song and compares them to what the user told us they like:

1. **Genre** — does the song belong to the user's favorite genre? This gets the most points because genre is usually the first thing a listener uses to filter music.
2. **Mood** — does the song's mood match what the user is looking for (e.g., happy, chill, intense)? Mood shapes whether a song fits the moment, so it gets the second-highest weight.
3. **Energy** — how close is the song's energy level (0 to 1) to the user's target? A song that is slightly off gets partial credit; a song that is very far off gets almost none. This rewards "close enough" rather than just "high" or "low."
4. **Acoustic feel** — if the user said they like acoustic music, songs with a high acousticness score get a small bonus.

Each song gets a total score from these four factors. VibeFinder then sorts all songs from highest to lowest score and returns the top results. It also writes a short sentence explaining why each song was chosen.

---

## 4. Data

- **Catalog size:** 20 songs in `data/songs.csv` (expanded from the original 10)
- **Genres represented:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, folk, electronic, r&b, country, hip-hop
- **Moods represented:** happy, chill, intense, relaxed, focused, moody
- **Moods NOT in catalog:** sad, melancholic, angry, euphoric — any user requesting these gets zero mood points on every song
- **Genres NOT in catalog:** classical, metal, reggae, afrobeats, k-pop, cumbia — any user requesting these gets zero genre points on every song
- **Whose taste does this reflect?** The catalog skews toward contemporary Western genres and English-language music conventions. Moods like "happy" and "chill" reflect assumptions common in North American and European streaming culture.

---

## 5. Strengths

- Works well for users whose favorite genre and mood appear in the catalog — a "pop / happy" user consistently gets the most relevant results.
- The energy-closeness formula is fairer than a simple "high energy = good" rule: it rewards songs that match the user's actual level, even if that level is low.
- The scoring logic is fully transparent — every point can be traced back to a specific attribute match, which makes it easy to audit and explain.
- Simple enough to run without any machine learning library or training data.

---

## 6. Limitations and Bias

**Discovered through adversarial testing with seven profiles:**

1. **Missing vocabulary is silent.** When a user requests mood "sad" or genre "classical" — neither of which exists in the catalog — the system returns results anyway with no warning. The user cannot tell their core preference was ignored. In a real product this could seriously mislead listeners.

2. **Contradictory preferences produce nonsense rankings.** A "Lofi Intensifier" profile (genre=lofi, energy=0.9) exposes a fatal conflict: all lofi songs have energy below 0.45. The genre signal and energy signal fight each other. The system returns lofi songs with almost no energy closeness, interleaved with rock songs that match energy but not genre. Neither group satisfies the stated vibe.

3. **Acoustic preference can be silently dropped.** A user who sets `likes_acoustic=True` while targeting high-energy rock will have that preference ignored — no high-energy rock songs in the catalog exceed the acousticness threshold (0.6). The user sees the same results as if they had not stated acoustic preference at all.

4. **Genre exact-string matching penalizes related genres.** "indie pop" and "pop" are completely unrelated in the scoring math. A pop fan gets zero genre points for every indie pop song, even though the genres are adjacent.

5. **Filter bubble by design.** Because genre carries the highest weight (2.0 out of a max 5.5), the same genre will dominate every recommendation for a given profile. Over time this narrows exposure rather than encouraging discovery.

---

## 7. Evaluation

Seven profiles were tested — three standard and four adversarial/edge-case:

| Profile | Type | Top result | As expected? |
|---|---|---|---|
| Pop / happy / energy 0.8 | Standard | Sunrise City (pop/happy) | Yes |
| Lofi / chill / energy 0.38 / acoustic | Standard | Library Rain (lofi/chill/acoustic) | Yes |
| Rock / intense / energy 0.9 | Standard | Storm Runner (rock/intense) | Yes |
| Rock / **sad** / energy 0.88 | Edge — mood missing | Thunder Protocol (rock/intense) | Partial — genre correct, mood silently dropped |
| **Classical** / relaxed / energy 0.35 / acoustic | Edge — genre missing | Coffee Shop Stories (jazz/relaxed) | Reasonable fallback, but not classical |
| Rock / intense / energy 0.92 / **acoustic** | Edge — feature conflict | Storm Runner (rock/intense, low acousticness) | Acoustic preference silently dropped |
| **Lofi** / intense / energy **0.9** | Edge — contradictory | Midnight Coding (lofi/chill, energy 0.42) | Wrong — genre won but energy is opposite |

**Weight experiment — Intense Rock Fan with energy×2, genre÷2:**

| | #1 | #2 | #3 | Gap (#1 vs #3) |
|---|---|---|---|---|
| Original weights (genre=2.0, energy×=2.0) | Storm Runner 4.98 | Thunder Protocol 4.96 | Gym Hero 2.94 | 2.04 pts |
| Experimental (genre=1.0, energy×=4.0) | Storm Runner 5.96 | Thunder Protocol 5.92 | Gym Hero 4.88 | 1.08 pts |

The top-2 stayed the same (they had all three signals), but the buffer protecting them from wrong-genre songs shrank by half. In a larger catalog, non-rock songs would break into the top results entirely.

**Automated tests (`pytest`):**
- `recommend()` returns songs sorted by score, best genre+mood match first — PASS
- `explain_recommendation()` returns a non-empty string — PASS

---

## 8. Intended Use and Non-Intended Use

**Intended use:**
- Classroom exploration of how content-based recommendation logic works
- Learning how weighted scoring turns structured data into ranked suggestions
- Demonstrating algorithmic bias in a safe, small-scale environment
- Showing students how a scoring formula can have unintended consequences

**Not intended for:**
- Real music listeners or production deployment
- Serving users with taste profiles outside the catalog's genre/mood vocabulary
- Making any claims about musical quality or cultural value
- Replacing a real recommendation system that uses listening history or collaborative signals

---

## 9. Ideas for Improvement

- **Multi-genre profiles:** Let users specify up to three genres with individual weights instead of a single favorite, so people with broad taste are not penalized.
- **Vocabulary mismatch warnings:** When a user's requested genre or mood does not match any song in the catalog, surface a clear message rather than silently falling back.
- **Diversity injection:** After ranking, swap one of the top-5 results for a "wildcard" from a different genre — this intentionally fights filter bubbles and introduces serendipity.
- **Tempo as a signal:** BPM directly affects workout suitability and danceability; a "tempo range" preference would make the system more useful for activity-specific listening.
- **Negative preferences:** Let users say "never recommend hip-hop" rather than only specifying what they like.

---

## 10. Personal Reflection

**Biggest learning moment:**  
The adversarial profiles were the most revealing part of the project. When I asked for "sad mood" — a preference that seemed completely reasonable — the system returned results without any indication the mood was ignored. That silence is dangerous. A real user would have no idea their preference was dropped. The biggest lesson was that a model's failures are often invisible by design, not by accident.

**How AI tools helped and when I had to double-check:**  
AI tools were useful for generating the scoring formula structure and for suggesting test profiles I might not have thought of (like the acoustic-rocker conflict). But I had to manually verify the math: the energy closeness formula `(1 - |delta|) × weight` was suggested correctly, but when the AI initially described the weight experiment it got the resulting score totals wrong. I ran the actual code to verify. The numbers in the code are always more trustworthy than a verbal description of what the numbers will be.

**What surprised me about simple algorithms feeling like recommendations:**  
Even four weighted rules and 20 songs feel surprisingly "correct" when the profile matches the catalog well. The pop/happy/0.8 profile returns Sunrise City first every time — and Sunrise City really is the most pop/happy/energetic song. The formula is not magic; it is just arithmetic. But because the inputs (genre, mood, energy) are things humans actually think about when choosing music, the output *feels* like taste, even though it is just addition and comparison.

**What I would try next:**  
First, add a vocabulary check so the system warns when a genre or mood has no catalog matches. Second, build a "diversity mode" that intentionally puts one surprising song in every top-5. Third, connect this to a real dataset (like the Million Song Dataset or a Spotify API sample) to see whether the same simple weights still hold up at scale — or whether the catalog's composition itself was doing most of the work.
