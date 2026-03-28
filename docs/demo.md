# ARIA Demo Script + Pitch

## Before you go up

- [ ] Pi 5 running backend (`python main.py`)
- [ ] Chromium open fullscreen on Pi screen at `http://localhost:8000`
- [ ] AirPods paired and connected to Pi 5
- [ ] Pendant charged and connected (green/blue idle glow)
- [ ] Pre-loaded transcript: at least 1-2 hours of hackathon ambient data
- [ ] Voice clone active (ELEVENLABS_VOICE_ID set in .env)
- [ ] Rehearsed this script 3+ times

---

## The Demo (60-90 seconds)

**[Step 1 — the reveal]**

> "This is ARIA. It's a personal AI you wear. We've been wearing it all hackathon — it's been listening."

*Hold up the pendant. Show the glow. Let people look.*

**[Step 2 — memory demo]**

Press button. Speak:

> "ARIA, who am I and what have I been working on?"

Wait for response in AirPods + room speaker.

*ARIA answers with the user's name, project, team — drawn from ambient transcript + stored memories.*

**[Step 3 — tool use demo]**

Press button. Speak:

> "ARIA, search the web — how much did the Humane AI Pin raise in funding?"

Wait. ARIA searches and answers:

*"Humane raised $230 million. Their pin was discontinued and sold to HP. You're building something better for about £30."*

**[Step 4 — show the tech]**

Point at the Pi 5 screen showing the live transcript.

> "Everything it hears, it remembers. Every conversation. Every decision. You can query any of it, any time."

**[Step 5 — the kicker]**

Hold up the pendant.

> "Open source. Runs on £30 of hardware. No subscription. No data leaving your own network. Your memories, owned by you."

> "We built this in 24 hours. Imagine 6 months."

---

## Handling Judge Questions

**"This already exists — Tab AI, Plaud Note, Limitless Pendant"**
> "Those products cost £150-300, require subscriptions, and send all your data to their servers. ARIA is open source, runs locally, and costs £30 in parts. The market exists — the right execution didn't."

**"Privacy concerns — it records everything?"**
> "Three safeguards: first, the button is push-to-talk so ARIA only processes what you deliberately share. Second, all speech processing runs on your own Raspberry Pi — nothing goes to a third-party server except the Claude API query text, which is already how you'd use Claude on your phone. Third, there's a physical kill switch — unplug the pendant."

**"How's it different from just using Siri?"**
> "Siri forgets everything the moment you close the app. ARIA accumulates memory over time — the longer you use it, the more it knows you. It's also agentic: it can take real actions — search the web, set reminders, summarise your day. And it runs on your own hardware."

**"Does it work reliably?"**
> "We've been running it for [X] hours. The transcript you can see on screen is real from today. Every query we've demoed has worked." *(Do not over-promise — show what you have.)*

---

## The 30-Second Pitch

> "Every AI assistant forgets you the moment you close the app. Your data lives on someone else's servers. Humane raised $230 million and failed. Rabbit raised $180 million. Tab AI, Plaud, Limitless — all funded, none nailed it.
>
> We think we know why: they built hardware looking for a use case. We built the use case first.
>
> ARIA is the AI you wear. It learns who you are. It remembers your life. It takes real actions. It runs on your own hardware for £30 with no subscription.
>
> We built this in 24 hours. Imagine 6 months."
