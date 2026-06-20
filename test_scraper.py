"""
Test script for the Reddit collector module.
Run: python test_scraper.py

Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env first.
"""
import json
from dotenv import load_dotenv
from reddit_leads.reddit_collector import get_reddit_client, collect_all_items

load_dotenv()

# Load config
with open("config.json") as f:
    config = json.load(f)

subreddits = config["subreddits"]
post_limit = config.get("posts_per_subreddit", 10)

print(f"Connecting to Reddit...")
reddit = get_reddit_client()
print(f"Connected. Fetching up to {post_limit} posts per subreddit from: {subreddits}\n")

items = collect_all_items(reddit, subreddits, processed_ids=set(), post_limit=post_limit)

print(f"\n{'='*60}")
print(f"Total new items collected: {len(items)}")
posts = [i for i in items if i["type"] == "post"]
comments = [i for i in items if i["type"] == "comment"]
print(f"  Posts   : {len(posts)}")
print(f"  Comments: {len(comments)}")
print(f"{'='*60}\n")

# Show first 5 items as a preview
for item in items[:5]:
    print(f"[{item['type'].upper()}] u/{item['username']} in r/{item['subreddit']}")
    print(f"  Title  : {item['post_title'][:80]}")
    print(f"  Content: {item['content'][:120]}...")
    print(f"  URL    : {item['url']}")
    print(f"  Time   : {item['timestamp']}")
    print()
