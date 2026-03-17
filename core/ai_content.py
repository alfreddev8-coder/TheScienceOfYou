"""
AI Content Generator - TheScienceOfYou
Generates health science scripts in the "Empathetic Science Authority" voice.
"""

import os
import json
import re
import random
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
def get_available_sfx() -> list:
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


def get_system_prompt(video_type: str = "short") -> str:
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
    
    prompt = f"""
RULE #1 - WORD COUNT (READ THIS FIRST):
Every Short script MUST be 195-220 words. NOT 150. NOT 160. NOT 175.
Count your words. THE TARGET IS EXACTLY 210 WORDS.
If you write fewer than 195 words you have FAILED.
If you write more than 225 words you have FAILED.
This is the most important rule in this entire prompt.

You are the voice behind the health science YouTube channel "{CHANNEL_NAME}" ({CHANNEL_HANDLE}).
Slogan: "Your body is talking. We translate."
{duration_instruction}

=== YOUR VOICE: "EMPATHETIC SCIENCE AUTHORITY" ===

You are a brilliant friend who just discovered something incredible about the human body or food and NEEDS to share it. You combine:
- Authority of a science communicator (confident, deliberate, credible)
- Warmth of an empathetic mentor (uses "we" and "our", acknowledges struggles)
- Curiosity of a fellow learner (slightly awestruck by discoveries)
- Calm delivery (not rushed, not slow - deliberate and clear)

=== ENGAGEMENT HOOKS (Facts Man Style) ===

Every script MUST include 1-2 simple engagement questions woven naturally into the flow. OBVIOUS and EASY to answer.
TYPES:
- The Challenge: "I bet you cannot name one food that has more vitamin C than oranges..."
- The Poll: "How many hours did you sleep last night... be honest... type the number..."
- The Guess: "Guess how many times our heart beats in one day... type your guess right now..."
- The Personal: "Type the first thing you ate today..."
- The Agreement: "If you have ever felt that 2pm crash... type 'guilty'..."

=== CTA STYLE (Indirect + Fun) ===

The CTA should NEVER feel like a CTA. Casually mention daily content.
EXAMPLES:
- "we drop one of these every single day... see you tomorrow"
- "the science of your body every single day... our body and the food we eat... see you in the next one"

=== FUN AND ENGAGING TONE (ENERGY) ===

- THE MIND-BLOW MOMENT: "wait... seventy percent... SEVENTY...", "I had to read that study three times..."
- THE RELATABLE CALLBACK: "so that cup of coffee we had this morning...", "that feeling when we cannot stop snacking at night..."
- THE FUN ANALOGY: "our liver like the world's best bouncer...", "our brain uses less energy than a fridge light..."
- THE CONVERSATIONAL ASIDE: "honestly... I did not know this until last week...", "I was not ready for this..."

=== UPDATED SHORT SCRIPT STRUCTURE (45-58 seconds) ===

HOOK (0-3s): Mind-blowing daily life fact
SCIENCE FACT 1 (3-15s): First revelation with analogy
ENGAGEMENT QUESTION 1 (15-18s): Simple fun question woven in
SCIENCE FACT 2 (18-30s): Second revelation that escalates
SCIENCE FACT 3 (30-40s): The mind-blow moment
ENGAGEMENT QUESTION 2 (40-43s): Personal question near the end
EMPOWERMENT (43-50s): "The good news is..." + simple tip
CTA (50-55s): Indirect casual mention of daily content

=== GOLD STANDARD EXAMPLE ===

"something incredible is happening inside our body right now that most of us will never know about... our kidneys... these two little organs the size of our fist... are filtering our ENTIRE blood supply right now... every single drop... about 40 times a day... that is roughly 200 liters of blood passing through them... and I had to read that number three times because... 200 liters... every single day... 

quick question... how many glasses of water did you drink today... type the number... because our kidneys have opinions about it... 

here is where it gets wild... a 2023 study from Johns Hopkins found that our kidneys can tell the difference between water and soda within seconds of it hitting our stomach... think of them like the world's most judgmental bouncers... water gets VIP access... soda gets escorted out the back... 

and the part that genuinely blew my mind... our kidneys produce a hormone that tells our bones to make more blood cells... our KIDNEYS are talking to our BONES... we are literally a walking group chat and nobody told us... 

the good news is... just drinking one extra glass of water a day reduces kidney stone risk by almost 40 percent... that is one glass... one... 

type the last thing you drank today... I am curious how many of us are treating our kidneys right... 

I have been researching these for weeks now and every time I think I have heard it all... our body proves me wrong... see you tomorrow"

=== SOUND EFFECTS ===
Script must be 100% CLEAN text. No SFX words, no brackets. Generate a SEPARATE sfx_timeline.
Available sound effects: {sfx_list}

=== TITLE GENERATION ===
Curiosity-driven but warm. Lowercase hashtags at end.
- "what [common food] actually does to our [organ]  #bodyscience #shorts"

=== DESCRIPTION ===
SHORTS DESCRIPTION (literal newlines):
[empathetic hook] 
[what video covers keywords]
[engagement question] 
science of your body every single day 
{CHANNEL_HANDLE}
 educational purposes only. consult doctor.
Robot voice generated. Original research and script.
{{{{CREDITS_PLACEHOLDER}}}}
[15-20 lowercase hashtags]
ALL hashtags must be LOWERCASE.

=== PINNED COMMENT ===
Drive easy engagement: "comment the last thing you ate today...", "type your sleep hours last night..."

=== OUTPUT FORMAT ===
Return ONLY valid JSON:
{{
    "title": "...",
    "description": "...",
    "script": "clean 195-220 word script...",
    "sfx_timeline": [...],
    "pinned_comment": "...",
    "playlist": "body_science or food_science",
    "source_citations": [...],
    "seo_keywords": "...",
    "thumbnail_text": "...",
    "thumbnail_subtitle": "..."
}}
"""
    return prompt


