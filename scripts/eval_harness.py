"""
VibeFinder AI — Evaluation Harness

Runs the recommender on 10 predefined test cases and prints a structured
pass/fail report with confidence scores. No API key required — tests the
deterministic scoring and guardrail layers only.

Usage:
    python scripts/eval_harness.py

Exit code 0 if all tests pass, 1 if any fail.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.guardrails import validate_input, validate_profile
from src.recommender import BALANCED, load_songs, recommend_songs

_W = 68
MAX_SCORE = BALANCED.max_score()   # theoretical ceiling under BALANCED mode


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "Pop / happy / high energy",
        "profile": {"genre": "pop", "mood": "happy", "energy": 0.80, "likes_acoustic": False,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "pop",
        "expect_top_mood": "happy",
        "min_confidence": 65,
        "expect_warnings": False,
    },
    {
        "name": "Lofi / chill / acoustic",
        "profile": {"genre": "lofi", "mood": "chill", "energy": 0.38, "likes_acoustic": True,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "lofi",
        "expect_top_mood": "chill",
        "min_confidence": 65,
        "expect_warnings": False,
    },
    {
        "name": "Rock / intense / high energy",
        "profile": {"genre": "rock", "mood": "intense", "energy": 0.90, "likes_acoustic": False,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "rock",
        "expect_top_mood": "intense",
        "min_confidence": 65,
        "expect_warnings": False,
    },
    {
        "name": "Jazz / relaxed / acoustic",
        "profile": {"genre": "jazz", "mood": "relaxed", "energy": 0.37, "likes_acoustic": True,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "jazz",
        "expect_top_mood": "relaxed",
        "min_confidence": 55,
        "expect_warnings": False,
    },
    {
        "name": "EDGE — Missing genre (classical)",
        "profile": {"genre": "classical", "mood": "relaxed", "energy": 0.35, "likes_acoustic": True,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": None,    # any genre is acceptable
        "expect_top_mood": None,
        "min_confidence": 0,
        "expect_warnings": True,     # guardrail must fire
    },
    {
        "name": "EDGE — Missing mood (sad)",
        "profile": {"genre": "rock", "mood": "sad", "energy": 0.88, "likes_acoustic": False,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "rock",
        "expect_top_mood": None,
        "min_confidence": 30,
        "expect_warnings": True,
    },
    {
        "name": "EDGE — Contradiction: lofi + energy 0.95",
        "profile": {"genre": "lofi", "mood": "chill", "energy": 0.95, "likes_acoustic": False,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_genre": "lofi",  # genre weight still wins
        "expect_top_mood": None,
        "min_confidence": 0,
        "expect_warnings": True,
    },
    {
        "name": "Regression — same input yields same #1 result",
        "profile": {"genre": "pop", "mood": "happy", "energy": 0.80, "likes_acoustic": False,
                    "prefers_popular": False, "target_decade": "", "mood_tags": []},
        "expect_top_title": "Sunrise City",   # deterministic — must always be this
        "min_confidence": 60,
        "expect_warnings": False,
    },
    {
        "name": "Guardrail — empty raw input blocked",
        "raw_input": "",
        "expect_blocked": True,
    },
    {
        "name": "Guardrail — valid short input passes",
        "raw_input": "chill lofi",
        "expect_blocked": False,
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_harness(songs: list) -> tuple[int, int, float]:
    passed = 0
    failed = 0
    confidences: list[float] = []
    rows: list[tuple[str, str, str]] = []

    for case in TEST_CASES:
        name = case["name"]

        # Raw input guardrail cases (no scoring)
        if "raw_input" in case:
            ok, _ = validate_input(case["raw_input"])
            blocked = not ok
            expected_blocked = case["expect_blocked"]
            success = blocked == expected_blocked
            status = "PASS" if success else "FAIL"
            detail = (
                f"input {'blocked' if blocked else 'allowed'} "
                f"(expected {'blocked' if expected_blocked else 'allowed'})"
            )
            rows.append((name, status, detail))
            passed += success
            failed += (not success)
            continue

        # Profile-based scoring cases
        profile = dict(case["profile"])
        warnings = validate_profile(profile)
        results = recommend_songs(profile, songs, k=5, mode=BALANCED)

        if not results:
            rows.append((name, "FAIL", "no results returned"))
            failed += 1
            continue

        top_song, top_score, _ = results[0]
        confidence = round((top_score / MAX_SCORE) * 100, 1)
        confidences.append(confidence)

        checks: list[str] = []
        ok = True

        # Check expected genre
        if case.get("expect_top_genre"):
            match = top_song["genre"] == case["expect_top_genre"]
            checks.append(f"genre={'✓' if match else '✗'}")
            ok = ok and match

        # Check expected mood
        if case.get("expect_top_mood"):
            match = top_song["mood"] == case["expect_top_mood"]
            checks.append(f"mood={'✓' if match else '✗'}")
            ok = ok and match

        # Check expected title (regression test)
        if case.get("expect_top_title"):
            match = top_song["title"] == case["expect_top_title"]
            checks.append(f"title={'✓' if match else '✗ (got '+top_song['title']+')'}")
            ok = ok and match

        # Check confidence floor
        min_conf = case.get("min_confidence", 0)
        conf_ok = confidence >= min_conf
        checks.append(f"conf={confidence}%{'✓' if conf_ok else '✗(min '+str(min_conf)+'%)'}")
        ok = ok and conf_ok

        # Check warnings fired (or didn't)
        if "expect_warnings" in case:
            fired = len(warnings) > 0
            expected = case["expect_warnings"]
            warn_ok = fired == expected
            checks.append(f"warnings={'✓' if warn_ok else '✗'}")
            ok = ok and warn_ok

        status = "PASS" if ok else "FAIL"
        passed += ok
        failed += (not ok)
        rows.append((name, status, "  |  ".join(checks)))

    # Print report
    avg_conf = round(sum(confidences) / len(confidences), 1) if confidences else 0.0

    print(f"\n{'═' * _W}")
    print(f"  VIBEFINDER AI — EVALUATION HARNESS")
    print(f"{'═' * _W}")
    for name, status, detail in rows:
        icon = "✅" if status == "PASS" else "❌"
        print(f"\n  {icon}  {name}")
        print(f"       {detail}")

    print(f"\n{'═' * _W}")
    print(
        f"  RESULT: {passed}/{len(TEST_CASES)} passed  |  "
        f"avg confidence: {avg_conf}%  |  failed: {failed}"
    )
    print(f"{'═' * _W}\n")

    return passed, failed, avg_conf


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _songs = load_songs("data/songs.csv")
    passed, failed, _ = run_harness(_songs)
    sys.exit(0 if failed == 0 else 1)
