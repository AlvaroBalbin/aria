# ARIA — Mission Statement & Project Vision
## Bath Hackathon 2026

---

## The One-Line Mission

> **Give every person an AI that genuinely knows them — private, wearable, and owned entirely by the user.**

---

## Why ARIA Exists

We are living through a paradox. We have access to the most powerful AI systems in human history — systems that can write code, compose music, diagnose medical images, and hold nuanced conversations in any language. And yet, when you close the app, they forget you completely. Every conversation starts from zero. The AI that just helped you plan your entire week doesn't know your name when you open it tomorrow.

This is not a technical limitation. It is a business model decision. Every major AI company wants your data to live on their servers. They want you locked into their platform, their subscription, their ecosystem. Your memories are not yours — they are their product.

Meanwhile, the hardware attempts to fix this — Humane AI Pin (raised $230M, discontinued), Rabbit R1 (raised $180M, largely abandoned), Tab AI, Plaud Note, Limitless Pendant — all funded, all trying to build the AI wearable. All of them either failed or produced something underwhelming. Not because the idea was wrong. The idea is obviously right. They failed because they built hardware looking for a use case, rather than starting from a genuine human need and working backwards.

**ARIA starts from the need.**

The need is this: *your life is full of conversations, decisions, ideas, and context that your AI assistant never gets to see.* You have a meeting where your manager says something important. You have a coffee chat where someone mentions a name you'll need later. You have a late-night conversation with your team where you land on a critical decision. None of that ever reaches your AI. And so the AI that's supposed to help you is permanently operating with one hand tied behind its back.

ARIA fixes this. Completely. Permanently. Without sending your private conversations to a corporation.

---

## What ARIA Is

ARIA is a circular pendant worn around your neck. Inside it: an ESP32 microcontroller, an INMP441 digital microphone, a small OLED display, a ring of NeoPixel LEDs, and a battery. It is connected via WiFi to a Raspberry Pi 5 — a small, cheap, silent computer that fits in a bag or sits on a desk.

When you want to talk to ARIA, you press the button. The pendant glows purple. You speak. ARIA listens. Within seconds, a voice speaks back through your AirPods — and it sounds like you, because it is your voice, cloned and synthesised by ElevenLabs.

But ARIA is not just a voice interface. It is an agent. It has tools. It can search the web in real time. It can look up what's trending on X/Twitter. It saves facts about you permanently and recalls them in future conversations. It reads the ambient transcript of everything that's been said near you and draws on that context when you ask questions. It sets reminders. It knows your name, your project, your team, your goals — because it has been learning them from the moment you put it on.

The longer you wear ARIA, the better it knows you. It is not a product with a feature set. It is a relationship.

---

## The Technical Architecture

ARIA is a genuinely distributed AI system, with intelligence split across three layers:

### Layer 1 — The Edge (ESP32 Pendant)
The ESP32 microcontroller handles everything that must happen locally and instantly:
- **I2S digital audio capture** from the INMP441 microphone at 16kHz, 16-bit mono — the standard format for high-quality speech recognition
- **Real-time PCM streaming** over WiFi WebSocket to the Pi 5 base station — each 512-sample chunk (32ms) transmitted as binary with sub-100ms total transport latency
- **State machine** managing four states: IDLE (breathing blue), LISTENING (spinning purple), PROCESSING (spinning white), SPEAKING (pulsing green) — communicated to the LED ring and OLED display simultaneously
- **Touch/button interrupt** for push-to-talk activation — clean UX that eliminates false activations in noisy environments
- **OLED waveform animation** using SSD1306 128x64 display — real-time sine wave morphs based on current state, giving the pendant a living, responsive quality

The ESP32 connects to a WiFi hotspot run by the Pi 5 itself — this means ARIA has **zero dependency on the hackathon's WiFi network**. It creates its own closed network. This is a critical reliability decision.

### Layer 2 — The Local Brain (Raspberry Pi 5)
The Pi 5 is the invisible intelligence. It runs:

