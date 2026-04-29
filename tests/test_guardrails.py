"""
Tests for src/guardrails.py

Covers: input validation, missing genre/mood warnings,
        energy clamping, and contradiction detection.
"""

import pytest
from src.guardrails import validate_input, validate_profile


# ---------------------------------------------------------------------------
# validate_input
# ---------------------------------------------------------------------------

def test_empty_string_is_blocked():
    ok, err = validate_input("")
    assert not ok
    assert err != ""


def test_whitespace_only_is_blocked():
    ok, err = validate_input("   ")
    assert not ok
    assert err != ""


def test_too_short_input_is_blocked():
    ok, err = validate_input("hi")
    assert not ok
    assert err != ""


def test_too_long_input_is_blocked():
    ok, err = validate_input("a" * 501)
    assert not ok
    assert "long" in err.lower()


def test_valid_short_phrase_passes():
    ok, _ = validate_input("chill lofi")
    assert ok


def test_valid_sentence_passes():
    ok, _ = validate_input("something upbeat and happy for my workout")
    assert ok


# ---------------------------------------------------------------------------
# validate_profile — genre warnings
# ---------------------------------------------------------------------------

def test_genre_not_in_catalog_warns():
    warnings = validate_profile({"genre": "classical", "mood": "happy", "energy": 0.5, "likes_acoustic": False})
    assert any("classical" in w for w in warnings)


def test_valid_genre_no_genre_warning():
    warnings = validate_profile({"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": False})
    assert not any("genre" in w.lower() and "no songs" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_profile — mood warnings
# ---------------------------------------------------------------------------

def test_mood_not_in_catalog_warns():
    warnings = validate_profile({"genre": "pop", "mood": "sad", "energy": 0.5, "likes_acoustic": False})
    assert any("sad" in w for w in warnings)


def test_valid_mood_no_mood_warning():
    warnings = validate_profile({"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": False})
    assert not any("mood" in w.lower() and "no songs" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_profile — energy clamping
# ---------------------------------------------------------------------------

def test_energy_above_one_is_clamped():
    profile = {"genre": "pop", "mood": "happy", "energy": 1.5, "likes_acoustic": False}
    warnings = validate_profile(profile)
    assert profile["energy"] == 1.0
    assert any("clamped" in w for w in warnings)


def test_energy_below_zero_is_clamped():
    profile = {"genre": "pop", "mood": "happy", "energy": -0.3, "likes_acoustic": False}
    warnings = validate_profile(profile)
    assert profile["energy"] == 0.0
    assert any("clamped" in w for w in warnings)


def test_energy_in_range_not_clamped():
    profile = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    validate_profile(profile)
    assert profile["energy"] == 0.8


# ---------------------------------------------------------------------------
# validate_profile — contradiction detection
# ---------------------------------------------------------------------------

def test_lofi_high_energy_contradiction_warns():
    warnings = validate_profile({"genre": "lofi", "mood": "chill", "energy": 0.95, "likes_acoustic": False})
    assert any("Conflicting" in w for w in warnings)


def test_rock_high_energy_no_contradiction():
    warnings = validate_profile({"genre": "rock", "mood": "intense", "energy": 0.90, "likes_acoustic": False})
    assert not any("Conflicting" in w for w in warnings)


def test_ambient_high_energy_contradiction_warns():
    warnings = validate_profile({"genre": "ambient", "mood": "chill", "energy": 0.85, "likes_acoustic": False})
    assert any("Conflicting" in w for w in warnings)


# ---------------------------------------------------------------------------
# validate_profile — clean profile has no warnings
# ---------------------------------------------------------------------------

def test_fully_valid_profile_returns_no_warnings():
    warnings = validate_profile({
        "genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False,
    })
    assert warnings == []
