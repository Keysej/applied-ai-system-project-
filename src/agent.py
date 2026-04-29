"""
VibeFinder Multi-Step Music Agent

Implements an agentic workflow with 6 observable reasoning steps:

  Step 1 — Analyze   : Claude reads the initial query and identifies what
                        information is clear vs. missing.
  Step 2 — Ask       : Claude asks ONE targeted clarifying question.
  Step 3 — Build     : Claude synthesizes the full conversation into a
                        structured UserProfile JSON.
  Step 4 — Score     : Deterministic recommender ranks all catalog songs.
  Step 5 — Evaluate  : Claude rates result quality (1–10) and decides
                        whether the profile needs refinement.
  Step 6 — Explain   : Claude writes a grounded natural-language summary.

Every step prints a visible header so the reasoning chain is fully observable.
"""

import json
import os
import re

from google import genai
from google.genai import types

from .ai_interface import generate_explanation, load_genre_guide
from .guardrails import validate_profile
from .recommender import BALANCED, recommend_songs

_W = 64   # output width

_AGENT_SYSTEM = """You are a music taste analyst running a structured recommendation pipeline.
You will receive a conversation transcript and a specific instruction for each step.
Follow each step instruction precisely. Output only what the step asks for — no extra commentary.

Available genres: ["pop","lofi","rock","ambient","jazz","electronic","folk","indie pop","r&b","hip-hop","country","synthwave"]
Available moods:  ["happy","chill","intense","focused","relaxed","moody"]"""


def _step_header(n: int, label: str) -> None:
    pad = "─" * max(0, _W - len(label) - 12)
    print(f"\n  ── Step {n}: {label} {pad}")


_FALLBACK_RESPONSES = [
    "The genre and energy level are clear; the mood could be more specific.",
    "What energy level are you looking for — calm and low-key, or high and intense?",
    '{"genre": "pop", "mood": "happy", "energy": 0.70, "likes_acoustic": false}',
    None,  # Step 4 is deterministic — no AI response needed
    "Quality: 7/10 — Results match the general vibe but mood specificity could improve.",
    None,  # Step 6 uses generate_explanation directly
]


def _claude(history: list[dict], max_tokens: int = 300) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Count how many assistant turns exist to pick the right fallback
        step = sum(1 for m in history if m["role"] == "assistant")
        return _FALLBACK_RESPONSES[min(step, len(_FALLBACK_RESPONSES) - 1)] or ""
    client = genai.Client(api_key=api_key)
    gemini_history = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in history[:-1]
    ]
    chat = client.chats.create(
        model="gemini-1.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=_AGENT_SYSTEM,
            max_output_tokens=max_tokens,
        ),
        history=gemini_history,
    )
    response = chat.send_message(history[-1]["content"])
    return response.text.strip()


def _add(history: list[dict], role: str, content: str) -> None:
    history.append({"role": role, "content": content})