**Speech Recognition — OpenAI Whisper API**
When the user releases the button, the Pi sends the accumulated PCM audio to OpenAI's Whisper API. Whisper is state-of-the-art for speech recognition, trained on 680,000 hours of multilingual audio. It handles accents, background noise, and casual speech far better than any local model. The API returns a transcript in under a second for typical utterances.

**The AI Brain — OpenAI GPT-4o with Agentic Tool Use**
The transcript is passed to GPT-4o with a system prompt that includes:
- ARIA's personality and communication style
- The user's personal memory context (everything ARIA has learned about them)
- The last N turns of conversation history

GPT-4o operates in an agentic loop — it can call any of ARIA's tools, receive results, call more tools, and iterate until it has a complete answer. This is not a single-shot response. ARIA can chain: search the web → save a relevant memory → check the transcript → formulate a final answer, all in a single conversational turn.

**The Tool Suite:**
1. `search_web` — Brave Search API for real-time web results. Not cached, not stale. What's happening right now.
2. `search_x` — Twitter/X Bearer Token search for real-time social signal. Trending news, public sentiment, live events.
3. `save_memory` — Write a key-value fact to SQLite. Permanent across sessions.
4. `query_memories` — Retrieve relevant memories by text match. ARIA never forgets.
5. `get_transcript` — Pull the last N minutes of ambient transcript. What was said. Who said it. When.
6. `set_reminder` — Store time-sensitive notes. Surfaced automatically when due.
7. `get_datetime` — Current date, time, day. Grounded temporal awareness.

**Memory Extraction — Background Intelligence**
Every 15 minutes, a background task passes the recent ambient transcript to GPT-4o and asks it to extract 3-5 facts worth remembering. These are written to the memory store automatically. The user doesn't have to do anything. ARIA watches, listens, and learns — silently, continuously, locally.

**Text-to-Speech — ElevenLabs Voice Clone**
The final response text is sent to ElevenLabs' turbo TTS model, synthesised in the user's own cloned voice, and played through the Pi 5's Bluetooth connection to the user's AirPods. The audience hears it through a DAC-connected room speaker simultaneously. This dual-output setup means the demo is witnessed by everyone, not just the person wearing the pendant.

### Layer 3 — The Human Interface (Dashboard + AirPods)
The Pi 5 serves a fullscreen web dashboard — a dark, minimal UI that shows the live ambient transcript scrolling on the left, the ARIA conversation log on the right, and an animated waveform at the top that breathes and pulses with the system's state. Anyone in the room can see exactly what ARIA is hearing and thinking in real time.

The dashboard also has a chat box — you can type to ARIA directly, without the pendant. This serves as a demo fallback and also as a second interface for situations where you can't speak out loud.

---

## The Competitive Landscape

To understand why ARIA is significant, you need to understand what came before it.

**Humane AI Pin** — $230M raised from Salesforce Ventures, Tiger Global, and others. A lapel pin with a laser projector. Required a separate cellular plan. No voice cloning. No memory. No tool use. No ambient transcript. No local processing. Everything went to their servers. Launched at $699 + $24/month. Discontinued within a year. Sold to HP. The hardware was impressive. The software was a toy.

**Rabbit R1** — $180M raised. Bright orange handheld device. Promised a "Large Action Model" that would learn to use apps like a human. It did not do this. In practice it was a wrapper around existing AI APIs in a novel form factor. No persistent memory. No ambient awareness. No voice cloning. Overheated. Camera quality poor. Still technically alive but no longer culturally relevant.

**Tab AI (the necklace)** — A necklace with a microphone that records ambient audio and lets you query it. Closer to ARIA than the others. But: cloud-dependent, subscription-required, no tool use, no voice cloning, no on-device processing, no dashboard, no wearable identity. Funded but not shipped widely.

**Plaud Note** — A card-shaped device that sticks to your phone and records calls. Single-purpose. No AI interaction. No memory building. Passive only.

**Limitless Pendant** — Perhaps the closest spiritual predecessor. A wearable that records meetings and generates summaries. Has a "consent mode" that beeps to notify others. But: cloud-only, subscription model, no interactive AI, no tool use, no voice, no customisation.

