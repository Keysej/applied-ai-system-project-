"""
VibeFinder 1.0 — Extended Edition CLI

Demonstrates all four optional extension challenges:
  Challenge 1 — New song features: popularity, release decade, mood tags
  Challenge 2 — Scoring modes: Balanced / Genre-First / Mood-First /
                               Energy-Focused / Discovery
  Challenge 3 — Diversity mode: artist + genre repeat penalties
  Challenge 4 — Tabulate-formatted terminal output with reasons column

Run with:
    python -m src.main
"""

from tabulate import tabulate

from . import recommender as rec_module
from .recommender import (
    load_songs,
    recommend_songs,
    recommend_diverse,
    BALANCED,
    GENRE_FIRST,
    MOOD_FIRST,
    ENERGY_FOCUSED,
    DISCOVERY,
    ALL_MODES,
)


# ---------------------------------------------------------------------------
# Taste profiles
# ---------------------------------------------------------------------------
# Extended profiles include the new Challenge-1 preference keys:
#   prefers_popular  – True → popularity score is added
#   target_decade    – "2010s" / "2020s" / "" → decade bonus
#   mood_tags        – list of detail tags to match against song mood_tags

PROFILES = {
    # ---- Standard profiles ------------------------------------------------

    "Intense Rock Fan": {
        "genre": "rock", "mood": "intense", "energy": 0.90,
        "likes_acoustic": False,
        "prefers_popular": False, "target_decade": "2010s",
        "mood_tags": ["aggressive", "driving"],
    },
    "Chill Lofi Listener": {
        "genre": "lofi", "mood": "chill", "energy": 0.38,
        "likes_acoustic": True,
        "prefers_popular": False, "target_decade": "2020s",
        "mood_tags": ["calm", "focused", "mellow"],
    },
    "Pop Happy Listener": {
        "genre": "pop", "mood": "happy", "energy": 0.80,
        "likes_acoustic": False,
        "prefers_popular": True, "target_decade": "2020s",
        "mood_tags": ["uplifting", "danceable"],
    },

    # ---- Adversarial / edge-case profiles ---------------------------------

    "High Energy Sad [EDGE]": {
        "genre": "rock", "mood": "sad", "energy": 0.88,
        "likes_acoustic": False,
        "prefers_popular": False, "target_decade": "",
        "mood_tags": [],
    },
    "Classical Acoustic [EDGE]": {
        "genre": "classical", "mood": "relaxed", "energy": 0.35,
        "likes_acoustic": True,
        "prefers_popular": False, "target_decade": "2000s",
        "mood_tags": ["mellow", "nostalgic"],
    },
    "Acoustic Rocker [EDGE]": {
        "genre": "rock", "mood": "intense", "energy": 0.92,
        "likes_acoustic": True,
        "prefers_popular": False, "target_decade": "",
        "mood_tags": ["aggressive"],
    },
    "Lofi Intensifier [EDGE]": {
        "genre": "lofi", "mood": "intense", "energy": 0.90,
        "likes_acoustic": False,
        "prefers_popular": False, "target_decade": "",
        "mood_tags": [],
    },
}

DIVIDER = "─" * 70


# ---------------------------------------------------------------------------
# Challenge 4: Tabulate helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, width: int = 34) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def results_to_table(
    results: list,
    title: str,
    mode_name: str = "",
) -> str:
    """Render a recommendation list as a tabulate grid table."""
    header_line = f"  {title}"
    if mode_name:
        header_line += f"  [{mode_name}]"

    rows = []
    for rank, item in enumerate(results, start=1):
        song, score, reasons = item[0], item[1], item[2]
        genre_mood = f"{song['genre']} / {song['mood']}"
        pop = song.get("popularity", "?")
        decade = song.get("release_decade", "")
        tags = "|".join(song.get("mood_tags", []))
        reason_str = _truncate(", ".join(reasons))
        rows.append([
            f"#{rank}",
            _truncate(song["title"], 22),
            _truncate(song["artist"], 16),
            genre_mood,
            f"{score:.2f}",
            f"{pop}  {decade}",
            reason_str,
        ])

    table = tabulate(
        rows,
        headers=["", "Title", "Artist", "Genre/Mood", "Score", "Pop Decade", "Reasons"],
        tablefmt="rounded_outline",
        colalign=("right", "left", "left", "left", "right", "center", "left"),
    )
    return f"\n{header_line}\n{table}"


