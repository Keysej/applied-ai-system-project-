from src.recommender import (
    Song, UserProfile, Recommender,
    score_song, recommend_songs, recommend_diverse,
    BALANCED, GENRE_FIRST, ENERGY_FOCUSED, DISCOVERY,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_songs() -> list:
    """Return a small catalog covering multiple genres and artists."""
    return [
        Song(id=1, title="Test Pop Track", artist="Artist A", genre="pop",
             mood="happy", energy=0.8, tempo_bpm=120, valence=0.9,
             danceability=0.8, acousticness=0.2,
             popularity=80, release_decade="2020s",
             mood_tags=["uplifting", "danceable"]),
        Song(id=2, title="Chill Lofi Loop", artist="Artist B", genre="lofi",
             mood="chill", energy=0.4, tempo_bpm=80, valence=0.6,
             danceability=0.5, acousticness=0.9,
             popularity=40, release_decade="2020s",
             mood_tags=["calm", "mellow"]),
        Song(id=3, title="Rock Storm", artist="Artist A", genre="rock",
             mood="intense", energy=0.9, tempo_bpm=150, valence=0.4,
             danceability=0.6, acousticness=0.1,
             popularity=60, release_decade="2010s",
             mood_tags=["aggressive", "driving"]),
        Song(id=4, title="Jazz Corner", artist="Artist C", genre="jazz",
             mood="relaxed", energy=0.35, tempo_bpm=90, valence=0.7,
             danceability=0.5, acousticness=0.85,
             popularity=35, release_decade="2000s",
             mood_tags=["mellow", "nostalgic"]),
        Song(id=5, title="Pop Anthem", artist="Artist D", genre="pop",
             mood="happy", energy=0.85, tempo_bpm=128, valence=0.88,
             danceability=0.85, acousticness=0.1,
             popularity=90, release_decade="2020s",
             mood_tags=["uplifting", "energetic"]),
    ]


def pop_happy_prefs() -> dict:
    return {
        "genre": "pop", "mood": "happy", "energy": 0.8,
        "likes_acoustic": False,
        "prefers_popular": False, "target_decade": "", "mood_tags": [],
    }


# ---------------------------------------------------------------------------
# Original tests (must still pass)
# ---------------------------------------------------------------------------

def make_small_recommender() -> Recommender:
    songs = [
        Song(id=1, title="Test Pop Track", artist="Test Artist",
             genre="pop", mood="happy", energy=0.8, tempo_bpm=120,
             valence=0.9, danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Test Artist",
             genre="lofi", mood="chill", energy=0.4, tempo_bpm=80,
             valence=0.6, danceability=0.5, acousticness=0.9),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop", favorite_mood="happy",
        target_energy=0.8, likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)
    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop", favorite_mood="happy",
        target_energy=0.8, likes_acoustic=False,
    )
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Challenge 1: new attribute scoring
# ---------------------------------------------------------------------------

def test_popularity_bonus_fires_when_prefers_popular():
    prefs = {
        "genre": "", "mood": "", "energy": 0.5,
        "likes_acoustic": False, "prefers_popular": True,
        "target_decade": "", "mood_tags": [],
    }
    song_dict = {
        "genre": "pop", "mood": "happy", "energy": 0.5,
        "acousticness": 0.1, "popularity": 100,
        "release_decade": "", "mood_tags": [],
    }
    score_with, _ = score_song(prefs, song_dict, BALANCED)

    prefs_no_pop = dict(prefs, prefers_popular=False)
    score_without, _ = score_song(prefs_no_pop, song_dict, BALANCED)

    assert score_with > score_without, "Popularity bonus should increase score"


def test_decade_match_bonus():
    prefs = {
        "genre": "", "mood": "", "energy": 0.5,
        "likes_acoustic": False, "prefers_popular": False,
        "target_decade": "2010s", "mood_tags": [],
    }
    song_match = {
        "genre": "rock", "mood": "intense", "energy": 0.5,
        "acousticness": 0.1, "popularity": 50,
        "release_decade": "2010s", "mood_tags": [],
    }
    song_miss = dict(song_match, release_decade="2000s")
    score_match, _ = score_song(prefs, song_match, BALANCED)
    score_miss,  _ = score_song(prefs, song_miss,  BALANCED)
    assert score_match > score_miss, "Decade match should add bonus points"


def test_mood_tag_overlap_scoring():
    prefs = {
        "genre": "", "mood": "", "energy": 0.5,
        "likes_acoustic": False, "prefers_popular": False,
        "target_decade": "", "mood_tags": ["calm", "mellow", "focused"],
    }
    song_two_match = {
        "genre": "lofi", "mood": "chill", "energy": 0.5,
        "acousticness": 0.1, "popularity": 40,
        "release_decade": "", "mood_tags": ["calm", "mellow"],
    }
    song_no_match = dict(song_two_match, mood_tags=["aggressive", "driving"])

    score_match, _ = score_song(prefs, song_two_match, BALANCED)
    score_none,  _ = score_song(prefs, song_no_match,  BALANCED)
    assert score_match > score_none, "Mood-tag overlap should increase score"


