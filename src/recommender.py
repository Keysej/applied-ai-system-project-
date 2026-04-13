"""
Core recommendation logic for VibeFinder 1.0 (Extended Edition).

Public API
----------
load_songs(csv_path)                          -> List[Dict]
score_song(user_prefs, song, mode)            -> Tuple[float, List[str]]
recommend_songs(user_prefs, songs, k, mode)   -> List[Tuple[Dict, float, List[str]]]
recommend_diverse(user_prefs, songs, k, ...)  -> List[Tuple[Dict, float, List[str]]]

Scoring modes (Challenge 2 — Strategy pattern)
-----------------------------------------------
BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED, DISCOVERY

OOP API (required by tests)
----------------------------
Song, UserProfile, Recommender
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import csv


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """Represents a single song and all of its audio attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Extended attributes (Challenge 1)
    popularity: int = 50
    release_decade: str = ""
    mood_tags: List[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """Captures a listener's content-based taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Extended preferences (Challenge 1) — optional, defaults keep existing tests passing
    prefers_popular: bool = False
    target_decade: str = ""
    preferred_mood_tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Challenge 2: Scoring Modes — Strategy pattern
#
# Each ScoringMode is a named set of weights. Passing a different mode to
# score_song is all you need to switch the ranking strategy entirely.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScoringMode:
    """A named bundle of weights that controls how songs are ranked."""
    name: str
    w_genre: float      # binary: genre exact match
    w_mood: float       # binary: mood exact match
    w_energy: float     # continuous: (1 - |delta|) × w_energy
    w_acoustic: float   # conditional bonus: acousticness > threshold
    w_popularity: float # proportional: (popularity / 100) × w_popularity
    w_decade: float     # binary: release_decade match
    w_mood_tags: float  # overlap: (matching tags / user tags) × w_mood_tags

    def max_score(self) -> float:
        """Return the theoretical maximum score under this mode."""
        return (self.w_genre + self.w_mood + self.w_energy
                + self.w_acoustic + self.w_popularity
                + self.w_decade + self.w_mood_tags)


# Predefined modes — pick one to pass to score_song / recommend_songs
BALANCED = ScoringMode(
    name="Balanced",
    w_genre=2.0, w_mood=1.0, w_energy=2.0,
    w_acoustic=0.5, w_popularity=0.3, w_decade=0.5, w_mood_tags=0.8,
)

GENRE_FIRST = ScoringMode(
    name="Genre-First",
    w_genre=4.0, w_mood=0.5, w_energy=1.0,
    w_acoustic=0.3, w_popularity=0.2, w_decade=0.3, w_mood_tags=0.4,
)

MOOD_FIRST = ScoringMode(
    name="Mood-First",
    w_genre=1.0, w_mood=2.5, w_energy=1.0,
    w_acoustic=0.5, w_popularity=0.2, w_decade=0.3, w_mood_tags=2.0,
)

ENERGY_FOCUSED = ScoringMode(
    name="Energy-Focused",
    w_genre=0.5, w_mood=0.5, w_energy=4.0,
    w_acoustic=0.3, w_popularity=0.2, w_decade=0.3, w_mood_tags=0.4,
)

DISCOVERY = ScoringMode(
    name="Discovery",
    # Deliberately reduces genre and popularity weight so unexpected songs
    # can surface based on mood_tags and energy alone.
    w_genre=0.3, w_mood=0.5, w_energy=2.0,
    w_acoustic=0.5, w_popularity=0.0, w_decade=0.5, w_mood_tags=2.5,
)

ALL_MODES = [BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED, DISCOVERY]

# Diversity constants (Challenge 3)
ACOUSTIC_THRESHOLD = 0.6


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_dict(song) -> Dict:
    """Normalise a song to dict format.

    Accepts either a Song dataclass instance or a plain dict so that the
    functional API (recommend_songs, recommend_diverse, score_song) works
    transparently whether the caller passes Song objects or raw dicts.
    """
    if isinstance(song, dict):
        return song
    return {
        "id":             song.id,
        "title":          song.title,
        "artist":         song.artist,
        "genre":          song.genre,
        "mood":           song.mood,
        "energy":         song.energy,
        "tempo_bpm":      song.tempo_bpm,
        "valence":        song.valence,
        "danceability":   song.danceability,
        "acousticness":   song.acousticness,
        "popularity":     getattr(song, "popularity", 50),
        "release_decade": getattr(song, "release_decade", ""),
        "mood_tags":      getattr(song, "mood_tags", []),
    }
ARTIST_REPEAT_PENALTY = 0.50   # score multiplied by this for repeat artists
GENRE_REPEAT_PENALTY  = 0.70   # score multiplied by this when genre seen ≥ max times


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return them as a list of dicts.

    Numeric columns are cast to the correct types.
    The mood_tags column (pipe-separated) is split into a list.
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tags_raw = row.get("mood_tags", "")
            songs.append({
                "id":             int(row["id"]),
                "title":          row["title"],
                "artist":         row["artist"],
                "genre":          row["genre"],
                "mood":           row["mood"],
                "energy":         float(row["energy"]),
                "tempo_bpm":      float(row["tempo_bpm"]),
                "valence":        float(row["valence"]),
                "danceability":   float(row["danceability"]),
                "acousticness":   float(row["acousticness"]),
                # Extended (Challenge 1)
                "popularity":     int(row.get("popularity", 50)),
                "release_decade": row.get("release_decade", ""),
                "mood_tags":      [t.strip() for t in tags_raw.split("|") if t.strip()],
            })
    return songs


# ---------------------------------------------------------------------------
# Core scoring (Challenges 1 + 2)
# ---------------------------------------------------------------------------

def score_song(
    user_prefs: Dict,
    song: Dict,
    mode: ScoringMode = BALANCED,
) -> Tuple[float, List[str]]:
    """Score a single song against a user taste profile under a given mode.

    Parameters
    ----------
    user_prefs : dict — keys: genre, mood, energy, likes_acoustic,
                        prefers_popular, target_decade, mood_tags (list)
    song       : dict — keys matching songs.csv columns
    mode       : ScoringMode — controls how each signal is weighted

    Returns
    -------
    score   : float — higher means better match
    reasons : list[str] — one entry per signal that contributed points
    """
    song = _to_dict(song)   # accept both Song dataclass and plain dict
    score = 0.0
    reasons: List[str] = []

    # --- Genre match (binary) ---
    if song["genre"] == user_prefs.get("genre", ""):
        score += mode.w_genre
        reasons.append(f"genre match (+{mode.w_genre})")

    # --- Mood match (binary) ---
    if song["mood"] == user_prefs.get("mood", ""):
        score += mode.w_mood
        reasons.append(f"mood match (+{mode.w_mood})")

    # --- Energy closeness (continuous, 0 → w_energy) ---
    target_energy = user_prefs.get("energy", 0.5)
    energy_pts = (1.0 - abs(song["energy"] - target_energy)) * mode.w_energy
    score += energy_pts
    reasons.append(f"energy closeness (+{energy_pts:.2f})")

    # --- Acoustic fit (conditional bonus) ---
    if user_prefs.get("likes_acoustic", False) and song.get("acousticness", 0) > ACOUSTIC_THRESHOLD:
        score += mode.w_acoustic
        reasons.append(f"acoustic fit (+{mode.w_acoustic})")

    # --- Popularity bonus (Challenge 1) ---
    if mode.w_popularity > 0 and user_prefs.get("prefers_popular", False):
        pop_pts = (song.get("popularity", 50) / 100.0) * mode.w_popularity
        score += pop_pts
        reasons.append(f"popularity (+{pop_pts:.2f})")

    # --- Decade match (Challenge 1) ---
    target_decade = user_prefs.get("target_decade", "")
    if mode.w_decade > 0 and target_decade and song.get("release_decade", "") == target_decade:
        score += mode.w_decade
        reasons.append(f"decade match {target_decade} (+{mode.w_decade})")

    # --- Mood-tag overlap (Challenge 1) ---
    user_tags = set(user_prefs.get("mood_tags", []))
    song_tags = set(song.get("mood_tags", []))
    if mode.w_mood_tags > 0 and user_tags:
        overlap = len(user_tags & song_tags)
        tag_pts = (overlap / len(user_tags)) * mode.w_mood_tags
        if tag_pts > 0:
            score += tag_pts
            reasons.append(f"mood-tag overlap {user_tags & song_tags} (+{tag_pts:.2f})")

    return score, reasons


# ---------------------------------------------------------------------------
# Standard recommender
# ---------------------------------------------------------------------------

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: ScoringMode = BALANCED,
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song and return the top-k ranked highest to lowest.

    Uses score_song as the judge for every song in the catalog.
    sorted() is preferred over .sort() — it returns a new list and leaves
    the original catalog order intact for subsequent calls.

    Returns a list of (song_dict, score, reasons) tuples.
    """
    scored = [
        (d := _to_dict(song), *score_song(user_prefs, d, mode))
        for song in songs
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]


# ---------------------------------------------------------------------------
# Challenge 3: Diversity-aware recommender
# ---------------------------------------------------------------------------

def recommend_diverse(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    max_per_artist: int = 1,
    max_per_genre: int = 2,
    mode: ScoringMode = BALANCED,
) -> List[Tuple[Dict, float, List[str]]]:
    """Build a top-k list that avoids repeating the same artist or genre too often.

    Algorithm (greedy with hard exclusion + fallback):
    1. Score all songs and sort highest-to-lowest.
    2. Walk the sorted list and add each song only if it satisfies the
       diversity constraints (artist count < max_per_artist AND
       genre count < max_per_genre).
    3. If the primary pass fills fewer than k slots (constraints too strict
       for the catalog size), a fallback pass adds the highest-scoring
       remaining songs — annotated with a diversity-penalty note — until k
       is reached.

    Parameters
    ----------
    max_per_artist : int — max songs by the same artist allowed without penalty
    max_per_genre  : int — max songs from the same genre allowed without penalty
    """
    # Score and sort all songs; normalise to dict so entries are subscriptable
    scored = sorted(
        [(d := _to_dict(song), *score_song(user_prefs, d, mode)) for song in songs],
        key=lambda x: x[1],
        reverse=True,
    )

    results: List[Tuple[Dict, float, List[str]]] = []
    artist_count: Dict[str, int] = {}
    genre_count:  Dict[str, int] = {}
    used_ids: set = set()

    # Primary pass: add songs that satisfy diversity constraints
    for song, score, reasons in scored:
        if len(results) >= k:
            break
        if (artist_count.get(song["artist"], 0) < max_per_artist
                and genre_count.get(song["genre"], 0) < max_per_genre):
            results.append((song, score, reasons))
            artist_count[song["artist"]] = artist_count.get(song["artist"], 0) + 1
            genre_count[song["genre"]]   = genre_count.get(song["genre"], 0) + 1
            used_ids.add(song["id"])

    # Fallback pass: fill remaining slots with the best unused songs
    if len(results) < k:
        for song, score, reasons in scored:
            if len(results) >= k:
                break
            if song["id"] not in used_ids:
                note = f"diversity fallback (constraints relaxed)"
                results.append((song, score, reasons + [note]))
                used_ids.add(song["id"])

    return results


# ---------------------------------------------------------------------------
# OOP interface (required by tests/test_recommender.py)
# ---------------------------------------------------------------------------

class Recommender:
    """Content-based recommender backed by a fixed song catalog.

    Delegates all scoring to the module-level score_song function so
    the OOP and functional interfaces stay in sync.
    """

    def __init__(self, songs: List[Song]):
        """Initialise with a list of Song dataclass instances."""
        self.songs = songs

    def _song_to_dict(self, song: Song) -> Dict:
        """Convert a Song dataclass to the dict format expected by score_song."""
        return {
            "id":             song.id,
            "title":          song.title,
            "artist":         song.artist,
            "genre":          song.genre,
            "mood":           song.mood,
            "energy":         song.energy,
            "tempo_bpm":      song.tempo_bpm,
            "valence":        song.valence,
            "danceability":   song.danceability,
            "acousticness":   song.acousticness,
            "popularity":     song.popularity,
            "release_decade": song.release_decade,
            "mood_tags":      song.mood_tags,
        }

    def _prefs_from_profile(self, user: UserProfile) -> Dict:
        """Convert a UserProfile dataclass to the dict expected by score_song."""
        return {
            "genre":          user.favorite_genre,
            "mood":           user.favorite_mood,
            "energy":         user.target_energy,
            "likes_acoustic": user.likes_acoustic,
            "prefers_popular": user.prefers_popular,
            "target_decade":  user.target_decade,
            "mood_tags":      user.preferred_mood_tags,
        }

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        mode: ScoringMode = BALANCED,
    ) -> List[Song]:
        """Return the top-k Song objects ranked by score (highest first)."""
        prefs = self._prefs_from_profile(user)
        scored = sorted(
            self.songs,
            key=lambda s: score_song(prefs, self._song_to_dict(s), mode)[0],
            reverse=True,
        )
        return scored[:k]

    def explain_recommendation(
        self,
        user: UserProfile,
        song: Song,
        mode: ScoringMode = BALANCED,
    ) -> str:
        """Return a plain-English sentence explaining why this song was chosen."""
        prefs = self._prefs_from_profile(user)
        _, reasons = score_song(prefs, self._song_to_dict(song), mode)
        if reasons:
            return "Recommended because: " + ", and ".join(reasons) + "."
        return "Recommended as a discovery pick (best energy match available)."
