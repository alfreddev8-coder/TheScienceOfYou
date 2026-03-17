"""
Content Source  TheScienceOfYou
Provides topics from multiple sources with fallback chain.
Priority: Question Bank  Google Trends  RSS Feeds  AI Generated
"""

import os
import json
import random
import time
import requests
import re
from datetime import datetime
import sys
# Debug path
print(f"DEBUG sys.path: {sys.path}")
from core.google_sheets import get_topics_from_sheet, mark_sheet_topic_used

QUESTIONS_BANK_FILE = "data/questions_bank.json"
USED_TOPICS_FILE = "data/used_topics.json"

# 
#  TOPIC TRACKING
# 
def is_health_related(topic_text: str) -> bool:
    """Checks if a topic is actually health/body/food related."""
    health_keywords = [
        "body", "health", "food", "eat", "sleep", "brain", "heart",
        "stomach", "gut", "liver", "kidney", "lung", "skin", "bone",
        "muscle", "blood", "cell", "immune", "vitamin", "protein",
        "sugar", "fat", "calorie", "nutrition", "diet", "exercise",
        "fitness", "weight", "disease", "cancer", "diabetes",
        "cholesterol", "pressure", "anxiety", "stress", "mental",
        "water", "drink", "coffee", "tea", "fruit", "vegetable",
        "nutrient", "supplement", "organic", "processed", "inflammation",
        "allergy", "infection", "bacteria", "virus", "hormone",
        "metabolism", "digestion", "breathing", "oxygen", "hydration",
        "fasting", "detox", "antioxidant", "fiber", "mineral",
    ]
    
    topic_lower = topic_text.lower()
    
    # Must contain at least ONE health keyword
    has_health = any(kw in topic_lower for kw in health_keywords)
    
    # Must NOT contain obvious non-health keywords
    non_health = [
        "movie", "book", "song", "album", "actor", "actress",
        "politician", "election", "game", "sport", "team",
        "stock", "crypto", "bitcoin", "nft", "fashion",
        "celebrity", "tv show", "series", "netflix", "disney",
    ]
    has_non_health = any(kw in topic_lower for kw in non_health)
    
    return has_health and not has_non_health


def load_used_topics() -> list:
    if os.path.exists(USED_TOPICS_FILE):
        with open(USED_TOPICS_FILE, "r") as f:
            return json.load(f)
    return []

def save_used_topic(topic: str, source: str = "bank"):
    used = load_used_topics()
    used.append({
        "topic": topic,
        "source": source,
        "date": datetime.now().isoformat(),
    })
    with open(USED_TOPICS_FILE, "w") as f:
        json.dump(used, f, indent=2)

# 
#  TIER 1: QUESTION BANK (Most Reliable)
# 
def get_topic_from_bank(playlist: str = None) -> dict | None:
    """
    Gets unused topic from pre-curated question bank.
    playlist: "body_science" or "food_science" or None (random)
    """
    if not os.path.exists(QUESTIONS_BANK_FILE):
        print("[Source] Question bank not found")
        return None
    
    try:
        with open(QUESTIONS_BANK_FILE, "r") as f:
            bank = json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"[Source] Question bank read error: {e}")
        return None
    
    if not bank:
        print("[Source] Question bank is empty")
        return None
    
    used = load_used_topics()
    available = [t for t in bank if t.get("topic") not in [u.get("topic") for u in used]]
    
    if playlist:
        available = [t for t in available if t.get("playlist") == playlist]
    
    if not available:
        print(f"[Source] Bank exhausted for playlist: {playlist}")
        # Reset bank usage (recycling topics from bank ONLY)
        non_bank_used = [u for u in used if u.get("source") != "bank"]
        with open(USED_TOPICS_FILE, "w") as f:
            json.dump(non_bank_used, f, indent=2)
        print("[Source] Reset bank usage  recycling topics")
        # Try again after reset
        available = bank if not playlist else [t for t in bank if t.get("playlist") == playlist]
    
    if not available:
        return None
    
    chosen = random.choice(available)
    save_used_topic(chosen["topic"], "bank")
    
    print(f"[Source] Bank topic: '{chosen['topic'][:60]}...' ({chosen.get('playlist', 'general')})")
    return chosen

