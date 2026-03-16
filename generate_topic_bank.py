"""
Run this LOCALLY to generate the initial topic bank.
python generate_topic_bank.py
"""

import json
from groq import Groq
import os

# Try to get from environment first
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-key-here")
client = Groq(api_key=GROQ_API_KEY)

def generate_topics(category: str, playlist: str, count: int = 50) -> list:
    print(f"Generating {count} topics for {playlist}...")
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"Generate exactly {count} unique viral health science topics for YouTube. Each topic should make someone think 'wait really?' Category: {category}. Return JSON array of objects with 'topic' and 'playlist' keys."
            },
            {
                "role": "user",
                "content": f"Generate {count} topics for {playlist} playlist. Return JSON: {{\"topics\": [{{\"topic\": \"...\", \"playlist\": \"{playlist}\"}}]}}"
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.95,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result.get("topics", [])

# Generate all topics
all_topics = []

try:
    all_topics.extend(generate_topics("What happens to our body when we do common daily activities", "body_science", 50))
    all_topics.extend(generate_topics("Surprising facts about human organs and bodily functions", "body_science", 50))
    all_topics.extend(generate_topics("Sleep brain exercise and health science facts", "body_science", 50))

    all_topics.extend(generate_topics("What common foods actually do to our body and organs", "food_science", 50))
    all_topics.extend(generate_topics("Food myths debunked and surprising nutrition facts", "food_science", 50))
    all_topics.extend(generate_topics("Hidden ingredients and food comparisons backed by science", "food_science", 50))

    # Save
    os.makedirs("data", exist_ok=True)
    with open("data/questions_bank.json", "w") as f:
        json.dump(all_topics, f, indent=2)

    print(f"Generated {len(all_topics)} topics")
    print(f"Body Science: {len([t for t in all_topics if t['playlist'] == 'body_science'])}")
    print(f"Food Science: {len([t for t in all_topics if t['playlist'] == 'food_science'])}")
except Exception as e:
    print(f"Error generating bank: {e}")
