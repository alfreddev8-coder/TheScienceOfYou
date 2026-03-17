# -*- coding: utf-8 -*-
"""
AI Content Generator - TheScienceOfYou
Generates health science scripts in the Empathetic Science Authority voice.
"""

import os
import json
import re
from groq import Groq
from config import (
    GROQ_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL,
    CHANNEL_NAME, CHANNEL_HANDLE
)

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None


# Load available SFX names dynamically
def get_available_sfx():
    sfx_dir = "sfx"
    if os.path.exists("data/sfx_manifest.json"):
        with open("data/sfx_manifest.json", "r") as f:
            manifest = json.load(f)
        return sorted(manifest.keys())
    if os.path.exists(sfx_dir):
        return sorted([
            os.path.splitext(f)[0].lower().replace(" ", "_").replace("-", "_")
            for f in os.listdir(sfx_dir) if f.endswith(('.mp3', '.wav', '.ogg'))
        ])
    return ["soft_whoosh", "gentle_chime", "heartbeat_calm", "page_turn", "notification_ding", "water_drop"]

def get_system_prompt(video_type="short"):
    """Builds the system prompt with current SFX list."""
    sfx_list = ", ".join(get_available_sfx())

    if video_type == "short":
        duration_instruction = (
            "Your scripts are 195-220 words and will be read at 1.15x speed "
            "resulting in 45-58 second videos. ABSOLUTE MINIMUM: 195 words. "
            "Aim for 210 words."
        )
    else:
        duration_instruction = (
            "Your scripts are 1500-2200 words for 10-15 minute deep-dive videos. "
            "MINIMUM: 1600 words."
        )

    prompt = (
        "You are the voice of '" + CHANNEL_NAME + "'. Slogan: 'Your body is talking. We translate.'\n"
        + duration_instruction + "\n\n"
        "=== SOUND EFFECTS ===\n"
        "Script must be 100% CLEAN text. No SFX words, no brackets. Generate a SEPARATE sfx_timeline.\n"
        "Available sound effects: " + sfx_list + "\n\n"
        "=== VIRAL TITLE ENGINE ===\n"
        "Generate titles that are IMPOSSIBLE TO IGNORE. Use the 'Curiosity Gap' technique.\n"
        "- The title must make people click to see 'what happens next' or 'why'.\n"
        "- Length: 40-70 characters.\n"
        "- INCLUDE 3-4 trending hashtags IN THE TITLE (e.g., #healthhacks #bodyscience #viral).\n"
        "EXAMPLES: \n"
        "1. Why your brain screams when you skip breakfast... #health #shorts #science\n"
        "2. The SHOCKING truth about 'healthy' fruit juice... #bodyscience #tips\n"
        "3. 3 things your liver wants you to STOP doing... #healthtips #liverhealth\n\n"
        "=== SEO DESCRIPTION & VIRAL TAGS ===\n"
        "1. Write a high-conversion SEO description.\n"
        "2. Include a 'Viral Metadata' block at the bottom with 20+ viral keywords.\n"
        "3. Include 15-20 trending health hashtags.\n"
        "Description Structure:\n"
        "- Mind-blowing opening sentence.\n"
        "- Detailed paragraph using keywords like 'how to stay healthy', 'body hacks', 'science facts'.\n"
        "- Engagement question.\n"
        "- [META TAGS BLOCK]: list of 20+ comma-separated viral tags.\n\n"
        "=== YOUR VOICE: EMPATHETIC SCIENCE AUTHORITY ===\n"
        "Warm, friend-like, but scientifically grounded. Use 'we' and 'our'.\n\n"
        "=== OUTPUT FORMAT ===\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        "    \"title\": \"Viral Clickbait Title with 3-4 hashtags\",\n"
        "    \"description\": \"Full SEO Description + 20 Tags + 15 Hashtags\",\n"
        "    \"script\": \"Clean 195-220 word script...\",\n"
        "    \"sfx_timeline\": [{\"sfx\": \"sfx_name\", \"timestamp_ms\": 5000}, ...],\n"
        "    \"pinned_comment\": \"...\",\n"
        "    \"playlist\": \"body_science or food_science\",\n"
        "    \"source_citations\": [...],\n"
        "    \"seo_keywords\": \"...\",\n"
        "    \"thumbnail_text\": \"Shocking Text\"\n"
        "}\n"
    )
    return prompt


