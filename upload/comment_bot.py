"""
Comment Bot  TheScienceOfYou
Posts unique AI-generated engagement-driving pinned comments.
"""

import random

FALLBACK_COMMENTS = [
    "genuine question... how many of us actually knew this before watching... because I definitely did not ",
    "comment the last thing you ate today... you might be surprised what it is doing right now",
    "type your sleep hours last night... no judgment but our brain has opinions about it",
    "drop a  if you learned something new... genuinely curious how many of us did not know this",
    "which fact surprised you most... mine was the one about our kidneys and I am still processing it",
    "comment your age and think about what your body has been doing for you all these years... wild right",
    "genuine question... what health topic should we break down next... we actually read every single comment",
    "the fact that our body does all this without us even thinking about it... type GRATEFUL if that hit different",
    "ok but which organ deserves the most appreciation... I am voting kidneys... they are so underrated",
    "type what time you are watching this... I bet 80 percent of us are watching at night ",
]

def get_comment(ai_comment: str = None) -> str:
    if ai_comment and len(ai_comment.strip()) > 10:
        return ai_comment.strip()
    return random.choice(FALLBACK_COMMENTS)

def post_pinned_comment(youtube, video_id: str, comment_text: str = None) -> str | None:
    if not youtube or not video_id:
        return None
    final = get_comment(comment_text)
    try:
        resp = youtube.commentThreads().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": final}}}}
        ).execute()
        cid = resp["snippet"]["topLevelComment"]["id"]
        youtube.comments().setModerationStatus(id=cid, moderationStatus="published", banAuthor=False).execute()
        print(f"[Comment] Pinned: '{final[:60]}...'")
        return cid
    except Exception as e:
        print(f"[Comment] Error: {e}")
        return None
