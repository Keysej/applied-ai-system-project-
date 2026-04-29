"""
Input validation and bias-detection guardrails for VibeFinder AI.

Two public functions:
  validate_input(text)     -> (ok: bool, error: str)
  validate_profile(profile) -> warnings: list[str]
"""

VALID_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "electronic",
    "folk", "indie pop", "r&b", "hip-hop", "country", "synthwave",
}

VALID_MOODS = {"happy", "chill", "intense", "focused", "relaxed", "moody"}

# Typical energy ranges observed in the catalog per genre.
# Used to detect contradictory preferences (e.g. lofi + energy 0.95).
_GENRE_ENERGY_RANGES: dict[str, tuple[float, float]] = {
    "lofi":       (0.22, 0.50),
    "ambient":    (0.10, 0.40),
    "jazz":       (0.30, 0.65),
    "folk":       (0.25, 0.55),
    "rock":       (0.65, 1.00),
    "electronic": (0.65, 1.00),
    "hip-hop":    (0.60, 0.95),
    "synthwave":  (0.55, 0.90),
}

_TOLERANCE = 0.15   # how far outside a genre's typical range before we warn


def validate_input(text: str) -> tuple[bool, str]:
    """Check that raw user text is usable before sending it to Claude.

    Returns (True, "") if valid, or (False, human-readable error) if not.
    """
    if not text or not text.strip():
        return False, "Input cannot be empty. Please describe what you're in the mood for."
    if len(text.strip()) < 4:
        return False, "Input too short. Try something like 'chill lofi to study to'."
    if len(text) > 500:
        return False, "Input too long (max 500 characters). Please be more concise."
    return True, ""


def validate_profile(profile: dict) -> list[str]:
    """Validate a parsed UserProfile dict and return a list of warning strings.

    Warnings are informational — the system still runs, but the user is told
    which preferences could not be honoured and why.

    Side-effect: clamps profile['energy'] to [0, 1] if out of range.
    """
    warnings: list[str] = []
    genre  = profile.get("genre", "")
    mood   = profile.get("mood", "")
    energy = float(profile.get("energy", 0.5))

    # 1. Genre not in catalog
    if genre not in VALID_GENRES:
        warnings.append(
            f"Genre '{genre}' has no songs in the catalog — genre score will be 0 "
            f"for all results. Suggestions are based on mood and energy only."
        )

    # 2. Mood not in catalog
    if mood not in VALID_MOODS:
        warnings.append(
            f"Mood '{mood}' has no songs in the catalog — mood score will be 0 "
            f"for all results."
        )

    # 3. Energy out of [0, 1] — clamp silently but warn
    if not 0.0 <= energy <= 1.0:
        clamped = max(0.0, min(1.0, energy))
        profile["energy"] = clamped
        warnings.append(
            f"Energy {energy:.2f} is outside [0, 1] and has been clamped to {clamped:.2f}."
        )
        energy = clamped

    # 4. Contradictory genre + energy combination
    if genre in _GENRE_ENERGY_RANGES:
        lo, hi = _GENRE_ENERGY_RANGES[genre]
        if energy < lo - _TOLERANCE or energy > hi + _TOLERANCE:
            warnings.append(
                f"Conflicting preferences: '{genre}' songs in the catalog typically "
                f"have energy {lo:.2f}–{hi:.2f}, but your target is {energy:.2f}. "
                f"Genre and energy signals will fight each other — results may feel off."
            )

    return warnings