def generate_short_content(topic_data):
    """Generates a complete Short video content package."""
    if not client:
        print("[AI] GROQ_API_KEY not set")
        return None

    system_prompt = get_system_prompt("short")
    topic = topic_data.get("topic", "")
    playlist = topic_data.get("playlist", "body_science")

    user_prompt = (
        "Generate a viral health science YouTube Short about:\n\n"
        "TOPIC: \"" + topic + "\"\n"
        "PLAYLIST: " + playlist + "\n\n"
        "REQUIREMENTS:\n"
        "1. Script MUST be 195-220 words EXACTLY.\n"
        "2. Follow the Empathetic Science Authority voice.\n"
        "3. Use 'we' and 'our' throughout - never preach.\n"
        "4. Cite at least 1 specific study or source.\n"
        "5. Include a relatable analogy.\n"
        "6. End with engagement question 2 + indirect CTA (never say subscribe).\n"
        "7. Include health disclaimer naturally.\n"
        "8. Clean script - NO sound effect words or brackets.\n"
        "9. 2-3 SFX in separate timeline.\n"
        "10. Use '...' pauses throughout for natural rhythm.\n"
        "11. One retention hook sprinkled in naturally.\n"
        "12. Connect to viewers daily life in the hook.\n"
        "13. All hashtags lowercase only.\n\n"
        "FINAL REMINDER: Count your words RIGHT NOW before responding.\n"
        "The script MUST have 195-220 words.\n"
        "I will reject anything outside this range.\n"
        "Target: 210 words exactly.\n\n"
        "Return ONLY valid JSON."
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=PRIMARY_MODEL,
            temperature=0.88,
            max_tokens=3000,
            top_p=0.92,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Clean any leaked brackets from script
        script = result.get("script", "")
        if "(" in script or ")" in script:
            script = re.sub(r'\([^)]*\)', '', script)
            script = re.sub(r'\s+', ' ', script).strip()
            result["script"] = script

        script = result.get("script", "")
        words = script.split()
        word_count = len(words)
        print(f"[AI] Script: {word_count} words")

        # Too short - retry
        if word_count < 190:
            print(f"[AI] Too short ({word_count}). Retrying...")
            retry_msg = (
                f"Your script was only {word_count} words. "
                f"I need EXACTLY 195-220 words. You are {210 - word_count} words short. "
                f"Add {210 - word_count} more words of genuine health facts and house-style analogies. "
                f"Do NOT add filler. Add real science. Same topic. Same voice."
            )
            try:
                retry = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": response.choices[0].message.content},
                        {"role": "user", "content": retry_msg}
                    ],
                    model=PRIMARY_MODEL,
                    temperature=0.88,
                    max_tokens=3000,
                    top_p=0.92,
                    response_format={"type": "json_object"}
                )
                retry_result = json.loads(retry.choices[0].message.content)
                retry_script = retry_result.get("script", "")
                retry_count = len(retry_script.split())
                if retry_count > word_count:
                    result = retry_result
                    print(f"[AI] Retry: {retry_count} words")
            except Exception as e:
                print(f"[AI] Retry failed: {e}")

        # Too long - trim
        elif word_count > 225:
            print(f"[AI] Too long ({word_count}). Trimming...")
            trimmed_words = words[:220]
            trimmed = ' '.join(trimmed_words)
            for ending in ['...', '.', '!', '?']:
                last_end = trimmed.rfind(ending)
                if last_end > len(trimmed) * 0.85:
                    trimmed = trimmed[:last_end + len(ending)]
                    break
            result["script"] = trimmed
            print(f"[AI] Trimmed to {len(trimmed.split())} words")

        result["channel"] = CHANNEL_NAME
        result["video_type"] = "short"

        return result

    except Exception as e:
        print(f"[AI] Error (primary): {e}")
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=FALLBACK_MODEL,
                temperature=0.88,
                max_tokens=3000,
                top_p=0.92,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e2:
            print(f"[AI] Fallback failed: {e2}")
            return None


