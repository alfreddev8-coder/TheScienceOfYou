"""
Run this ONCE locally to generate the topic bank.
python generate_topics.py
"""

import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)

def gen(prompt, count=50):
    """Generates topics using Groq."""
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Generate exactly {count} unique viral health science questions/topics for YouTube. Each should make someone think 'wait really?' Return JSON: {{\"topics\": [{{\"topic\": \"...\", \"playlist\": \"body_science or food_science\"}}]}}"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.95,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("topics", [])
    except Exception as e:
        print(f"Error: {e}")
        return []

all_topics = []
prompts = [
    ("What happens to our body when we do daily activities like sleeping eating drinking coffee exercising", "body_science", 50),
    ("Surprising facts about human organs brain heart liver gut kidneys", "body_science", 50),
    ("Sleep science brain facts exercise effects immune system aging", "body_science", 50),
    ("What common foods actually do to our body and organs", "food_science", 50),
    ("Food myths debunked nutrition facts ingredients people eat daily", "food_science", 50),
    ("Hidden ingredients banned foods country comparisons nutrition science", "food_science", 50),
]

for prompt, playlist, count in prompts:
    print(f"Generating {playlist} topics...")
    topics = gen(f"Generate {count} unique topics about: {prompt}. ALL must have playlist: {playlist}")
    for t in topics:
        t["playlist"] = playlist
    all_topics.extend(topics)
    time.sleep(2)

# Deduplicate
seen = set()
unique = []
for t in all_topics:
    if t["topic"] not in seen:
        seen.add(t["topic"])
        unique.append(t)

os.makedirs("data", exist_ok=True)
with open("data/questions_bank.json", "w") as f:
    json.dump(unique, f, indent=2)

print(f"\nGenerated {len(unique)} unique topics")
print(f"Body Science: {len([t for t in unique if t['playlist'] == 'body_science'])}")
print(f"Food Science: {len([t for t in unique if t['playlist'] == 'food_science'])}")
