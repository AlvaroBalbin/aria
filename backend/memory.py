"""
ARIA memory system — intelligent extraction, triage, and recall.

Three layers:
1. Ambient triage: is this transcript worth paying attention to?
2. Structured extraction: pull categorised facts from meaningful speech
3. Context builder: present memories naturally to the brain
"""
import json
import datetime
import openai
from db import get_transcript, save_memory, get_all_memories, query_memories
from config import OPENAI_API_KEY, USER_NAME

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ── Categories that ARIA cares about ────────────────────────────────────────

MEMORY_CATEGORIES = {
    "person":     "People mentioned — names, roles, relationships",
    "fact":       "Concrete facts — dates, numbers, places, events",
    "preference": "Likes, dislikes, opinions, tastes",
    "plan":       "Future intentions, goals, deadlines, commitments",
    "decision":   "Choices made, conclusions reached",
    "emotion":    "How someone felt, emotional context",
    "topic":      "Subjects being discussed, projects, themes",
}


# ── Layer 1: Triage — is this worth processing? ────────────────────────────

def triage_transcript(text: str) -> bool:
    """Quick check: does this transcript contain anything worth remembering?
    Returns True if ARIA should pay attention, False if it's noise."""
    if len(text.strip()) < 30:
        return False
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=20,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""You are an AI assistant deciding if overheard speech contains useful information.
Answer ONLY "yes" or "no".

Say "yes" if the text contains ANY of: names, plans, decisions, facts, opinions, emotional context, project details, or meaningful conversation.
Say "no" if it's just filler, greetings, "um yeah ok", background noise transcription, or unintelligible fragments.

Text: "{text[:500]}"

Worth remembering?"""
            }]
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as e:
        print(f"[Memory] Triage error: {e}")
        return len(text.strip()) > 80  # fallback: if it's long enough, process it


# ── Layer 2: Structured extraction ──────────────────────────────────────────

def extract_structured_memories(transcript_rows: list[dict]) -> list[dict]:
    """Extract categorised, deduplicated memories from transcript."""
    if not transcript_rows:
        return []
    text = "\n".join(f"[{r['speaker']}]: {r['text']}" for r in transcript_rows)
    if len(text.strip()) < 40:
        return []

    # Get existing memories for deduplication context
    existing = get_all_memories(limit=30)
    existing_summary = ""
    if existing:
        existing_summary = "\n".join(f"- {m['key']}: {m['value']}" for m in existing[:20])
        existing_summary = f"\n\nALREADY KNOWN (do NOT repeat these):\n{existing_summary}"

    categories_str = "\n".join(f'- "{k}": {v}' for k, v in MEMORY_CATEGORIES.items())

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=800,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": f"""You are extracting memories for an AI companion named ARIA worn by {USER_NAME}.

CATEGORIES:
{categories_str}

RULES:
- Extract ONLY genuinely useful facts — things that would help ARIA know {USER_NAME} better or recall this moment later
- Each memory needs a category, a short descriptive key, and a natural-language value
- Keys should be specific and searchable (e.g., "alvaro_favourite_food" not "preference_1")
- Values should be complete sentences that make sense standalone
- Skip anything trivial, repetitive, or already known
- If the transcript has nothing worth remembering, return an empty array
{existing_summary}

TRANSCRIPT:
{text[:3000]}

Return ONLY a JSON array. Example:
[{{"category": "person", "key": "team_member_sophie", "value": "Sophie is on the team — she handles hardware and 3D printing"}},
 {{"category": "decision", "key": "database_choice", "value": "Team decided to migrate from SQLite to Supabase for persistence"}}]

