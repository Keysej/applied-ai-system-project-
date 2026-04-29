# VibeFinder AI — Full 7-Minute Presentation Script
## Word-for-Word What To Say + Step-by-Step What To Do

---

## BEFORE YOU START — Setup Checklist

Do these things BEFORE walking to the front of the room:

- [ ] Open terminal, navigate to the project:
      `cd /Users/jimalekeyse/applied-ai-system-project`
- [ ] Make sure your virtual environment is active:
      `source .venv/bin/activate`
- [ ] Have this command ready but NOT run yet:
      `python scripts/eval_harness.py`
- [ ] Have this command ready but NOT run yet:
      `python -m src.main --interactive`
- [ ] Open your GitHub repo in a browser tab:
      https://github.com/Keysej/applied-ai-system-project-
- [ ] Open your slides and go to Slide 1
- [ ] Take a breath. You built this. You know it inside and out.

---

## SLIDE 1 — Title
### ⏱ 0:00 – 0:20

**Do this:** Stand at the front. Pull up Slide 1. Look at the audience.

**Say this:**

> "Hi everyone. My name is Jimale, and my project is called VibeFinder AI.
> It's a music recommendation system that I extended from my Module 3 project —
> one that now lets you describe what you're in the mood for in plain English,
> and uses Claude AI to find the right songs.
> Let me show you the problem it solves."

**Then:** Click to Slide 2.

---

## SLIDE 2 — The Problem
### ⏱ 0:20 – 1:20

**Do this:** Stay on Slide 2. No demo yet. Just talk.

**Say this:**

> "This started as my Module 3 project — a music recommender I built from scratch.
> It worked. You gave it a genre, a mood, and an energy level between 0 and 1,
> and it ranked songs by score.
>
> But it had two real problems.
>
> First — nobody talks like that. Real people don't say 'energy equals 0.8.'
> They say 'I need something to study to' or 'hype me up before the gym.'
>
> Second — and this was the more dangerous problem —
> if you asked for something the system didn't understand,
> like the mood 'sad' or a genre like 'classical' that wasn't in my catalog,
> it would silently ignore you.
> It would return results anyway. No warning. No explanation.
> You would never know your preference was dropped.
>
> That silent failure is what I set out to fix.
> The question was: how do you make a rigid algorithm
> actually understand a human being —
> without losing the transparency that makes it trustworthy?"

**Then:** Click to Slide 3.

---

## SLIDE 3 — The Logic: How the AI Thinks
### ⏱ 1:20 – 3:00

**Do this:** Stay on Slide 3. Point to the data flow diagram as you name each layer.

**Say this:**

> "My solution has four layers working together.
>
> Layer one — Guardrails.
> Before anything touches Claude, raw input is validated.
> Empty input is blocked outright.
> And if your preferences contradict each other —
> like asking for lofi music at 95% energy, which is physically impossible
> in my catalog — the system surfaces a visible warning
> instead of hiding it.
>
> Layer two — the RAG pipeline. Retrieval Augmented Generation.
> Claude doesn't guess genres from thin air.
> Before it parses your text, it reads two documents.
> The first is the song catalog vocabulary — the genres and moods that actually exist.
> The second is a genre guide I wrote myself,
> which maps slang terms, artist names, and activities to real genres.
> 'Study beats' maps to lofi.
> 'Something like Billie Eilish' maps to indie pop.
> '80s night drive' maps to synthwave.
> That's retrieval — every answer is grounded in real data, not invented.
>
> Layer three — the deterministic scorer.
> This is the original Module 3 algorithm, completely untouched.
> Genre match, mood match, energy closeness, acoustic preference —
> every single point is traceable back to a specific rule.
> Claude does NOT rank the songs. Math does.
> That's an intentional design decision I'll come back to.
>
> Layer four — the explainer.
> Claude receives the actual top five song rows as context
> and writes a natural language explanation.
> Every sentence is anchored to real data.
>
> And for the stretch features —
> I also built an agentic mode with six observable steps.
> The agent analyzes your request, asks you one clarifying question,
> builds your profile from the conversation,
> runs the scorer, then rates its own result quality
> on a scale of one to ten before generating the final explanation.
> You can watch every reasoning step happen in the terminal."

**Then:** Click to Slide 4.

---

## SLIDE 4 — Live Demo
### ⏱ 3:00 – 4:30

**Do this:** Switch from slides to your terminal. This is the strongest part of your presentation.

**Say this:**

> "Let me show you the system running."

**Step 1 — Run the eval harness:**

Type and run:
```
python scripts/eval_harness.py
```

Wait for it to finish. Let the audience read the output for 3–4 seconds. Then say:

> "This is my evaluation harness —
> it runs 10 predefined test cases including standard profiles,
> edge cases with missing genres, and adversarial inputs like contradictory preferences.
> It prints a confidence score for each case.
> 10 out of 10 passing. Average confidence 65.6%."

**Step 2 — Run the interactive mode:**

Type and run:
```
python -m src.main --interactive
```

When the prompt appears, type:
```
something chill to study to, not too loud
```

Wait for the output. Let the audience read the recommendations and the AI summary. Then say:

> "The system parsed 'something chill to study to' into
> genre lofi, mood focused, low energy.
> It ran the scorer, returned the top five songs,
> and Claude wrote that explanation using the actual song data —
> not a template.
>
> Now watch what happens with a request the system can't fully satisfy."

Type:
```
sad classical music, very quiet
```

Wait for the output with the guardrail warnings. Then say:

> "Two warnings fired — 'classical' and 'sad' have no songs in my catalog.
> The system still returns results, but it tells you exactly why
> they might not feel right.
> That's the silent failure from Module 3, fixed."

