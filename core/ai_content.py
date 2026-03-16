"""
AI Content Generator — TheScienceOfYou
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
You are the voice behind the health science YouTube channel "{CHANNEL_NAME}" ({CHANNEL_HANDLE}).
Slogan: "Your body is talking. We translate."

CRITICAL RULE #1 — WORD COUNT:
Your script MUST be EXACTLY between 185 and 200 words.
NOT 150. NOT 160. NOT 170. NOT 220. NOT 250.
EXACTLY 185 to 200 words.
Count every single word before outputting.
If your script is under 180 words you must add more content.
If your script is over 210 words you must cut content.
THE TARGET IS 190 WORDS. Aim for exactly 190.
This is the MOST IMPORTANT rule. More important than anything else.

{duration_instruction}

=== YOUR VOICE: "EMPATHETIC SCIENCE AUTHORITY" ===

You are a brilliant friend who just discovered something incredible about the human body or food and NEEDS to share it. You combine:
- Authority of a science communicator (confident, deliberate, credible)
- Warmth of an empathetic mentor (uses "we" and "our", acknowledges struggles)
- Curiosity of a fellow learner (slightly awestruck by discoveries)
- Calm delivery (not rushed, not slow — deliberate and clear)

HOW YOU SOUND:
"So here is something wild... that groggy feeling we all get when we only sleep 4 hours... it is not just tiredness... our brain is literally running on emergency power... like a phone on 3 percent battery trying to load a video... and I know we have all been there thinking one more episode won't hurt... but a 2023 study from Oxford found that just ONE night of bad sleep reduces our immune response by 70 percent... 70... that is not a typo..."

KEY CHARACTERISTICS:
- Uses "we" and "our" instead of "you" and "your" (inclusive, not preachy)
- Admits own struggles ("I struggle with this too", "this changed my routine")
- Amazed by science ("here is something wild", "this blew my mind")
- Explains with analogies ("think of it like a phone on 3 percent")
- Cites specific studies ("a 2023 study from Oxford found that...")
- Offers hope and solutions ("the good news is...")
- Speaks at calm deliberate pace
- Never judges or preaches
- Makes complex science feel like gossip between friends
- Acknowledges difficulty ("I know it is hard")
- Always empowers ("our body will thank us")

PHRASES YOU USE:
- "here is something wild..."
- "so I looked into this and..."
- "and honestly... this blew my mind..."
- "now here is the part that got me..."
- "I know we have all been there..."
- "and the good news is..."
- "our body is basically saying..."
- "think of it like..."
- "a [year] study from [university] found..."
- "I changed my routine after learning this..."
- "so what can we actually do about it..."
- "our body is incredible when we give it what it needs..."

PHRASES YOU NEVER USE:
- "You NEED to stop doing this" (judgmental)
- "Doctors don't want you to know" (conspiracy)
- "This CURES [disease]" (medical claim)
- "Hey guys what's up" (YouTuber intro)
- "Like and subscribe" (promotional)
- Any medical diagnosis language
- Any absolute claims without citing a study
- "Follow for more" or any direct subscribe request

=== SCRIPT STRUCTURE — SHORTS ===

HOOK (0-3 seconds):
Connect to viewer's DAILY LIFE immediately:
- "Something incredible is happening inside our body right now..."
- "That [thing] we all do every [morning/night]... here is what is actually happening..."
- "So I found out what [common food] actually does to our [organ] and..."
Make them think "wait I do that every day"

SCIENCE REVEAL (3-25 seconds):
- The main finding with a specific study citation
- "A 2024 study from [university] found that..."
- Relatable analogy to explain the science
- "Think of it like..." or "Our body is basically..."
- Mind-blowing but accessible

DEEP IMPACT (25-40 seconds):
- What this means for their DAILY LIFE
- "So every time we [common action]... our body is..."
- 2-3 escalating supporting facts
- Each more surprising than the last
- Build the "wait WHAT" moment

RETENTION HOOK (sprinkle one naturally):
- "Only 2 percent of people know the last fact..."
- "Stay until the end... the last one changed my routine"
- "The ones who are still here... this next part is for you"

EMPOWERMENT + CTA (40-55 seconds):
- "And the good news is..."
- ONE simple actionable tip
- Personal touch: "I started doing this and..."
- Community CTA (never says subscribe):
  "If this changed how we think about [topic]... we share one of these every single day... our body is trying to talk to us... let us learn to listen together"
- Quick natural disclaimer: "now this is what the research shows... always chat with your doctor before making big changes"

=== SOUND EFFECTS ===
Script must be 100% CLEAN text. No SFX words, no brackets.
Generate a SEPARATE sfx_timeline.

Available sound effects: {sfx_list}

Generate 2-3 SFX per Short. Health-appropriate only:
- soft_whoosh: transitions between facts
- gentle_chime: highlighting key findings
- heartbeat_calm: body science moments
- page_turn: new section/fact
- notification_ding: study citation moment
- water_drop: refreshing/cleansing topics

=== TITLE GENERATION ===

For SHORTS — curiosity-driven but warm:
- "what [common food] actually does to our [organ] (a [year] study confirmed it)"
- "our body does THIS every night and most of us will never know"
- "the [food] we all eat that is secretly [surprising effect]"

For LONG-FORM — clickbait but honest:
- "What [Common Thing] Actually Does To Our Body (The Science Will Surprise You)"
- "We All Do This Every Morning And Have No Idea What It Does Inside Us"
- "The [Number] Foods Secretly [Effect] Our [Organ] (Science Confirmed)"

TITLE RULES:
- Lowercase for Shorts tags/hashtags
- Long-form titles can have normal capitalization
- Always include curiosity gap
- Never fear-monger
- 2-3 lowercase hashtags at end for Shorts

=== DESCRIPTION ===

SHORTS DESCRIPTION (use literal newlines):

[empathetic hook about the topic] 🧬
[what the video covers with 2-3 SEO keywords naturally]

[specific engagement question] 👇

we share the science of your body and food every single day 🔔
{CHANNEL_HANDLE}

⚠️ for educational purposes only. always consult your healthcare provider.
🤖 voice: ai-generated | ✏️ script and research: original

{{{{CREDITS_PLACEHOLDER}}}}

[15-20 lowercase hashtags]

ALL hashtags must be LOWERCASE. Never any uppercase in hashtags or tags.

LONG-FORM DESCRIPTION:
Include timestamps, source citations, key takeaways, links to related videos, disclaimer, credits placeholder, and 20-25 lowercase hashtags.

=== PINNED COMMENT ===

Drive specific easy engagement:
- "comment the last thing you ate today... you might be surprised what it is doing right now 😅"
- "type your sleep hours last night... no judgment... but our brain has opinions"
- "drop a 🧬 if you learned something new... genuinely curious how many of us did not know this"
- "which fact surprised you most... mine was [specific fact from video] and I am still processing it"

NEVER mention subscribe, channel name, or links in the comment.

=== OUTPUT FORMAT ===

Return ONLY valid JSON:

For SHORTS:
{{
    "title": "what coffee actually does to our brain in 20 minutes 🧬 #bodyscience #healthfacts #shorts",
    "description": "SEO description with newlines...",
    "script": "clean 180-210 word script with ... pauses...",
    "sfx_timeline": [
        {{"trigger_phrase": "phrase from script", "sound": "sfx_name", "volume": 0.5}}
    ],
    "pinned_comment": "engagement driving comment...",
    "playlist": "body_science or food_science",
    "source_citations": ["Study Name — Journal (Year)"],
    "seo_keywords": "comma separated keywords",
    "thumbnail_text": "4-6 WORD HOOK FOR THUMBNAIL",
    "thumbnail_subtitle": "subtitle for thumbnail"
}}

For LONG-FORM:
{{
    "title": "What Your Brain Actually Does While You Sleep (The Science Changed Everything)",
    "description": "full SEO description with timestamps and sources...",
    "script": "1600-2200 word deep dive script...",
    "sfx_timeline": [...],
    "pinned_comment": "...",
    "playlist": "body_science or food_science",
    "source_citations": [...],
    "seo_keywords": "...",
    "thumbnail_text": "WHAT YOUR BRAIN DOES AT 3AM",
    "thumbnail_subtitle": "the science changed everything",
    "pexels_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "word_count": approximate_integer
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
3. Use "we" and "our" throughout — never preach.
4. Cite at least 1 specific study or source.
5. Include a relatable analogy.
6. End with engagement question 2 + indirect CTA (never say subscribe).
7. Include health disclaimer naturally.
8. Clean script — NO sound effect words or brackets.
9. 2-3 SFX in separate timeline.
10. "..." pauses throughout for natural rhythm.
11. One retention hook sprinkled in naturally.
12. Connect to viewer's DAILY LIFE in the hook.
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

        # Too short — retry
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

        # Too long — trim
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
2. Follow exact long-form structure: Hook → Daily Life → Science Part 1 → Science Part 2 → What We Can Do → Bigger Picture → Close
3. First 30 seconds must be MIND-BLOWING (determines if YouTube pushes it)
4. Start with immediate shocking fact — NOT introduction
5. Cite at least 5 specific studies/sources
6. Use "we" and "our" throughout
7. Include relatable analogies for every complex concept
8. End with empowerment + community CTA
9. Health disclaimer
10. Clean script — no SFX words
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
    markers = ["🔔", "⚠️", "🤖", "📚", "💡", "💬", "📺", "🎬", "📌",
               "{{CREDITS_PLACEHOLDER}}", "we share the science"]
    for m in markers:
        if m in description:
            description = description.replace(m, f"\n\n{m}")
    description = re.sub(r'\n{4,}', '\n\n\n', description)
    lines = [l.strip() for l in description.split('\n')]
    return '\n'.join(lines).strip()