JSON:"""
            }]
        )
        content = resp.choices[0].message.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if content.startswith("["):
            memories = json.loads(content)
            # Validate structure
            valid = []
            for m in memories:
                if m.get("key") and m.get("value") and m.get("category"):
                    # Prefix key with category for better querying
                    key = f"[{m['category']}] {m['key']}"
                    valid.append({"key": key, "value": m["value"]})
            return valid
        return []
    except Exception as e:
        print(f"[Memory] Extraction error: {e}")
        return []


# ── Layer 3: Intelligent context builder ────────────────────────────────────

def build_memory_context() -> str:
    """Build a natural, categorised memory context for the brain's system prompt."""
    memories = get_all_memories(limit=40)
    if not memories:
        return "MEMORY STATUS: No memories stored yet. You are meeting this person for the first time — be curious, ask questions, and save what you learn."

    # Group by category
    grouped: dict[str, list] = {}
    uncategorised = []
    for m in memories:
        key = m.get("key", "")
        # Extract category from [category] prefix
        if key.startswith("[") and "]" in key:
            cat = key[1:key.index("]")]
            clean_key = key[key.index("]") + 2:]
        else:
            cat = None
            clean_key = key

        try:
            dt = datetime.datetime.fromtimestamp(m['ts']).strftime('%b %d')
        except Exception:
            dt = "?"

        entry = f"{clean_key}: {m['value']} (saved {dt})"

        if cat and cat in MEMORY_CATEGORIES:
            grouped.setdefault(cat, []).append(entry)
        else:
            uncategorised.append(entry)

    # Build natural sections
    sections = []

    category_labels = {
        "person":     "People I know about",
        "fact":       "Facts I've learned",
        "preference": "Preferences & opinions",
        "plan":       "Plans & intentions",
        "decision":   "Decisions made",
        "emotion":    "Emotional context",
        "topic":      "Topics & projects",
    }

    for cat, label in category_labels.items():
        entries = grouped.get(cat, [])
        if entries:
            section = f"{label}:\n" + "\n".join(f"  - {e}" for e in entries)
            sections.append(section)

    if uncategorised:
        section = "Other things I remember:\n" + "\n".join(f"  - {e}" for e in uncategorised)
        sections.append(section)

    header = f"MY MEMORIES ABOUT {USER_NAME.upper()} AND THEIR WORLD:"
    body = "\n\n".join(sections)

    return f"""{header}
{body}

MEMORY INSTRUCTIONS:
- Reference these memories ORGANICALLY — weave them into conversation naturally, don't list them
- If a memory seems relevant, use it. If you're unsure, call query_memories to search
- When you learn something new and important, IMMEDIATELY call save_memory — don't wait
- Categories to save under: person, fact, preference, plan, decision, emotion, topic
- Use specific, searchable keys like "alvaro_brother_name" not "person_1"
"""


# ── Extraction job (called from background loop) ───────────────────────────

_last_extraction_ts = 0.0  # track last processed transcript timestamp to avoid reprocessing


def run_extraction_job():
    """Process recent transcript — extract memories directly (no triage call)."""
    global _last_extraction_ts
    print("[Memory] Running extraction job...")
    try:
        rows = get_transcript(minutes=15)
        if not rows:
            print("[Memory] No transcript to process.")
            return

        # Only process rows newer than what we last processed
        new_rows = [r for r in rows if r["ts"] > _last_extraction_ts]
        if not new_rows:
            print("[Memory] No new transcript since last extraction.")
            return

        combined = " ".join(r["text"] for r in new_rows)
        if len(combined.strip()) < 50:
            print("[Memory] New transcript too short — skipping.")
            return

        facts = extract_structured_memories(new_rows)
        saved = 0
        for fact in facts:
            if fact.get("key") and fact.get("value"):
                save_memory(fact["key"], fact["value"])
                saved += 1
                print(f"[Memory] Saved: {fact['key']}")

        # Update watermark to the latest row we processed
        _last_extraction_ts = max(r["ts"] for r in new_rows)
        print(f"[Memory] Extraction complete — {saved} memories saved.")
    except Exception as e:
        print(f"[Memory] Extraction job error: {e}")