Type `quit` to exit. Switch back to slides.

**Then:** Click to Slide 5.

---

## SLIDE 5 — The Reliability
### ⏱ 4:30 – 5:30

**Do this:** Stay on Slide 5. Talk through the three reliability layers.

**Say this:**

> "Behind what you just saw are three layers of reliability.
>
> First — 36 automated pytest tests across three files.
> Scoring logic, guardrail behavior, and Claude output structure.
> All mocked — no API key required — so anyone can run them.
> 36 out of 36 passing.
>
> Second — the evaluation harness you just watched.
> It runs without Claude. It tests the deterministic layers only.
> Anyone can clone the repo and run it in under a minute.
>
> Third — a specialization comparison script
> that calls Claude twice on the same tricky inputs —
> once with a zero-shot baseline prompt,
> once with my few-shot specialized prompt —
> and prints a side-by-side accuracy table
> showing the measurable improvement.
>
> The key design principle behind all of this:
> I test the AI layer and the algorithm layer separately.
> When something breaks, I know exactly which layer to look at."

**Then:** Click to Slide 6.

---

## SLIDE 6 — The Reflection
### ⏱ 5:30 – 6:30

**Do this:** Stay on Slide 6. Slow down a little here — this is the part people remember.

**Say this:**

> "The biggest surprise in this project wasn't the code.
> It was the guardrails.
>
> Building the warning system forced me to think about failure modes
> before they happened.
> Every 'what if' question —
> what if the genre doesn't exist,
> what if the preferences contradict each other,
> what if the user's input is empty —
> had to become a concrete check in the code.
> That's a different skill than building what the system can do.
> It's building for what it can't.
>
> The other thing that surprised me:
> Claude is an interface, not a decision-maker.
> It handles the language.
> The algorithm handles the decisions.
>
> Keeping those two things separate made the system
> more reliable, more debuggable, and easier to explain to someone else.
> I can point to any score and tell you exactly why it is what it is.
> That traceability is what makes it trustworthy.
>
> That's the most important thing I'm taking from this project —
> and it's the principle I want to carry into every AI system I build."

**Then:** Click to Slide 7.

---

## SLIDE 7 — Wrap-Up
### ⏱ 6:30 – 6:45

**Do this:** Show the GitHub repo in the browser tab you have open.

**Say this:**

> "The full system is live on GitHub.
> It has 36 passing tests, a working eval harness,
> an agentic mode, a few-shot specialization comparison script,
> and a portfolio README.
>
> I'm happy to answer questions or run a live demo of the agent mode if there's time.
> Thank you."

**Then:** Stop talking. Smile. You're done.

---

## Q&A — Say These If Asked

**Q: Why didn't you let Claude rank the songs?**

> "Because then I can't explain a single score.
> The algorithm gives me full traceability —
> I can tell you exactly why Song A beat Song B by 0.3 points.
> Claude can't do that reliably.
> The math is the decision layer. Claude is the language layer."

---

**Q: How does RAG actually make it better than just prompting Claude normally?**

> "Without retrieval, Claude sometimes invents genres or misreads slang.
> With the genre guide loaded as context, it picks from a known vocabulary.
> I have a comparison script that proves this concretely —
> genre accuracy goes up measurably when the guide is included."

---

**Q: What is the filter bubble problem and does your system fix it?**

> "Because genre carries the most scoring weight,
> users tend to get their favorite genre back every time.
> My system warns you when that's happening, but doesn't fully fix it.
> The real fix is a diversity injection mode —
> intentionally swapping one result for something unexpected.
> I documented it in the model card as a future improvement."

---

**Q: Could this work on a real catalog with thousands of songs?**

> "The scoring algorithm scales fine — it's just a loop.
> The bigger issue is that the weights were calibrated on 20 songs,
> so they'd need recalibration at scale.
> I'd also replace exact string matching with embedding similarity
> so 'indie pop' and 'pop' are treated as adjacent genres, not completely different."

---

**Q: What would you build next?**

> "Three things.
> Expand the catalog to at least 200 songs.
> Add a feedback loop — after you see results you can say 'too slow'
> and the system re-scores with adjusted weights.
> And a Streamlit UI so anyone can use it without a terminal."

---

## FULL TIMING GUIDE

| Slide | Content | Time | Running Total |
|---|---|---|---|
| 1 — Title | Introduce yourself | 0:20 | 0:20 |
| 2 — Problem | Form input + silent failures | 1:00 | 1:20 |
| 3 — Logic | Four layers + architecture | 1:40 | 3:00 |
| 4 — Live Demo | Harness + interactive + guardrail | 1:30 | 4:30 |
| 5 — Reliability | Tests + harness + comparison | 1:00 | 5:30 |
| 6 — Reflection | Guardrails insight + Claude as interface | 1:00 | 6:30 |
| 7 — Wrap-up | GitHub + thank you | 0:15 | 6:45 |

15 seconds of buffer. **Do not skip the live demo on Slide 4 — that is your strongest moment.**

---

## LOOM RECORDING — What To Show

When you record your Loom walkthrough, follow this order:

1. Show the GitHub repo and README (30 seconds)
2. Run `pytest` — show 36/36 passing (30 seconds)
3. Run `python scripts/eval_harness.py` — show 10/10 (30 seconds)
4. Run `python -m src.main --interactive` with a clean request (45 seconds)
5. Run it again with a missing genre request to show the guardrail warning (45 seconds)
6. Optional: run `python -m src.main --agent` and show one full agentic loop (60 seconds)
7. Close on the model card / README reflection (30 seconds)

Target: 4–5 minutes for the Loom. Paste the link into the Portfolio Artifact section of your README when done.