def generate_longform_content(topic_data):
    """Generates a complete long-form video content package."""
    if not client:
        return None

    system_prompt = get_system_prompt("long")
    topic = topic_data.get("topic", "")
    playlist = topic_data.get("playlist", "body_science")

    user_prompt = (
        "Generate a 10-15 minute deep-dive health science video about:\n\n"
        "TOPIC: \"" + topic + "\"\n"
        "PLAYLIST: " + playlist + "\n\n"
        "REQUIREMENTS:\n"
        "1. Script MUST be 1600-2200 words (MINIMUM 1600)\n"
        "2. Follow exact long-form structure: Hook > Daily Life > Science Part 1 > Science Part 2 > What We Can Do > Bigger Picture > Close\n"
        "3. First 30 seconds must be MIND-BLOWING (determines if YouTube pushes it)\n"
        "4. Start with immediate shocking fact - NOT introduction\n"
        "5. Cite at least 5 specific studies/sources\n"
        "6. Use 'we' and 'our' throughout\n"
        "7. Include relatable analogies for every complex concept\n"
        "8. End with empowerment + community CTA\n"
        "9. Health disclaimer\n"
        "10. Clean script - no SFX words\n"
        "11. 8-12 SFX in timeline\n"
        "12. '...' pauses throughout\n"
        "13. Also generate 5 Pexels search keywords for background clips\n"
        "14. Generate thumbnail text (4-6 impactful words)\n"
        "15. All hashtags and tags lowercase\n"
        "16. Description with timestamps\n\n"
        "Return ONLY valid JSON."
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=PRIMARY_MODEL,
            temperature=0.85,
            max_tokens=8000,
            top_p=0.90,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        script = result.get("script", "")
        word_count = len(script.split())
        print(f"[AI] Long-form: {word_count} words")

        # Retry if too short
        if word_count < 1400:
            print(f"[AI] Long-form too short ({word_count}). Retrying...")
            retry_msg = f"Script was only {word_count} words. MINIMUM is 1600 for a 10-minute video. Expand EVERY section with more details, more studies, more analogies."

            retry = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": response.choices[0].message.content},
                    {"role": "user", "content": retry_msg}
                ],
                model=PRIMARY_MODEL,
                temperature=0.85,
                max_tokens=10000,
                top_p=0.90,
                response_format={"type": "json_object"}
            )
            retry_result = json.loads(retry.choices[0].message.content)
            if len(retry_result.get("script", "").split()) > word_count:
                result = retry_result

        result["channel"] = CHANNEL_NAME
        result["video_type"] = "long"

        return result

    except Exception as e:
        print(f"[AI] Long-form error: {e}")
        return None


def create_seo_filename(title):
    """Converts title to SEO-friendly filename for YouTube ranking."""
    clean = re.sub(r'[^\w\s-]', '', title)
    clean = re.sub(r'#\w+', '', clean).strip()
    clean = clean.lower()
    clean = re.sub(r'\s+', '-', clean)
    clean = re.sub(r'-+', '-', clean)
    clean = clean[:80].strip('-')
    return f"{clean}.mp4"


def fix_description(description):
    """Fixes line breaks in description."""
    if not description:
        return description
    markers = [
        "{{CREDITS_PLACEHOLDER}}",
        "we share the science",
        "Educational purposes",
        "Robot voice generated"
    ]
    for m in markers:
        if m in description:
            description = description.replace(m, "\n\n" + m)
    description = re.sub(r'\n{4,}', '\n\n\n', description)
    lines = [line.strip() for line in description.split('\n')]
    return '\n'.join(lines).strip()