# 
#  TIER 2: GOOGLE TRENDS (Trending Topics)
# 
def get_trending_health_topic() -> dict | None:
    """Gets trending health topic using pytrends with strict filtering."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("[Source] pytrends not installed")
        return None
    
    try:
        import time as t
        t.sleep(random.uniform(2, 5))
        
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        
        health_seeds = [
            "health benefits of",
            "what happens to body when",
            "is it healthy to eat",
            "foods that help with",
            "why does body",
        ]
        seed = random.choice(health_seeds)
        
        try:
            pytrends.build_payload([seed], timeframe='now 7-d', geo='US')
            related = pytrends.related_queries()
        except Exception as e:
            print(f"[Source] Google Trends build error: {e}")
            return None
        
        if not related or seed not in related:
            print("[Source] Google Trends: No results")
            return None
        
        # Safely check for rising queries
        rising = related[seed].get("rising")
        if rising is None or rising.empty:
            # Try top queries instead
            top = related[seed].get("top")
            if top is None or top.empty:
                print("[Source] Google Trends: No rising or top queries")
                return None
            queries_df = top
        else:
            queries_df = rising
        
        # Safely get query list
        try:
            if "query" in queries_df.columns:
                topics = queries_df["query"].tolist()
            else:
                topics = queries_df.iloc[:, 0].tolist()
        except (IndexError, KeyError):
            print("[Source] Google Trends: Cannot parse results")
            return None
        
        if not topics:
            return None
        
        # STRICT health filter
        health_topics = [t for t in topics if is_health_related(str(t))]
        
        if not health_topics:
            print("[Source] Google Trends: No health-related results")
            return None
        
        used = [u.get("topic", "") for u in load_used_topics()]
        fresh = [t for t in health_topics if t not in used]
        
        if fresh:
            chosen = random.choice(fresh[:5])
            save_used_topic(chosen, "google_trends")
            print(f"[Source] Google Trends: '{chosen}'")
            return {
                "topic": chosen,
                "playlist": categorize_topic(chosen),
                "source": "google_trends"
            }
        
        return None
        
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "rate" in error_str:
            print("[Source] Google Trends: Rate limited")
        else:
            print(f"[Source] Google Trends error: {e}")
        return None

# 
#  TIER 3: RSS HEALTH NEWS (Latest Studies)
# 
RSS_FEEDS = [
    {
        "name": "ScienceDaily Health",
        "url": "https://www.sciencedaily.com/rss/health_medicine.xml",
    },
    {
        "name": "ScienceDaily Nutrition",
        "url": "https://www.sciencedaily.com/rss/health_medicine/nutrition.xml",
    },
    {
        "name": "EurekAlert Health",
        "url": "https://www.eurekalert.org/rss/health.xml",
    },
    {
        "name": "NIH News",
        "url": "https://www.nih.gov/news-events/news-releases/feed",
    },
    {
        "name": "Harvard Health Blog",
        "url": "https://www.health.harvard.edu/blog/feed",
    },
]

def get_rss_health_topic() -> dict | None:
    """Gets latest health topic from RSS feeds with robust parsing."""
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        return None
    
    # Try multiple feeds
    random.shuffle(RSS_FEEDS)
    
    for feed in RSS_FEEDS[:3]:
        try:
            print(f"[Source] Checking RSS: {feed['name']}...")
            headers = {
                "User-Agent": "TheScienceOfYou Research Bot 1.0",
                "Accept": "application/rss+xml, application/xml, text/xml"
            }
            response = requests.get(feed["url"], headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"[Source] RSS {feed['name']}: HTTP {response.status_code}")
                continue
            
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError:
                print(f"[Source] RSS {feed['name']}: Parse error")
                continue
            
            # Try multiple item/entry formats
            items = (
                root.findall(".//item") or 
                root.findall(".//{http://www.w3.org/2005/Atom}entry") or
                root.findall(".//entry")
            )
            
            if not items:
                print(f"[Source] RSS {feed['name']}: No items")
                continue
            
            used = [u.get("topic", "") for u in load_used_topics()]
            
            for item in items[:15]:
                # Try multiple title tag formats
                title_elem = (
                    item.find("title") or
                    item.find("{http://www.w3.org/2005/Atom}title")
                )
                
                if title_elem is None or not title_elem.text:
                    continue
                
                title = title_elem.text.strip()
                
                # Skip if already used or too short
                if title in used or len(title) < 20:
                    continue
                
                # Skip non-health topics
                title_lower = title.lower()
                health_keywords = [
                    "health", "body", "brain", "food", "diet", "sleep",
                    "heart", "gut", "nutrition", "exercise", "disease",
                    "immune", "vitamin", "study", "research", "patients",
                    "cancer", "diabetes", "weight", "mental", "stress",
                    "muscle", "bone", "blood", "skin", "aging"
                ]
                if not any(kw in title_lower for kw in health_keywords):
                    continue
                
                # Get description if available
                desc = ""
                desc_elem = (
                    item.find("description") or
                    item.find("{http://www.w3.org/2005/Atom}summary") or
                    item.find("summary")
                )
                if desc_elem is not None and desc_elem.text:
                    desc = re.sub(r'<[^>]+>', '', desc_elem.text)[:500]
                
                save_used_topic(title, f"rss_{feed['name']}")
                print(f"[Source] RSS: '{title[:60]}...'")
                
                return {
                    "topic": title,
                    "description": desc,
                    "playlist": categorize_topic(title),
                    "source": f"rss_{feed['name']}",
                }
            
            print(f"[Source] No fresh topics from {feed['name']}")
            
        except Exception as e:
            print(f"[Source] RSS {feed['name']} error: {e}")
            continue
    
    return None

def get_quora_health_topic() -> dict | None:
    """Scrapes viral health questions from Quora topic pages."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[Source] beautifulsoup4 not installed")
        return None
    
    quora_topics = [
        "Human-Body", "Nutrition", "Health", "Food-Science",
        "Sleep", "Exercise", "Brain", "Diet-and-Nutrition",
        "Medical-Science", "Healthy-Eating",
    ]
    
    topic = random.choice(quora_topics)
    url = f"https://www.quora.com/topic/{topic}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[Source] Quora HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        questions = []
        for elem in soup.find_all(['span', 'a', 'div']):
            text = elem.get_text().strip()
            if '?' in text and 20 < len(text) < 200:
                text_lower = text.lower()
                health_kws = ['body', 'health', 'food', 'eat', 'sleep',
                              'brain', 'heart', 'stomach', 'muscle', 'skin',
                              'weight', 'vitamin', 'nutrient', 'organ', 'blood']
                if any(kw in text_lower for kw in health_kws):
                    questions.append(text)
        
        questions = list(set(questions))
        
        if questions:
            used = [u.get("topic", "") for u in load_used_topics()]
            fresh = [q for q in questions if q not in used]
            
            if fresh:
                chosen = random.choice(fresh[:5])
                save_used_topic(chosen, "quora")
                print(f"[Source] Quora: '{chosen[:60]}...'")
                return {
                    "topic": chosen,
                    "playlist": categorize_topic(chosen),
                    "source": "quora"
                }
        
        print(f"[Source] No Quora questions found for {topic}")
        return None
        
    except Exception as e:
        print(f"[Source] Quora error: {e}")
        return None

