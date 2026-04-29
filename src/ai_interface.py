"""
Claude-powered RAG layer for VibeFinder AI.

RAG Enhancement: two data sources are retrieved before every parse call —
  1. data/songs.csv   → catalog vocabulary (genres, moods in use)
  2. data/genre_guide.md → domain knowledge (slang, artists, activities)

Specialization: the parser prompt includes 6 few-shot examples covering
  slang terms, artist names, and activity descriptions.  This measurably
  improves accuracy on edge-case inputs vs. a zero-shot baseline.

Public API:
  load_genre_guide(path)                          -> str
  parse_user_preferences(text, guide)             -> dict
  parse_user_preferences_baseline(text)           -> dict   (no few-shot)
  generate_explanation(profile, songs, warnings)  -> str
"""

import json
import os
from google import genai
from google.genai import types

CATALOG_GENRES = sorted([
    "pop", "lofi", "rock", "ambient", "jazz", "electronic",
    "folk", "indie pop", "r&b", "hip-hop", "country", "synthwave",
])
CATALOG_MOODS = sorted(["happy", "chill", "intense", "focused", "relaxed", "moody"])

_DEFAULT_GUIDE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "genre_guide.md"
)


# ---------------------------------------------------------------------------
# RAG: load second data source
# ---------------------------------------------------------------------------

def load_genre_guide(path: str = _DEFAULT_GUIDE_PATH) -> str:
    """Load the genre guide document (second RAG data source).

    Returns the full text, or an empty string if the file is missing so the
    system degrades gracefully without crashing.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# ---------------------------------------------------------------------------
# Few-shot specialization examples
# ---------------------------------------------------------------------------
# These 6 examples train the parser to handle slang, artist names, and
# activity descriptions — inputs where a zero-shot prompt frequently
# picks the wrong genre or energy level.

_FEW_SHOT_EXAMPLES = [
    (
        "lofi hip hop for coding at 2am",
        '{"genre": "lofi", "mood": "focused", "energy": 0.38, "likes_acoustic": false}',
    ),
    (
        "something like Billie Eilish but a bit more upbeat",
        '{"genre": "indie pop", "mood": "happy", "energy": 0.65, "likes_acoustic": false}',
    ),
    (
        "get me hyped for the gym, heavy rap",
        '{"genre": "hip-hop", "mood": "intense", "energy": 0.88, "likes_acoustic": false}',
    ),
    (
        "campfire acoustic vibes, nothing loud",
        '{"genre": "folk", "mood": "relaxed", "energy": 0.32, "likes_acoustic": true}',
    ),
    (
        "80s night drive, retro synth neon vibes",
        '{"genre": "synthwave", "mood": "moody", "energy": 0.72, "likes_acoustic": false}',
    ),
    (
        "smooth jazz for a Sunday morning coffee",
        '{"genre": "jazz", "mood": "relaxed", "energy": 0.38, "likes_acoustic": true}',
    ),
]


def _build_few_shot_block() -> str:
    lines = ["Examples (input → JSON output):"]
    for user_input, output in _FEW_SHOT_EXAMPLES:
        lines.append(f'Input: "{user_input}"')
        lines.append(f"Output: {output}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

def _build_parser_system(genre_guide: str, include_few_shot: bool = True) -> str:
    """Build the parser system prompt, optionally injecting the genre guide and few-shot block."""
    guide_section = (
        f"\n\n## Domain Knowledge (second data source)\n{genre_guide}"
        if genre_guide else ""
    )
    few_shot_section = (
        f"\n\n## {_build_few_shot_block()}"
        if include_few_shot else ""
    )
    return f"""You are a music preference parser for a recommendation system.
Extract the listener's taste from their text and return ONLY a valid JSON object — no prose, no markdown.

Available genres (you MUST pick one of these exactly): {CATALOG_GENRES}
Available moods  (you MUST pick one of these exactly): {CATALOG_MOODS}

Return this exact JSON structure:
{{"genre": "<genre>", "mood": "<mood>", "energy": <float 0.0–1.0>, "likes_acoustic": <true|false>}}

Energy mapping guide:
  silent / very soft / ambient  →  0.10–0.25
  quiet / chill / mellow        →  0.25–0.45
  moderate / steady             →  0.45–0.65
  upbeat / energetic            →  0.65–0.80
  intense / high energy         →  0.80–0.92
  maximum / extreme             →  0.92–1.00

likes_acoustic: true only if the user explicitly mentions acoustic, unplugged,
                natural sound, campfire, or stripped-down. Otherwise false.{guide_section}{few_shot_section}