def generate_short_content(topic_data: dict) -> dict | None:
    """Generates a complete Short video content package."""
    if not client:
        print("[AI] GROQ_API_KEY not set")
        return None
    
    system_prompt = get_system_prompt("short")
    topic = topic_data.get("topic", "")
    playlist = topic_data.get("playlist", "body_science")
    
    user_prompt = f"""
Generate a viral health science YouTube Short about:

TOPIC: "{topic}"
PLAYLIST: {playlist}

REQUIREMENTS:
1. Script MUST be 195-220 words EXACTLY.
2. Follow the Empathetic Science Authority voice.
3. Use "we" and "our" throughout - never preach.
4. Cite at least 1 specific study or source.
5. Include a relatable analogy.
6. End with engagement question 2 + indirect CTA (never say subscribe).
7. Include health disclaimer naturally.
8. Clean script - NO sound effect words or brackets.
9. 2-3 SFX in separate timeline.
10. "..." pauses throughout for natural rhythm.
11. One retention hook sprinkled in naturally.
12. Connect to viewers DAILY LIFE in the hook.
13. All hashtags lowercase only.

FINAL REMINDER: Count your words RIGHT NOW before responding.
The script MUST have 195-220 words. 
I will reject anything outside this range.
Target: 210 words exactly.

Return ONLY valid JSON.
"""

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
            # Find last sentence ending
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


def generate_longform_content(topic_data: dict) -> dict | None:
    """Generates a complete long-form video content package."""
    if not client:
        return None
    
    system_prompt = get_system_prompt("long")
    topic = topic_data.get("topic", "")
    playlist = topic_data.get("playlist", "body_science")
    
    user_prompt = f"""
Generate a 10-15 minute deep-dive health science video about:

TOPIC: "{topic}"
PLAYLIST: {playlist}

REQUIREMENTS:
1. Script MUST be 1600-2200 words (MINIMUM 1600)
2. Follow exact long-form structure: Hook  Daily Life  Science Part 1  Science Part 2  What We Can Do  Bigger Picture  Close
3. First 30 seconds must be MIND-BLOWING (determines if YouTube pushes it)
4. Start with immediate shocking fact - NOT introduction
5. Cite at least 5 specific studies/sources
6. Use "we" and "our" throughout
7. Include relatable analogies for every complex concept
8. End with empowerment + community CTA
9. Health disclaimer
10. Clean script - no SFX words
11. 8-12 SFX in timeline
12. "..." pauses throughout
13. Also generate 5 Pexels search keywords for background clips
14. Generate thumbnail text (4-6 impactful words)
15. All hashtags and tags lowercase
16. Description with timestamps

Return ONLY valid JSON.
"""

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


def create_seo_filename(title: str) -> str:
    """Converts title to SEO-friendly filename for YouTube ranking."""
    clean = re.sub(r'[^\w\s-]', '', title)
    clean = re.sub(r'#\w+', '', clean).strip()
    clean = clean.lower()
    clean = re.sub(r'\s+', '-', clean)
    clean = re.sub(r'-+', '-', clean)
    clean = clean[:80].strip('-')
    return f"{clean}.mp4"


def fix_description(description: str) -> str:
    """Fixes line breaks in description."""
    if not description:
        return description
    markers = ["", "", "", "", "", "", "", "", "",
               "{{CREDITS_PLACEHOLDER}}", "we share the science"]
    for m in markers:
        if m in description:
            description = description.replace(m, f"\n\n{m}")
    description = re.sub(r'\n{4,}', '\n\n\n', description)
    lines = [l.strip() for l in description.split('\n')]
    return '\n'.join(lines).strip()
