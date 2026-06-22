"""
Test script for the Reddit collector module.
Run: python3 test_scraper.py

No credentials needed — uses Reddit's public JSON endpoints.
"""
import json
from reddit_leads.reddit_collector import collect_all_items

with open("config.json") as f:
    config = json.load(f)

subreddits = config["subreddits"]
post_limit = config.get("posts_per_subreddit", 10)

print(f"Fetching from Reddit (no login needed)...")
print(f"Subreddits : {subreddits}")
print(f"Post limit : {post_limit} per subreddit")
print()

items = collect_all_items(subreddits, processed_ids=set(), post_limit=post_limit)

print(f"\n{'='*60}")
print(f"Total new items collected: {len(items)}")
posts    = [i for i in items if i["type"] == "post"]
comments = [i for i in items if i["type"] == "comment"]
print(f"  Posts   : {len(posts)}")
print(f"  Comments: {len(comments)}")
print(f"{'='*60}\n")

# Preview first 5 items
for item in items[:5]:
    label = item["type"].upper()
    print(f"[{label}] u/{item['username']}  |  r/{item['subreddit']}")
    print(f"  Title  : {item['post_title'][:80]}")
    print(f"  Content: {item['content'][:120]}...")
    print(f"  URL    : {item['url']}")
    print(f"  Time   : {item['timestamp']}")
    print()