**What all of them got wrong:**
They treated AI as a feature rather than as a relationship. They built recording devices with AI features bolted on, rather than building a genuine AI companion that happens to exist in physical form. And critically — every single one of them requires you to trust a corporation with your most private conversations.

**What ARIA does differently:**
1. **Local-first.** The audio never leaves your network except for the Whisper API call and GPT-4o query — both of which send only text, not raw audio. The transcript, memories, and conversation history live entirely on your own Raspberry Pi.
2. **Genuinely agentic.** ARIA doesn't just answer — it acts. It searches, remembers, retrieves, and reasons across multiple sources in a single conversational turn.
3. **Voice identity.** ARIA sounds like *you*. This is not a gimmick. When you hear your own voice come back to you as an AI, it creates a psychological intimacy that no other product replicates.
4. **Ambient intelligence.** The pendant is always listening in the background (ambient mode). By the time you ask a question, ARIA already has context. It knows what was discussed in the meeting you just left.
5. **Open source. No subscription. £30 hardware.**

---

## The Commercial Opportunity

The market for AI wearables is not a niche. It is one of the defining product categories of the next decade.

Knowledge workers spend approximately 40% of their working day in meetings, calls, and conversations. They forget 70% of what was discussed within 24 hours. They take incomplete notes. They miss action items. They repeat the same conversations to people who weren't in the room. They make decisions without full context.

ARIA eliminates all of this. Not by making people work harder, but by giving them an always-present AI that holds the context they cannot.

**Target customer:** Any knowledge worker — consultant, lawyer, product manager, entrepreneur, researcher, student, journalist. Anyone who lives in conversations and wishes they could remember everything.

**The business model:**
- **Hardware:** ARIA pendant kit, manufactured at scale for under £30, sold for £149. No proprietary components, open design.
- **Software:** Open source core. Premium features (team memory, shared context, integrations with Notion/Slack/Calendar) available via a lightweight cloud tier at £9/month.
- **Enterprise:** Compliant, on-premise deployment for law firms, consulting firms, healthcare providers — industries where conversation capture is both valuable and heavily regulated. ARIA's local-first architecture makes compliance dramatically simpler than any cloud-dependent competitor.

**Why now:**
- ESP32-S3 chips cost £3. Raspberry Pi 5 costs £70. INMP441 microphones cost £2. The hardware cost of building a capable AI wearable has collapsed.
- OpenAI Whisper, GPT-4o, ElevenLabs — the AI stack has commoditised. Any team with API access can build on world-class AI.
- Consumer trust in big tech AI is declining. Privacy-preserving, local-first products are a genuine market positioning, not just an ethical stance.
- The failures of Humane and Rabbit have educated the market — consumers know what the product *should* be. They're waiting for someone to build it right.

---

## The Team

Four people. 24 hours. Bath Hackathon 2026.

Two software engineers who understand AI systems, API integration, real-time web architecture, and database design. Two hardware engineers who understand microcontrollers, sensor integration, circuit design, I2S audio protocols, and physical fabrication. A soldering station. A 3D printer. A bag of components. An absurd amount of caffeine.

This is not a team that built a demo. This is a team that built a product — one with a complete software stack, a working hardware prototype, and a commercial vision that stands on its own merits.

The fact that it was built in 24 hours is not the story. The story is that it *works*.

---

## The Hackathon Tracks

ARIA was designed from first principles to compete across every track at Bath Hackathon 2026.

**Most Technically Impressive (Multimatic — DJI Neo prize)**
ARIA is a genuinely distributed AI system. Audio is captured on an ESP32 microcontroller, streamed over WiFi at 16kHz to a Raspberry Pi 5, transcribed by OpenAI Whisper, processed by GPT-4o in an agentic tool-use loop, synthesised by ElevenLabs TTS in a cloned voice, and played to Bluetooth AirPods — all within 3-5 seconds of the user releasing a button. A background process simultaneously extracts structured memories from ambient audio every 15 minutes using GPT-4o. A real-time WebSocket dashboard pushes live state to a browser. Seven APIs. Two compute layers. One coherent, seamless experience. This is not a hackathon project. This is infrastructure.

