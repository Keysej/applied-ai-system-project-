# VibeFinder AI — Applied Music Recommendation System

**Built by Jimale Keyse** | Applied AI Systems Final Project

---

## Original Project

This system is an extension of **VibeFinder 1.0**, the Music Recommender Simulation built in Module 3.

The original project implemented a content-based recommender that scored songs against a structured user profile (genre, mood, energy, acoustic preference) using a four-signal weighted formula. It demonstrated how real platforms like Spotify translate song attributes into ranked suggestions, and documented algorithmic bias through adversarial testing — including silent failures when a user's requested genre or mood had no catalog match.

---

## What This Project Does and Why It Matters

VibeFinder AI upgrades the original rule-based system into a full applied AI pipeline. Instead of requiring users to manually specify a genre, mood, and energy value, they can now type naturally — *"something chill to study to"* or *"high energy workout bangers"* — and the system handles the rest.

Under the hood, a Claude language model reads the song catalog, extracts structured preferences from the user's text, scores and ranks every song using the original weighted algorithm, and then returns natural-language explanations grounded in the actual retrieved song data. A guardrails layer catches contradictory or out-of-catalog preferences before they silently corrupt results — the biggest failure mode of the original system. Every query is logged for review, and a test suite checks that scoring, guardrails, and AI outputs remain consistent.

This matters because it shows how a deterministic algorithm (weighted scoring) and a language model (Claude) can be composed responsibly: the algorithm does the math, the model does the language, and guardrails sit between the user and both.

---

## Architecture Overview

```
User (natural language) → Guardrails → Claude NL Parser → Weighted Scorer → Claude Explainer → Output
                                  ↕                                                      ↕
                              Logger                                                  Logger
                                  ↕
                           Test Suite (pytest)
```

![System Architecture](assets/architecture.png)

**Four main layers:**

| Layer | Component | Role |
|---|---|---|
| Safety | Guardrails | Validates input, warns about missing genres/moods and contradictions |
| Retrieval | Claude NL Parser | Reads `songs.csv` and converts natural language into a `UserProfile` |
| Logic | Weighted Scorer + Ranker | Scores all 20 songs deterministically, returns top-k |
| Generation | Claude Explainer | Receives the top-k song rows as context and writes natural explanations |

The RAG pattern appears in two places: the parser receives the catalog's genre and mood vocabulary before extracting preferences, and the explainer receives the actual matched song rows before writing output. Claude never invents songs or guesses scores — the retrieval step anchors every response to real data.

---

## Setup Instructions

**Requirements:** Python 3.10+, an Anthropic API key.

### 1. Clone and enter the repo

```bash
git clone https://github.com/Keysej/applied-ai-system-project-.git
cd applied-ai-system-project-
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Mac / Linux
set ANTHROPIC_API_KEY=sk-ant-...        # Windows
```

### 5. Run the app

```bash
python -m src.main
```

### 6. Run the test suite

```bash
pytest
```

Logs are written to `logs/session.log` automatically on every run.

---

## Sample Interactions

### Example 1 — Clear match

**User input:**
```
I want something happy and danceable, high energy pop
```

**Guardrails:** No warnings — genre `pop` and mood `happy` are both in catalog.

**Parsed profile:** `genre=pop · mood=happy · energy=0.85 · likes_acoustic=False`

**Top recommendations:**
```
#1  Gym Hero by Max Pulse          Score: 4.96
    Genre matches (pop), mood matches (intense→happy), energy 0.93 is very close to your target.

#2  Sunrise City by Neon Echo      Score: 4.94
    Pop track with a happy, uplifting feel and energy of 0.82 — nearly identical to your target level.

#3  Rooftop Lights by Indigo Parade  Score: 3.82
    Indie pop with a romantic, happy vibe. Slightly lower energy (0.76) but strong on mood and feel.
```

---

### Example 2 — Guardrail fires

**User input:**
```
Give me some sad classical music, very quiet and soft
```

