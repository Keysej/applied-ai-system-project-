"""
Tests for src/ai_interface.py

Claude API calls are mocked so these tests run without an API key.
They verify that our code correctly processes Claude's responses
and handles errors gracefully.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ai_interface import parse_user_preferences, generate_explanation


# ---------------------------------------------------------------------------
# Helpers: build a fake Anthropic response object
# ---------------------------------------------------------------------------

def _mock_response(text: str) -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


# ---------------------------------------------------------------------------
# parse_user_preferences
# ---------------------------------------------------------------------------

VALID_PROFILE_JSON = json.dumps({
    "genre": "lofi",
    "mood": "chill",
    "energy": 0.38,
    "likes_acoustic": True,
})


@patch("src.ai_interface.anthropic.Anthropic")
def test_parse_returns_dict_with_required_keys(mock_anthropic_cls):
    mock_anthropic_cls.return_value.messages.create.return_value = _mock_response(VALID_PROFILE_JSON)

    result = parse_user_preferences("something chill to study to")

    assert isinstance(result, dict)
    for key in ("genre", "mood", "energy", "likes_acoustic"):
        assert key in result, f"Missing key: {key}"


@patch("src.ai_interface.anthropic.Anthropic")
def test_parse_energy_is_float(mock_anthropic_cls):
    mock_anthropic_cls.return_value.messages.create.return_value = _mock_response(VALID_PROFILE_JSON)

    result = parse_user_preferences("chill vibes")

    assert isinstance(result["energy"], float)
    assert 0.0 <= result["energy"] <= 1.0


@patch("src.ai_interface.anthropic.Anthropic")
def test_parse_likes_acoustic_is_bool(mock_anthropic_cls):
    mock_anthropic_cls.return_value.messages.create.return_value = _mock_response(VALID_PROFILE_JSON)

    result = parse_user_preferences("acoustic folk please")

    assert isinstance(result["likes_acoustic"], bool)


@patch("src.ai_interface.anthropic.Anthropic")
def test_parse_raises_on_invalid_json(mock_anthropic_cls):
    mock_anthropic_cls.return_value.messages.create.return_value = _mock_response("not valid json at all")

    with pytest.raises(json.JSONDecodeError):
        parse_user_preferences("some input")


@patch("src.ai_interface.anthropic.Anthropic")
def test_parse_calls_claude_once(mock_anthropic_cls):
    mock_instance = mock_anthropic_cls.return_value
    mock_instance.messages.create.return_value = _mock_response(VALID_PROFILE_JSON)

    parse_user_preferences("upbeat pop")

    mock_instance.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# generate_explanation
# ---------------------------------------------------------------------------

SAMPLE_SONGS = [
    {
        "title": "Sunrise City", "artist": "Neon Echo",
        "genre": "pop", "mood": "happy",
        "energy": 0.82, "acousticness": 0.18,
    },
    {
        "title": "Library Rain", "artist": "Paper Lanterns",
        "genre": "lofi", "mood": "chill",
        "energy": 0.35, "acousticness": 0.86,
    },
]

SAMPLE_PROFILE = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}


@patch("src.ai_interface.anthropic.Anthropic")
def test_explanation_returns_non_empty_string(mock_anthropic_cls):
    mock_anthropic_cls.return_value.messages.create.return_value = _mock_response(
        "These songs match your upbeat pop energy perfectly."
    )

    result = generate_explanation(SAMPLE_PROFILE, SAMPLE_SONGS, warnings=[])

    assert isinstance(result, str)
    assert result.strip() != ""


@patch("src.ai_interface.anthropic.Anthropic")
def test_explanation_passes_warnings_to_claude(mock_anthropic_cls):
    mock_instance = mock_anthropic_cls.return_value
    mock_instance.messages.create.return_value = _mock_response("Here are your results.")

    generate_explanation(
        SAMPLE_PROFILE,
        SAMPLE_SONGS,
        warnings=["Genre 'classical' has no songs in the catalog."],
    )

    call_kwargs = mock_instance.messages.create.call_args
    user_message = call_kwargs.kwargs["messages"][0]["content"]
    assert "classical" in user_message


@patch("src.ai_interface.anthropic.Anthropic")
def test_explanation_calls_claude_once(mock_anthropic_cls):
    mock_instance = mock_anthropic_cls.return_value
    mock_instance.messages.create.return_value = _mock_response("Great picks!")

    generate_explanation(SAMPLE_PROFILE, SAMPLE_SONGS, warnings=[])

    mock_instance.messages.create.assert_called_once()
