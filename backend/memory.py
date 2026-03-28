"""
Periodic memory extraction from ambient transcripts using OpenAI GPT-4o.
Runs every 15 minutes in the background.
"""
import asyncio
import json
import openai
from db import get_transcript, save_memory, get_all_memories
from config import OPENAI_API_KEY, USER_NAME

client = openai.OpenAI(api_key=OPENAI_API_KEY)


def extract_memories_from_transcript(transcript_rows: list[dict]) -> list[dict]:
    """Ask GPT-4o to extract key facts from transcript rows."""
    if not transcript_rows:
        return []
    text = "\n".join(f"[{r['speaker']}]: {r['text']}" for r in transcript_rows)
    if len(text.strip()) < 50:
        return []
    try:
        resp = client.chat.completions.create(
            model="gpt-5.2",
            max_completion_tokens=512,
            messages=[{
                "role": "user",
                "content": f"""Extract 3-5 key facts worth remembering from this conversation.
Return ONLY a JSON array with "key" and "value" fields. No other text.
Example: [{{"key": "user_project", "value": "building AI wearable called ARIA"}}, ...]

Transcript:
{text[:3000]}

JSON:"""
            }]
        )
        content = resp.choices[0].message.content.strip()
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
        await asyncio.sleep(900)
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
    memories = get_all_memories(limit=25)
    if not memories:
        return ""
    lines = [f"- {m['key']}: {m['value']}" for m in memories]
    return "What I know about you:\n" + "\n".join(lines)