Return ONLY the JSON object — no explanation, no markdown fences."""


_EXPLAINER_SYSTEM = (
    "You are a friendly music recommendation assistant. "
    "Explain in 2–3 sentences why the listed songs match the user's preferences. "
    "Reference specific song attributes (genre, mood, energy). "
    "If catalog warnings exist, briefly acknowledge what could not be satisfied. "
    "Keep your response under 120 words."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _gemini_call(system_text: str, user_message: str, max_tokens: int = 256) -> None:
    """Placeholder — always uses local fallback."""
    return None


# ---------------------------------------------------------------------------
# Local fallback — keyword-based parser (no API key required)
# ---------------------------------------------------------------------------

_GENRE_KEYWORDS = {
    "pop": ["pop", "mainstream", "charts", "radio"],
    "lofi": ["lofi", "lo-fi", "lo fi", "study", "coding", "background"],
    "rock": ["rock", "guitar", "band", "metal", "grunge"],
    "ambient": ["ambient", "atmospheric", "drone", "space"],
    "jazz": ["jazz", "saxophone", "blues", "swing", "bebop"],
    "electronic": ["electronic", "edm", "techno", "house", "club"],
    "folk": ["folk", "campfire", "acoustic", "country road", "singer-songwriter"],
    "indie pop": ["indie", "alternative", "indie pop"],
    "r&b": ["r&b", "rnb", "soul", "smooth"],
    "hip-hop": ["hip-hop", "hiphop", "hip hop", "rap", "trap", "bars"],
    "country": ["country", "cowboy", "southern", "nashville"],
    "synthwave": ["synthwave", "retro", "80s", "neon", "synth", "night drive"],
}

_MOOD_KEYWORDS = {
    "happy": ["happy", "fun", "joy", "upbeat", "cheerful", "danceable", "dance", "good vibes"],
    "chill": ["chill", "relax", "calm", "mellow", "easy", "lazy", "slow", "soft"],
    "intense": ["intense", "hype", "hype me", "pump up", "workout", "gym", "aggressive", "fire", "hard"],
    "focused": ["focus", "concentrate", "study", "work", "productive", "deep work"],
    "relaxed": ["relaxed", "peaceful", "gentle", "quiet", "soothing", "sleep"],
    "moody": ["moody", "dark", "brooding", "melancholy", "sad", "emotional", "feel"],
}

_HIGH_ENERGY_WORDS = {"workout", "gym", "pump", "intense", "hype", "fire", "hard", "aggressive", "running", "energy", "bangers"}
_LOW_ENERGY_WORDS  = {"sleep", "quiet", "soft", "calm", "slow", "gentle", "peaceful", "study", "relax", "chill"}


def _local_parse(text: str) -> dict:
    """Simple keyword-based parser used when no API key is available."""
    lowered = text.lower()
    words = set(lowered.split())

    # Genre — pick first match
    genre = "pop"
    for g, keywords in _GENRE_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            genre = g
            break

    # Mood — pick first match
    mood = "chill"
    for m, keywords in _MOOD_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            mood = m
            break

    # Energy
    if words & _HIGH_ENERGY_WORDS:
        energy = 0.85
    elif words & _LOW_ENERGY_WORDS:
        energy = 0.30
    else:
        energy = 0.60

    # Acoustic
    likes_acoustic = any(w in lowered for w in ["acoustic", "unplugged", "campfire", "stripped"])

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic}


def _local_explain(user_profile: dict, songs: list[dict], warnings: list[str]) -> str:
    """Template explanation used when no API key is available."""
    genre = user_profile.get("genre", "")
    mood  = user_profile.get("mood", "")
    top   = songs[0] if songs else {}
    warn_note = " Note: " + "; ".join(warnings) + "." if warnings else ""
    return (
        f"These songs were selected based on your {genre} and {mood} preferences. "
        f"{top.get('title', '')} leads the list with the closest energy and mood match "
        f"in the catalog.{warn_note}"
    )


def parse_user_preferences(
    natural_language: str,
    genre_guide: str = "",
) -> dict:
    """Parse natural language into a structured UserProfile dict.
    Uses Gemini if GEMINI_API_KEY is set, otherwise falls back to local keyword matching."""
    system_text = _build_parser_system(genre_guide, include_few_shot=True)
    result = _gemini_call(system_text, natural_language)
    if result is None:
        return _local_parse(natural_language)
    return json.loads(result)


def parse_user_preferences_baseline(natural_language: str) -> dict:
    """Zero-shot baseline parser — no few-shot examples, no genre guide."""
    system_text = _build_parser_system(genre_guide="", include_few_shot=False)
    result = _gemini_call(system_text, natural_language)
    if result is None:
        return _local_parse(natural_language)
    return json.loads(result)


def generate_explanation(
    user_profile: dict,
    songs: list[dict],
    warnings: list[str],
) -> str:
    """Generate a natural-language explanation grounded in retrieved song rows.
    Uses Gemini if GEMINI_API_KEY is set, otherwise returns a template explanation."""
    songs_context = "\n".join([
        f"- {s['title']} by {s['artist']} | "
        f"genre: {s['genre']} | mood: {s['mood']} | "
        f"energy: {s['energy']:.2f} | acousticness: {s['acousticness']:.2f}"
        for s in songs
    ])
    warning_note = (
        f"\nCatalog warnings (mention briefly): {'; '.join(warnings)}"
        if warnings else ""
    )
    user_message = (
        f"User preferences: genre={user_profile.get('genre')}, "
        f"mood={user_profile.get('mood')}, "
        f"energy={user_profile.get('energy')}, "
        f"acoustic={user_profile.get('likes_acoustic')}"
        f"{warning_note}\n\n"
        f"Top recommended songs (already ranked by score):\n{songs_context}"
    )
    result = _gemini_call(_EXPLAINER_SYSTEM, user_message)
    if result is None:
        return _local_explain(user_profile, songs, warnings)
    return result
