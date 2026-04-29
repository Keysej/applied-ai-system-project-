"""
VibeFinder AI — Specialization Comparison Script

Demonstrates that the few-shot specialized parser measurably outperforms
the zero-shot baseline on edge-case inputs: slang terms, artist names,
and activity descriptions.

Runs each test input through both parsers and scores how often each
returns the expected genre and mood.

Usage:
    python scripts/compare_baseline.py

Requires: ANTHROPIC_API_KEY environment variable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ai_interface import (
    load_genre_guide,
    parse_user_preferences,
    parse_user_preferences_baseline,
)

_W = 70

# ---------------------------------------------------------------------------
# Test cases — slang, artist names, and activity descriptions
# A zero-shot parser struggles with these; few-shot specialization handles them.
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "input": "lofi hip hop beats to study and relax to",
        "expected_genre": "lofi",
        "expected_mood": "focused",
    },
    {
        "input": "give me something like Billie Eilish but more upbeat",
        "expected_genre": "indie pop",
        "expected_mood": "happy",
    },
    {
        "input": "hype me up before the gym, heavy rap",
        "expected_genre": "hip-hop",
        "expected_mood": "intense",
    },
    {
        "input": "campfire acoustic vibes, nothing loud please",
        "expected_genre": "folk",
        "expected_mood": "relaxed",
    },
    {
        "input": "80s night drive, retro neon vibes",
        "expected_genre": "synthwave",
        "expected_mood": "moody",
    },
    {
        "input": "smooth jazz for a Sunday morning coffee",
        "expected_genre": "jazz",
        "expected_mood": "relaxed",
    },
    {
        "input": "something for the dancefloor, heavy EDM",
        "expected_genre": "electronic",
        "expected_mood": "intense",
    },
    {
        "input": "coffee shop background music, nothing distracting",
        "expected_genre": "jazz",
        "expected_mood": "relaxed",
    },
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def score_result(result: dict, expected_genre: str, expected_mood: str) -> tuple[bool, bool]:
    genre_ok = result.get("genre", "").lower() == expected_genre.lower()
    mood_ok  = result.get("mood",  "").lower() == expected_mood.lower()
    return genre_ok, mood_ok


def run_comparison() -> None:
    guide = load_genre_guide()

    baseline_genre_hits  = 0
    baseline_mood_hits   = 0
    specialized_genre_hits = 0
    specialized_mood_hits  = 0
    n = len(TEST_CASES)

    print(f"\n{'═' * _W}")
    print("  VIBEFINDER AI — SPECIALIZATION COMPARISON")
    print("  Baseline (zero-shot)  vs  Specialized (few-shot + genre guide)")
    print(f"{'═' * _W}")

    for i, case in enumerate(TEST_CASES, 1):
        user_input = case["input"]
        exp_genre  = case["expected_genre"]
        exp_mood   = case["expected_mood"]

        print(f"\n  [{i}/{n}] \"{user_input}\"")
        print(f"   Expected: genre={exp_genre}  mood={exp_mood}")

        # Baseline (zero-shot, no guide, no few-shot)
        try:
            base = parse_user_preferences_baseline(user_input)
            b_genre_ok, b_mood_ok = score_result(base, exp_genre, exp_mood)
        except Exception as e:
            base = {}
            b_genre_ok = b_mood_ok = False
            print(f"   Baseline  ERROR: {e}")

        baseline_genre_hits += b_genre_ok
        baseline_mood_hits  += b_mood_ok

        # Specialized (few-shot + genre guide)
        try:
            spec = parse_user_preferences(user_input, guide)
            s_genre_ok, s_mood_ok = score_result(spec, exp_genre, exp_mood)
        except Exception as e:
            spec = {}
            s_genre_ok = s_mood_ok = False
            print(f"   Specialized ERROR: {e}")

        specialized_genre_hits += s_genre_ok
        specialized_mood_hits  += s_mood_ok

        b_icon = "✓" if b_genre_ok else "✗"
        s_icon = "✓" if s_genre_ok else "✗"
        b_mood_icon = "✓" if b_mood_ok else "✗"
        s_mood_icon = "✓" if s_mood_ok else "✗"

        print(f"   Baseline    → genre={base.get('genre','?')} {b_icon}  "
              f"mood={base.get('mood','?')} {b_mood_icon}  "
              f"energy={base.get('energy','?')}")
        print(f"   Specialized → genre={spec.get('genre','?')} {s_icon}  "
              f"mood={spec.get('mood','?')} {s_mood_icon}  "
              f"energy={spec.get('energy','?')}")

    # Summary
    b_genre_pct  = round(baseline_genre_hits    / n * 100)
    b_mood_pct   = round(baseline_mood_hits      / n * 100)
    s_genre_pct  = round(specialized_genre_hits  / n * 100)
    s_mood_pct   = round(specialized_mood_hits   / n * 100)

    print(f"\n{'═' * _W}")
    print("  SUMMARY")
    print(f"{'─' * _W}")
    print(f"  {'Metric':<28}  {'Baseline':>10}  {'Specialized':>12}  {'Improvement':>12}")
    print(f"  {'─'*28}  {'─'*10}  {'─'*12}  {'─'*12}")
    print(f"  {'Genre accuracy':<28}  {b_genre_pct:>9}%  {s_genre_pct:>11}%  "
          f"  {s_genre_pct - b_genre_pct:>+10}pp")
    print(f"  {'Mood accuracy':<28}  {b_mood_pct:>9}%  {s_mood_pct:>11}%  "
          f"  {s_mood_pct - b_mood_pct:>+10}pp")
    print(f"{'═' * _W}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    run_comparison()