# 
#  TIER 4: AI GENERATED (Ultimate Fallback)
# 
def generate_ai_topic(playlist: str = None) -> dict | None:
    """Uses AI to generate a fresh health topic when all sources fail."""
    try:
        from groq import Groq
        from config import GROQ_API_KEY, PRIMARY_MODEL
        
        if not GROQ_API_KEY:
            return None
        
        client = Groq(api_key=GROQ_API_KEY)
        
        used = load_used_topics()
        recent = [u.get("topic", "") for u in used[-30:]]
        
        playlist_instruction = ""
        if playlist == "body_science":
            playlist_instruction = "The topic must be about the human body, organs, bodily functions, sleep, exercise, or health conditions."
        elif playlist == "food_science":
            playlist_instruction = "The topic must be about food, nutrition, ingredients, diet, cooking science, or eating habits."
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate unique viral health science topics for YouTube. "
                        "Topics should be mind-blowing facts about the human body or food science. "
                        "Format: A question or statement that makes someone think 'wait... really?' "
                        f"{playlist_instruction} "
                        "Return ONLY JSON: {\"topic\": \"your topic\", \"playlist\": \"body_science or food_science\"}"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate 1 viral health science topic. "
                        f"Must NOT be similar to: {json.dumps(recent)}\n"
                        f"Return JSON only."
                    )
                }
            ],
            model=PRIMARY_MODEL,
            temperature=1.0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        topic = result.get("topic", "")
        
        if topic:
            save_used_topic(topic, "ai_generated")
            print(f"[Source] AI topic: '{topic[:60]}...'")
            return {
                "topic": topic,
                "playlist": result.get("playlist", playlist or "body_science"),
                "source": "ai_generated"
            }
        
        return None
        
    except Exception as e:
        print(f"[Source] AI topic error: {e}")
        return None

