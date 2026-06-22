"""
Test script for the AI analyzer module.
Run: python test_analyzer.py

Uses a small set of fake Reddit items so you can verify Gemini scoring
without needing live Reddit credentials.

Required in .env: GEMINI_API_KEY
Get a free key at: https://aistudio.google.com/app/apikey
"""
from dotenv import load_dotenv
from reddit_leads.ai_analyzer import analyze_all_items

load_dotenv()

SAMPLE_ITEMS = [
    {
        "id": "post_001",
        "type": "post",
        "username": "mba_hopeful_2025",
        "subreddit": "MBA",
        "post_title": "Is hiring an admissions consultant worth it for M7?",
        "content": (
            "I'm targeting Wharton and Booth for R1. My GMAT is 730 and GPA is 3.6 from a target undergrad. "
            "I've heard consultants can make a big difference but they're expensive. Has anyone used one? "
            "Would love to hear if it was worth the $5k-$10k investment."
        ),
        "url": "https://www.reddit.com/r/MBA/comments/001",
        "timestamp": "2025-09-01T10:00:00+00:00",
        "parent_title": None,
    },
    {
        "id": "comment_002",
        "type": "comment",
        "username": "gmat_warrior_99",
        "subreddit": "GMAT",
        "post_title": "Finally broke 700 after 3 attempts",
        "content": (
            "Just got a 710 on my third attempt. Honestly not sure if I should retake for a 730+ "
            "or just apply with this. Targeting Kellogg and Tuck. Round 1 deadline is in 6 weeks and "
            "my essays are nowhere near done. Feeling super overwhelmed."
        ),
        "url": "https://www.reddit.com/r/GMAT/comments/002",
        "timestamp": "2025-09-01T09:00:00+00:00",
        "parent_title": "Finally broke 700 after 3 attempts",
    },
    {
        "id": "comment_003",
        "type": "comment",
        "username": "random_user",
        "subreddit": "MBA",
        "post_title": "MBA memes thread",
        "content": "Lol same honestly",
        "url": "https://www.reddit.com/r/MBA/comments/003",
        "timestamp": "2025-09-01T08:00:00+00:00",
        "parent_title": "MBA memes thread",
    },
    {
        "id": "post_004",
        "type": "post",
        "username": "curious_about_mba",
        "subreddit": "gradadmissions",
        "post_title": "Is an MBA even worth it in 2025?",
        "content": (
            "I keep going back and forth. I have 3 years of work experience in consulting and make decent money. "
            "Would an MBA from a top 20 school actually move the needle for my career? Not sure what I'd even study."
        ),
        "url": "https://www.reddit.com/r/gradadmissions/comments/004",
        "timestamp": "2025-09-01T07:00:00+00:00",
        "parent_title": None,
    },
    {
        "id": "dm_005",
        "type": "dm",
        "username": "waitlisted_at_stern",
        "subreddit": "DM",
        "post_title": "Help with waitlist",
        "content": (
            "Hi, I saw your comment in r/MBA. I got waitlisted at Stern and Darden and have no idea what to do next. "
            "Do you offer waitlist consulting? I really need help crafting a strong update letter. Budget isn't an issue."
        ),
        "url": "https://www.reddit.com/message/messages/005",
        "timestamp": "2025-09-01T06:00:00+00:00",
        "parent_title": None,
    },
]

print("Running AI analysis on 5 sample items (1 will be pre-filtered)...\n")
results = analyze_all_items(SAMPLE_ITEMS, batch_size=5)

print(f"\n{'='*65}")
print(f"Results: {len(results)} items analyzed (sorted by lead score)")
print(f"{'='*65}\n")

for r in results:
    score = r.get("lead_score", 0)
    intent = r.get("intent_level", "?")
    bar = "█" * score + "░" * (10 - score)
    print(f"[{score:2d}/10] {bar}  {intent.upper()}")
    print(f"  u/{r['username']} ({r['type']}) — r/{r['subreddit']}")
    print(f"  Stage   : {r.get('applicant_stage')}")
    print(f"  Pain    : {r.get('pain_points')}")
    print(f"  Schools : {r.get('target_schools')}")
    print(f"  GMAT    : {r.get('gmat_gre_score')}")
    print(f"  Urgency : {r.get('urgency_signals')}")
    print(f"  Action  : {r.get('recommended_outreach')}")
    print(f"  Why     : {r.get('reasoning')}")
    print()
