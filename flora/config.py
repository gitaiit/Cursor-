"""
Central configuration for the Flora / The Admit Co. lead generation pipeline.
Edit values here — you shouldn't need to touch collector/analyzer logic.
"""

# --- Reddit collection ---

SUBREDDITS = [
    "GMAT",
    "MBA",
    "gradadmissions",
    "MBAAdmissions",
    "business_school",
]

# How far back to look on each run. 24h matches a daily cron schedule.
LOOKBACK_HOURS = 24

# Skip posts/comments shorter than this many words — too short to carry signal.
MIN_WORD_COUNT = 15

# Reddit accounts to always ignore.
BOT_USERNAMES = {
    "AutoModerator",
}

# Max items pulled per subreddit per type, per run (safety cap on API usage).
MAX_SUBMISSIONS_PER_SUB = 100
MAX_COMMENTS_PER_SUB = 200

# --- File paths ---

SEEN_IDS_PATH = "data/seen_ids.json"
RAW_OUTPUT_PATH = "data/raw_leads.json"

# --- Reddit API (read from environment / .env) ---
# REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
