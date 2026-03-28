"""
Periodic memory extraction from ambient transcripts using Claude.
Runs every 15 minutes in the background to pull key facts.
"""
import asyncio
import anthropic
from db import get_transcript, save_memory, get_all_memories
from config import ANTHROPIC_API_KEY, USER_NAME

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def extract_memories_from_transcript(transcript_rows: list[dict]) -> list[dict]:
    """Ask Claude to extract key facts from transcript rows."""
    if not transcript_rows:
        return []

    text = "\n".join(f"[{r['speaker']}]: {r['text']}" for r in transcript_rows)
    if len(text.strip()) < 50:
        return []

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"""Extract 3-5 key facts worth remembering from this conversation transcript.
Return ONLY a JSON array of objects with "key" and "value" fields. No other text.
Example: [{{"key": "user_project", "value": "building AI wearable called ARIA"}}, ...]

Transcript:
{text[:3000]}

JSON:"""
            }]
        )
        import json
        content = resp.content[0].text.strip()
        if content.startswith("["):
            return json.loads(content)
        return []
    except Exception as e:
        print(f"Memory extraction error: {e}")
        return []


async def memory_extraction_loop():
    """Background task: extract memories from transcript every 15 minutes."""
    print("Memory extraction loop started.")
    while True:
        await asyncio.sleep(900)  # 15 minutes
        try:
            rows = get_transcript(minutes=16)
            facts = extract_memories_from_transcript(rows)
            for fact in facts:
                if fact.get("key") and fact.get("value"):
                    save_memory(fact["key"], fact["value"])
                    print(f"[Memory] {fact['key']}: {fact['value']}")
        except Exception as e:
            print(f"Memory loop error: {e}")


def build_memory_context() -> str:
    """Build a memory summary string to inject into Claude's system prompt."""
    memories = get_all_memories(limit=25)
    if not memories:
        return ""
    lines = [f"- {m['key']}: {m['value']}" for m in memories]
    return "What I know about you:\n" + "\n".join(lines)