# ---------------------------------------------------------------------------
# Challenge 2: scoring modes
# ---------------------------------------------------------------------------

def test_genre_first_mode_ranks_genre_match_higher():
    """Under GENRE_FIRST, genre weight is 4× — genre-matching song must win."""
    songs = make_songs()          # has pop songs (Artist A/D) and lofi/rock/jazz
    prefs = pop_happy_prefs()

    gf = recommend_songs(prefs, songs, k=5, mode=GENRE_FIRST)
    bal = recommend_songs(prefs, songs, k=5, mode=BALANCED)

    # Genre-first top result must be a pop song
    assert gf[0][0]["genre"] == "pop"
    # Genre-first should give the top genre-match song a higher score than balanced
    assert gf[0][1] > bal[0][1] or gf[0][0]["id"] == bal[0][0]["id"]


def test_energy_focused_top_is_closest_energy():
    """Under ENERGY_FOCUSED (energy weight 4×), the nearest-energy song wins."""
    prefs = {
        "genre": "jazz", "mood": "sad", "energy": 0.85,   # neither jazz nor sad exists
        "likes_acoustic": False, "prefers_popular": False,
        "target_decade": "", "mood_tags": [],
    }
    songs = make_songs()
    results = recommend_songs(prefs, songs, k=5, mode=ENERGY_FOCUSED)
    # All genre/mood points are 0 → sorted purely by energy closeness to 0.85
    energies = [item[0]["energy"] for item in results]
    # The top result should have energy closest to 0.85 among all songs
    assert abs(energies[0] - 0.85) <= 0.1


def test_discovery_mode_reduces_genre_dominance():
    """Under DISCOVERY, genre weight is 0.3 so a tag-rich off-genre song can beat a genre match."""
    # User wants pop, but the pop song has no matching tags
    # A jazz song with matching tags should outscore it under DISCOVERY
    prefs = {
        "genre": "pop", "mood": "happy", "energy": 0.5,
        "likes_acoustic": False, "prefers_popular": False,
        "target_decade": "", "mood_tags": ["mellow", "nostalgic"],
    }
    pop_no_tags = {
        "genre": "pop", "mood": "happy", "energy": 0.5,
        "acousticness": 0.1, "popularity": 50, "release_decade": "",
        "mood_tags": [],  # no matching tags
    }
    jazz_with_tags = {
        "genre": "jazz", "mood": "relaxed", "energy": 0.5,
        "acousticness": 0.85, "popularity": 35, "release_decade": "",
        "mood_tags": ["mellow", "nostalgic"],  # both user tags match
    }
    pop_score,  _ = score_song(prefs, pop_no_tags,    DISCOVERY)
    jazz_score, _ = score_song(prefs, jazz_with_tags, DISCOVERY)
    assert jazz_score > pop_score, (
        "Under DISCOVERY mode, tag overlap should outweigh the genre penalty"
    )


# ---------------------------------------------------------------------------
# Challenge 3: diversity
# ---------------------------------------------------------------------------

def test_diversity_limits_artist_repeats():
    """With max_per_artist=1 and k=4, no artist should appear twice.

    The catalog has 5 songs from 4 unique artists (Artist A appears twice).
    Asking for k=4 means the primary pass can fill all slots without
    repeating any artist; the fallback is never needed.
    """
    songs = make_songs()   # Artist A appears in songs 1 (pop) and 3 (rock)
    prefs = pop_happy_prefs()
    results = recommend_diverse(prefs, songs, k=4, max_per_artist=1, mode=BALANCED)
    artists = [item[0]["artist"] for item in results]
    assert len(results) == 4
    assert len(artists) == len(set(artists)), (
        f"Diversity mode should not repeat artists in primary pass: {artists}"
    )


def test_diversity_limits_genre_repeats():
    """With max_per_genre=1 and k=4, each genre appears at most once.

    The catalog has genres: pop (×2), lofi, rock, jazz — 4 distinct genres.
    k=4 means the primary pass picks one song per genre and fills all slots.
    """
    songs = make_songs()
    prefs = pop_happy_prefs()
    # k=4 matches the number of distinct genres in make_songs()
    results = recommend_diverse(prefs, songs, k=4, max_per_genre=1, mode=BALANCED)
    # Only count primary-pass results (no fallback annotation in reasons)
    primary = [item for item in results if not any("fallback" in r for r in item[2])]
    genres = [item[0]["genre"] for item in primary]
    for genre in set(genres):
        assert genres.count(genre) <= 1, (
            f"Genre '{genre}' appeared more than once in primary pass: {genres}"
        )


def test_diversity_still_returns_k_results():
    """Diversity mode should always return exactly k songs (or fewer if catalog is smaller)."""
    songs = make_songs()
    prefs = pop_happy_prefs()
    results = recommend_diverse(prefs, songs, k=5, max_per_artist=1, mode=BALANCED)
    assert len(results) == 5