**Guardrails output:**
```
⚠ WARNING: Genre 'classical' has no songs in the catalog. Genre score will be 0 for all results.
⚠ WARNING: Mood 'sad' has no songs in the catalog. Mood score will be 0 for all results.
Results below are ranked by energy closeness and acoustic fit only — they may not feel 'classical' or 'sad'.
```

**Parsed profile:** `genre=classical · mood=sad · energy=0.15 · likes_acoustic=True`

**Top recommendations (with caveat surfaced):**
```
#1  Glass Mountain by Paper Lanterns    Score: 2.43
    Very quiet ambient track (energy 0.22) with high acousticness (0.95). Closest energy match in catalog.

#2  Spacewalk Thoughts by Orbit Bloom   Score: 2.38
    Dreamy, introspective ambient track. Your requested genre and mood weren't found — these are the
    softest, most acoustic songs available.
```

---

### Example 3 — Contradiction detected

**User input:**
```
lofi hip hop but make it super intense and high energy, like 90% energy
```

**Guardrails output:**
```
⚠ WARNING: Conflicting preferences detected — genre 'lofi' typically has energy 0.35–0.45,
  but your target energy is 0.90. Lofi songs will score high on genre but low on energy.
  Consider genre 'hip-hop' or 'electronic' for high-energy results.
Proceeding with your original preferences. Results may feel inconsistent.
```

**Top recommendations:**
```
#1  Midnight Coding by LoRoom     Score: 3.84   (genre: lofi ✓ | energy: 0.42 vs target 0.90 — far off)
#2  Street Anthem by Nova Crew    Score: 3.60   (genre: hip-hop | energy: 0.85 — close, but genre miss)
```

*This example shows the system surfacing a real limitation rather than hiding it.*

---

## Design Decisions and Trade-offs

**Why RAG instead of a fine-tuned model?**
Fine-tuning requires a labeled training dataset that doesn't exist for this catalog. RAG lets Claude reason over the actual song rows at inference time, which means the system stays accurate even if the catalog grows or changes — no retraining needed.

**Why keep the weighted scorer instead of letting Claude rank everything?**
The deterministic scorer is auditable: every point can be traced to a specific attribute. Letting Claude rank songs would make the system a black box with no way to explain *why* Song A beat Song B by 0.3 points. The hybrid approach gives the best of both: algorithmic transparency for ranking, natural language for explanation.

**Why two Claude calls instead of one?**
Separating parsing from explanation keeps each prompt focused and testable. A single mega-prompt that both extracts preferences and explains results is harder to evaluate and more likely to hallucinate. Two smaller calls with a deterministic step in between are easier to debug and more reliable.

**Why guardrails before the Claude parser?**
If an out-of-catalog genre reaches the scorer, the failure is silent — the user gets results with no genre points and no explanation. Catching it before parsing means the warning appears in the output and in the log, which is the behavior a real product would need.

**Trade-offs accepted:**
- Catalog is only 20 songs — patterns hold at this scale but would need recalibration at thousands.
- Exact string matching for genre/mood is fragile — "indie pop" ≠ "pop." A future version could use embeddings to handle genre proximity.
- Two API calls per query adds latency (~1–2 seconds) compared to the original instant response.

---

## Testing Summary

**What the test suite covers:**

| Test category | What it checks |
|---|---|
| Scoring unit tests | Correct weight formula; genre/mood/energy/acoustic points add up as expected |
| Ranking tests | Top result for a pop/happy profile is always a pop/happy song |
| Guardrail tests | Missing genre triggers warning; contradictory energy/genre triggers warning; empty input is blocked |
| RAG integration tests | Claude returns valid JSON for the UserProfile; explanation string is non-empty |
| Regression tests | Same input produces same top result across repeated runs |

**What worked:**
The deterministic scorer is completely reliable — given the same profile, it returns the same ranked list every time. Guardrails caught every adversarial input that was tested, including the silent-failure cases discovered in Module 3.