class MusicAgent:
    """Six-step music recommendation agent with fully observable reasoning."""

    def __init__(self, songs: list[dict], genre_guide: str = ""):
        self.songs = songs
        self.genre_guide = genre_guide or load_genre_guide()

    def run(self, initial_query: str) -> list:
        """Run the full agentic pipeline for a given user query.

        Prints each reasoning step as it executes.
        Returns the final list of (song, score, reasons) tuples.
        """
        history: list[dict] = []
        print(f"\n{'═' * _W}")
        print(f"  🎵 VibeFinder Agent")
        print(f"  Query: \"{initial_query}\"")
        print(f"{'═' * _W}")

        # ── Step 1: Analyze ──────────────────────────────────────────────────
        _step_header(1, "Analyzing request")
        _add(history, "user", (
            f"User query: \"{initial_query}\"\n\n"
            "In one sentence: state which musical preferences are already clear "
            "from this query, and which single piece of information would most "
            "improve the recommendation."
        ))
        analysis = _claude(history)
        _add(history, "assistant", analysis)
        print(f"     {analysis}")

        # ── Step 2: Ask ───────────────────────────────────────────────────────
        _step_header(2, "Asking clarifying question")
        _add(history, "user", (
            "Write ONE short, friendly question to fill the most important gap "
            "you identified. Just the question — no preamble."
        ))
        question = _claude(history)
        _add(history, "assistant", question)
        print(f"     Agent → {question}")

        try:
            clarification = input("     You   → ").strip() or "no preference"
        except (EOFError, KeyboardInterrupt):
            clarification = "no preference"
        _add(history, "user", f"User answered: \"{clarification}\"")

        # ── Step 3: Build UserProfile ─────────────────────────────────────────
        _step_header(3, "Building UserProfile from conversation")
        guide_hint = (
            f"\n\nDomain reference:\n{self.genre_guide[:800]}"
            if self.genre_guide else ""
        )
        _add(history, "user", (
            "Based on the full conversation above, extract a UserProfile. "
            "Return ONLY a JSON object with these exact keys:\n"
            '{"genre": "...", "mood": "...", "energy": 0.0, "likes_acoustic": false}'
            f"{guide_hint}"
        ))
        profile_raw = _claude(history)
        _add(history, "assistant", profile_raw)

        try:
            m = re.search(r"\{.*\}", profile_raw, re.DOTALL)
            profile: dict = json.loads(m.group() if m else profile_raw)
        except Exception:
            profile = {"genre": "pop", "mood": "happy", "energy": 0.6, "likes_acoustic": False}

        warnings = validate_profile(profile)
        print(f"     Profile: {profile}")
        for w in warnings:
            print(f"     ⚠  {w}")

        # ── Step 4: Score ─────────────────────────────────────────────────────
        _step_header(4, "Running deterministic recommender")
        results = recommend_songs(profile, self.songs, k=5, mode=BALANCED)
        if results:
            top_song, top_score, _ = results[0]
            print(f"     Top result : \"{top_song['title']}\"  score={top_score:.2f}")
            print(f"     Full top-5 : {[r[0]['title'] for r in results]}")
        else:
            print("     No results returned.")

        # ── Step 5: Evaluate quality ──────────────────────────────────────────
        _step_header(5, "Evaluating result quality")
        top3_text = "\n".join(
            f"  - {s['title']} | {s['genre']} | {s['mood']} | energy {s['energy']:.2f}"
            for s, _, _ in results[:3]
        )
        _add(history, "user", (
            f"The recommender returned these top results:\n{top3_text}\n\n"
            f"Profile used: {json.dumps(profile)}\n"
            f"Guardrail warnings: {warnings or 'none'}\n\n"
            "Rate the quality of this match on a scale of 1–10. "
            "Explain in ONE sentence whether the results satisfy the original request "
            "or if a different approach would help. "
            "Format exactly: 'Quality: X/10 — <reason>'"
        ))
        evaluation = _claude(history)
        _add(history, "assistant", evaluation)
        print(f"     {evaluation}")

        # ── Step 6: Generate explanation ──────────────────────────────────────
        _step_header(6, "Generating final explanation")
        top_dicts = [s for s, _, _ in results]
        try:
            explanation = generate_explanation(profile, top_dicts, warnings)
        except Exception as exc:
            explanation = f"(explanation unavailable: {exc})"
        print(f"     Done.\n")

        # ── Final output ──────────────────────────────────────────────────────
        print(f"\n{'─' * _W}")
        print(f"  Final Recommendations  (query: \"{initial_query}\")")
        print(f"{'─' * _W}")
        for i, (song, score, reasons) in enumerate(results, 1):
            reason_str = (
                ", ".join(reasons) if isinstance(reasons, list) else str(reasons)
            )
            print(f"  #{i}  {song['title']} by {song['artist']}")
            print(f"       Score {score:.2f}  |  {song['genre']} / {song['mood']}"
                  f"  |  energy {song['energy']:.2f}")
            print(f"       Why: {reason_str}")
        print(f"\n  AI Summary:\n  {explanation}")
        print(f"{'═' * _W}\n")

        return results