# ---------------------------------------------------------------------------
# Section printers
# ---------------------------------------------------------------------------

def section(label: str) -> None:
    print(f"\n{'━' * 70}")
    print(f"  {label}")
    print(f"{'━' * 70}")


def run_all_profiles(songs: list) -> None:
    """Challenge 1 + 4: run every profile under BALANCED mode, tabulate output."""
    section("CHALLENGE 1 + 4 — All Profiles (Balanced mode, new attributes scored)")
    for name, prefs in PROFILES.items():
        results = recommend_songs(prefs, songs, k=5, mode=BALANCED)
        print(results_to_table(results, name, mode_name="Balanced"))


def run_scoring_modes(songs: list) -> None:
    """Challenge 2: show how different scoring modes rerank the same profile."""
    prefs = PROFILES["Pop Happy Listener"]
    section("CHALLENGE 2 — Scoring Modes  (profile: Pop Happy Listener)")
    print(f"\n  Profile: genre=pop  mood=happy  energy=0.8  "
          f"tags={prefs['mood_tags']}  decade={prefs['target_decade']}")

    for mode in ALL_MODES:
        results = recommend_songs(prefs, songs, k=5, mode=mode)
        print(results_to_table(results, "", mode_name=mode.name))


def run_diversity_comparison(songs: list) -> None:
    """Challenge 3: side-by-side standard vs diversity-penalized output."""
    prefs = PROFILES["Chill Lofi Listener"]
    section("CHALLENGE 3 — Diversity Mode  (profile: Chill Lofi Listener)")
    print(f"\n  Profile: genre=lofi  mood=chill  energy=0.38  acoustic=True")

    # Standard — no diversity constraint
    standard = recommend_songs(prefs, songs, k=5, mode=BALANCED)
    print(results_to_table(standard, "Standard (no diversity constraint)", mode_name="Balanced"))

    # Diverse — max 1 song per artist, max 2 per genre
    diverse = recommend_diverse(prefs, songs, k=5, max_per_artist=1, max_per_genre=2, mode=BALANCED)
    print(results_to_table(diverse, "Diversity mode  (max 1/artist · max 2/genre)", mode_name="Balanced"))

    # Show which artists appear in each
    std_artists  = [item[0]["artist"] for item in standard]
    div_artists  = [item[0]["artist"] for item in diverse]
    std_genres   = [item[0]["genre"]  for item in standard]
    div_genres   = [item[0]["genre"]  for item in diverse]

    print(f"\n  Standard artists : {std_artists}")
    print(f"  Diverse  artists : {div_artists}")
    print(f"\n  Standard genres  : {std_genres}")
    print(f"  Diverse  genres  : {div_genres}")

    new_artists = set(div_artists) - set(std_artists)
    if new_artists:
        print(f"\n  New artists surfaced by diversity mode: {new_artists}")
    else:
        print(f"\n  (Same artist set — catalog too small to force new artists at k=5)")


def run_mood_tag_spotlight(songs: list) -> None:
    """Show how mood_tags change rankings under DISCOVERY mode vs GENRE_FIRST."""
    section("BONUS — Mood-Tag Spotlight  (nostalgic listener, Discovery vs Genre-First)")
    prefs = {
        "genre": "pop", "mood": "happy", "energy": 0.70,
        "likes_acoustic": False,
        "prefers_popular": False, "target_decade": "2010s",
        "mood_tags": ["nostalgic", "warm", "romantic"],
    }
    print(f"\n  Profile: genre=pop  energy=0.7  tags=nostalgic|warm|romantic  decade=2010s")

    for mode in [GENRE_FIRST, DISCOVERY]:
        results = recommend_songs(prefs, songs, k=5, mode=mode)
        print(results_to_table(results, "", mode_name=mode.name))

    print(f"\n  Observation: Discovery mode reduces genre weight so mood-tag overlap")
    print(f"  can surface jazz/folk/country songs that share 'nostalgic' or 'warm'.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded {len(songs)} songs  |  "
          f"new attributes: popularity, release_decade, mood_tags")

    run_all_profiles(songs)
    run_scoring_modes(songs)
    run_diversity_comparison(songs)
    run_mood_tag_spotlight(songs)

    print(f"\n{'━' * 70}\n")


if __name__ == "__main__":
    main()
