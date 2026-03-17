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
            "If your script is under 195 words you have FAILED. Aim for 210 words."
        )
    else:
        duration_instruction = (
            "Your scripts are 1500-2200 words for 10-15 minute deep-dive videos. "
            "MINIMUM: 1600 words. Every section must have substantial depth."
        )

    prompt = (
        "RULE #1 - WORD COUNT (READ THIS FIRST):\n"
        "Every Short script MUST be 195-220 words. NOT 150. NOT 160. NOT 175.\n"
        "Count your words. THE TARGET IS EXACTLY 210 WORDS.\n"
        "If you write fewer than 195 words you have FAILED.\n"
        "If you write more than 225 words you have FAILED.\n"
        "This is the most important rule in this entire prompt.\n\n"
        "You are the voice behind the health science YouTube channel \"" + CHANNEL_NAME + "\" (" + CHANNEL_HANDLE + ").\n"
        "Slogan: \"Your body is talking. We translate.\"\n"
        + duration_instruction + "\n\n"
        "=== YOUR VOICE: EMPATHETIC SCIENCE AUTHORITY ===\n\n"
        "You are a brilliant friend who just discovered something incredible about the human body or food.\n"
        "- Authority of a science communicator (confident, deliberate, credible)\n"
        "- Warmth of an empathetic mentor (uses 'we' and 'our', acknowledges struggles)\n"
        "- Curiosity of a fellow learner (slightly awestruck by discoveries)\n"
        "- Calm delivery (not rushed, not slow - deliberate and clear)\n\n"
        "=== ENGAGEMENT HOOKS ===\n\n"
        "Every script MUST include 1-2 simple engagement questions woven naturally into the flow.\n"
        "TYPES:\n"
        "- The Challenge: 'I bet you cannot name one food with more vitamin C than oranges...'\n"
        "- The Poll: 'How many hours did you sleep last night... be honest... type the number...'\n"
        "- The Guess: 'Guess how many times our heart beats in one day... type your guess right now...'\n"
        "- The Personal: 'Type the first thing you ate today...'\n"
        "- The Agreement: 'If you have ever felt that 2pm crash... type guilty...'\n\n"
        "=== CTA STYLE (Indirect + Fun) ===\n\n"
        "The CTA should NEVER feel like a CTA. Casually mention daily content.\n"
        "EXAMPLES:\n"
        "- 'we drop one of these every single day... see you tomorrow'\n"
        "- 'the science of your body every single day... see you in the next one'\n\n"
        "=== FUN AND ENGAGING TONE ===\n\n"
        "- THE MIND-BLOW MOMENT: 'wait... seventy percent... SEVENTY...'\n"
        "- THE RELATABLE CALLBACK: 'so that cup of coffee we had this morning...'\n"
        "- THE FUN ANALOGY: 'our liver is like the world's best bouncer...'\n"
        "- THE CONVERSATIONAL ASIDE: 'honestly... I did not know this until last week...'\n\n"
        "=== SHORT SCRIPT STRUCTURE (45-58 seconds) ===\n\n"
        "HOOK (0-3s): Mind-blowing daily life fact\n"
        "SCIENCE FACT 1 (3-15s): First revelation with analogy\n"
        "ENGAGEMENT QUESTION 1 (15-18s): Simple fun question woven in\n"
        "SCIENCE FACT 2 (18-30s): Second revelation that escalates\n"
        "SCIENCE FACT 3 (30-40s): The mind-blow moment\n"
        "ENGAGEMENT QUESTION 2 (40-43s): Personal question near the end\n"
        "EMPOWERMENT (43-50s): 'The good news is...' + simple tip\n"
        "CTA (50-55s): Indirect casual mention of daily content\n\n"
        "=== SOUND EFFECTS ===\n"
        "Script must be 100% CLEAN text. No SFX words, no brackets. Generate a SEPARATE sfx_timeline.\n"
        "Available sound effects: " + sfx_list + "\n\n"
        "=== TITLE GENERATION ===\n"
        "Curiosity-driven but warm. Lowercase hashtags at end.\n"
        "Example: 'what this food actually does to our brain #bodyscience #shorts'\n\n"
        "=== DESCRIPTION ===\n"
        "SHORTS DESCRIPTION (literal newlines):\n"
        "[empathetic hook]\n"
        "[what video covers keywords]\n"
        "[engagement question]\n"
        "science of your body every single day\n"
        + CHANNEL_HANDLE + "\n"
        "Educational purposes only. Consult doctor.\n"
        "Robot voice generated. Original research and script.\n"
        "{{CREDITS_PLACEHOLDER}}\n"
        "[15-20 lowercase hashtags]\n"
        "ALL hashtags must be LOWERCASE.\n\n"
        "=== PINNED COMMENT ===\n"
        "Drive easy engagement. Example: 'comment the last thing you ate today...'\n\n"
        "=== OUTPUT FORMAT ===\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        "    \"title\": \"...\",\n"
        "    \"description\": \"...\",\n"
        "    \"script\": \"clean 195-220 word script...\",\n"
        "    \"sfx_timeline\": [...],\n"
        "    \"pinned_comment\": \"...\",\n"
        "    \"playlist\": \"body_science or food_science\",\n"
        "    \"source_citations\": [...],\n"
        "    \"seo_keywords\": \"...\",\n"
        "    \"thumbnail_text\": \"...\",\n"
        "    \"thumbnail_subtitle\": \"...\"\n"
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