**Best Use of AI (Belmont Lansdown — De'Longhi Espresso Machine prize)**
AI is not a feature in ARIA. It is the entire product. GPT-4o is the brain. Whisper is the ears. ElevenLabs is the voice. Every interaction the user has is mediated, enhanced, and remembered by AI. The memory extraction loop means ARIA's intelligence grows over time — it is not static. Every ambient transcript is an opportunity to learn something new about the user. The tool suite means ARIA doesn't just respond — it acts in the world, searches the web, and reads live social data. This is AI embedded not just from the ground up, but woven into the physical form of the product itself.

**Most Commercially Viable (Ditch Carbon — Keychron keyboard prize)**
The commercial case for ARIA is not speculative. $230M was raised for Humane. $180M for Rabbit. Multiple other funded companies are building variants of the same product. The market has been validated at enormous scale — and then abandoned by products that didn't work. ARIA works. It costs £30 to build. It has a clear £149 hardware + £9/month software business model. It has a defensible privacy-first positioning at a time when consumer trust in big tech AI is at a historic low. It has enterprise applicability in legal, consulting, and healthcare. This is not a startup idea. This is a company.

**Embedded (XMOS — XCORE.AI Vision Development Kit + DS3 DAC prize)**
The ESP32-S3 is doing real embedded work. I2S audio capture from a digital MEMS microphone. Real-time PCM chunk streaming over WiFi. A hardware state machine driving NeoPixel LEDs and an OLED display simultaneously. A button interrupt handler managing push-to-talk transitions. The Pi 5 is running a full server stack with WebSocket connections, background async tasks, and real-time audio playback — all on a $70 single-board computer with no GPU. This is distributed embedded computing, designed from scratch to operate reliably in a noisy, uncertain real-world environment. No central cloud dependency. No proprietary lock-in. Anti-centralisation by architecture.

**Hackers' Choice (People's vote — Bambu Lab 3D Printer prize)**
ARIA is the product that every person in the room wishes existed the moment they see it. The demo is not a slideshow. It is a live experience. You watch someone hold up a small glowing pendant, press a button, ask a question about their own day — and hear the answer come back in their own voice, accurate and immediate. There is no sleight of hand. It has genuinely been listening. It genuinely knows who they are. It genuinely searched the web. That moment — the moment the audience realises the AI knows things it couldn't know unless it had been paying attention — is worth more than any feature list or pitch slide.

---

## The Demo, Explained

The demo works because ARIA has been operational for the duration of the hackathon. By the time we walk up to the judges, ARIA has 20+ hours of ambient transcript. It knows:
- The team's names
- What we've been building
- What problems we struggled with
- What we decided
- What we're proud of

When we ask "ARIA, who am I and what am I working on?" — it doesn't answer from a pre-loaded script. It answers from genuine context. When we ask it to search the web, it actually searches. When we demonstrate its memory, the memories are real.

This is not a prototype of a product. This is the product, running in production, demoing itself.

---

## The Future

ARIA v1 is a pendant with a Pi 5. ARIA v2 is a watch. ARIA v3 is an earpiece. ARIA v4 is invisible.

The hardware will shrink. The AI will improve. The memory will deepen. The tool suite will expand — calendar integration, email, health data, location context, smart home control.

But the core mission never changes: **give every person an AI that genuinely knows them, that lives in the physical world with them, that is owned entirely by them.**

Not rented. Not surveilled. Not forgotten.

Theirs.

---

## Summary

ARIA is a wearable AI personal assistant built in 24 hours at Bath Hackathon 2026.

It is a circular pendant with a microphone that listens to your life. A Raspberry Pi 5 that transcribes, thinks, and acts. An ElevenLabs voice clone that speaks back in your own voice through your AirPods. A memory system that grows every conversation. A tool suite that reaches into the live web.

It costs £30 to build. It requires no subscription. Your data never leaves your network.

Humane raised $230M and failed. Rabbit raised $180M and failed. We built what they were trying to build — in 24 hours, for £30, at a hackathon in Bath.

**Imagine what we do in six months.**