**What didn't work at first:**
The initial Claude parser prompt returned genres that weren't in the catalog (e.g., "acoustic folk" instead of "folk"). Adding the catalog's exact genre and mood vocabulary to the system prompt fixed this — the model now selects from the known list rather than inventing its own.

**What I learned:**
The most important insight was that the deterministic layer and the AI layer need to be tested separately before testing them together. When they were wired end-to-end before unit tests existed, a bug in the scorer looked like a Claude hallucination and vice versa.

---

## Reflection

**What this project taught me about AI:**
The original recommender felt like it was "doing AI" but it was just arithmetic. Adding Claude changed what the system could *accept* — natural language instead of structured form fields — without changing how it *decides*. That separation was the clearest thing I learned: language models are interfaces, not decision-makers. The decision-making here is still the weighted formula, which I can audit, adjust, and explain. Claude handles the parts that are genuinely hard for code — understanding that "gym bangers" means high energy and that "quiet and soft" means low energy and high acousticness.

**What this taught me about responsible design:**
The guardrails were the hardest part to get right, not because the code was complex but because I had to think about failure modes before they happened. The original system's biggest problem — silent failures — was invisible until adversarial testing exposed it. Building the warning system forced me to anticipate what users would ask that the system couldn't handle, which is a different skill than building what the system *can* handle.

**What I would do next:**
1. Expand the catalog to 200+ songs so genre patterns are more meaningful.
2. Replace exact string matching with embedding similarity so "indie pop" and "pop" are treated as adjacent.
3. Add a feedback loop — after the user sees results, they can say "too slow" or "not happy enough" and the system re-scores with adjusted weights.
4. Build a simple Streamlit UI so the natural language interface is accessible without a terminal.

---

## Project Files

```
applied-ai-system-project/
├── assets/
│   ├── architecture.md            # Mermaid source for the system diagram
│   ├── architecture.png           # Exported diagram image
│   ├── presentation_script.md     # Slide-by-slide speaker notes
│   └── full_presentation_script.md # Word-for-word 7-minute script
├── data/
│   ├── songs.csv                  # 20-song catalog with 13 attributes
│   └── genre_guide.md             # Second RAG data source (slang, artists, activities)
├── logs/
│   └── session.log                # Auto-generated query/output log
├── scripts/
│   ├── eval_harness.py            # Evaluation harness — 10 test cases, confidence scores
│   └── compare_baseline.py        # Specialization proof — baseline vs few-shot comparison
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point (--interactive, --agent flags)
│   ├── recommender.py             # Song, UserProfile, Recommender, scoring modes
│   ├── ai_interface.py            # Claude NL parser + explainer + baseline (RAG)
│   ├── guardrails.py              # Input validation and bias warnings
│   └── agent.py                   # 6-step agentic workflow
├── tests/
│   ├── test_recommender.py        # Scoring, ranking, and diversity tests
│   ├── test_guardrails.py         # Guardrail behavior tests
│   └── test_ai_interface.py       # RAG integration tests (mocked)
├── conftest.py
├── model_card.md
├── requirements.txt
└── README.md
```

---

## Portfolio Artifact

**GitHub Repository:** [github.com/Keysej/applied-ai-system-project-](https://github.com/Keysej/applied-ai-system-project-)

**Loom Walkthrough:** *(add your Loom link here after recording)*

**What this project says about me as an AI engineer:**

I build systems I can explain. Every design decision in VibeFinder AI — keeping the deterministic scorer separate from Claude, running guardrails before the AI layer, testing each component in isolation — came from a single principle: if I can't trace why the system did what it did, it isn't finished. This project taught me that responsible AI engineering is less about choosing the most powerful model and more about knowing exactly where the model's job ends and the algorithm's job begins. I'm drawn to the boundary between language and logic, and I want to keep building things that sit right at that line.

---

## Model Card

For the full bias analysis, evaluation results, and responsible use documentation see [model_card.md](model_card.md).