# 
#  TOPIC CATEGORIZER
# 
def categorize_topic(topic: str) -> str:
    """Categorizes a topic as body_science or food_science."""
    topic_lower = topic.lower()
    
    food_keywords = [
        "food", "eat", "diet", "nutrition", "ingredient", "cook",
        "meal", "fruit", "vegetable", "sugar", "protein", "vitamin",
        "drink", "water", "coffee", "tea", "bread", "rice", "meat",
        "dairy", "snack", "breakfast", "lunch", "dinner", "calorie",
        "fat", "carb", "fiber", "mineral", "supplement", "organic",
        "processed", "recipe", "spice", "herb", "garlic", "honey",
    ]
    
    food_score = sum(1 for kw in food_keywords if kw in topic_lower)
    
    if food_score >= 2:
        return "food_science"
    elif food_score == 1 and "body" not in topic_lower and "brain" not in topic_lower:
        return "food_science"
    else:
        return "body_science"

# 
#  MAIN: GET NEXT TOPIC (Fallback Chain)
# 
def get_next_topic(playlist: str = None) -> dict:
    """
    Fallback chain:
    Bank/Sheets  Google Trends  Quora  RSS  AI Generated
    """
    # Tier 0: Google Sheets (Highest Priority)
    try:
        from core.google_sheets import get_topics_from_sheet, mark_sheet_topic_used
        sheet_topics = get_topics_from_sheet()
        if sheet_topics:
            chosen = random.choice(sheet_topics)
            mark_sheet_topic_used(chosen["row_index"])
            save_used_topic(chosen["topic"], "google_sheets")
            return chosen
    except Exception as e:
        print(f"[Source] Sheets skip: {e}")

    # Tier 1: Question Bank
    topic = get_topic_from_bank(playlist)
    if topic:
        return topic
    
    # Tier 2: Google Trends
    topic = get_trending_health_topic()
    if topic:
        return topic
    
    # Tier 3: Quora
    topic = get_quora_health_topic()
    if topic:
        return topic
    
    # Tier 4: RSS Feeds
    topic = get_rss_health_topic()
    if topic:
        return topic
    
    # Tier 5: AI Generated
    topic = generate_ai_topic(playlist)
    if topic:
        return topic
    
    # Emergency
    emergency = "What happens to our body when we drink water on an empty stomach"
    print(f"[Source] Emergency fallback topic")
    return {
        "topic": emergency,
        "playlist": playlist or "body_science",
        "source": "emergency_fallback"
    }
