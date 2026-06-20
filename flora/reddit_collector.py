"""
Reddit collector for the Flora / The Admit Co. lead generation pipeline.

Pulls new posts and top-level comments from target subreddits within the
lookback window, applies basic noise filters, dedupes against previously
seen items, and writes a flat JSON file of raw records for the AI analyzer
to consume next.

Usage:
    python reddit_collector.py            # live run, needs Reddit API creds
    python reddit_collector.py --dry-run  # uses sample fixture data, no API calls
"""

import os
import json
import time
import argparse
from datetime import datetime, timezone

import config

try:
    import praw
except ImportError:
    praw = None

from dotenv import load_dotenv

load_dotenv()


def get_reddit_client():
    """Create an authenticated PRAW client from environment variables."""
    if praw is None:
        raise RuntimeError("praw is not installed. Run: pip install praw")

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "flora-lead-gen/0.1")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET. "
            "Set them in a .env file (see .env.example)."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def load_seen_ids(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_ids(path, seen_ids):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(sorted(seen_ids), f)


def word_count(text):
    return len((text or "").split())


def is_noise(author_name, body_text):
    """Return True if this item should be skipped before AI analysis."""
    if author_name in config.BOT_USERNAMES:
        return True
    if body_text in ("[deleted]", "[removed]", None, ""):
        return True
    if word_count(body_text) < config.MIN_WORD_COUNT:
        return True
    return False


def collect_submissions(reddit, subreddit_name, cutoff_ts, seen_ids):
    records = []
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=config.MAX_SUBMISSIONS_PER_SUB):
        if submission.created_utc < cutoff_ts:
            continue
        if submission.id in seen_ids:
            continue

        author_name = str(submission.author) if submission.author else "[deleted]"
        body_text = submission.selftext

        if is_noise(author_name, submission.title + " " + (body_text or "")):
            continue

        records.append({
            "type": "post",
            "id": submission.id,
            "username": author_name,
            "subreddit": subreddit_name,
            "title": submission.title,
            "content": body_text,
            "url": f"https://www.reddit.com{submission.permalink}",
            "created_utc": submission.created_utc,
            "timestamp": datetime.fromtimestamp(
                submission.created_utc, tz=timezone.utc
            ).isoformat(),
        })
        seen_ids.add(submission.id)
    return records


def collect_comments(reddit, subreddit_name, cutoff_ts, seen_ids):
    records = []
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.comments(limit=config.MAX_COMMENTS_PER_SUB):
        if comment.created_utc < cutoff_ts:
            continue
        if comment.id in seen_ids:
            continue

        author_name = str(comment.author) if comment.author else "[deleted]"
        body_text = comment.body

        if is_noise(author_name, body_text):
            continue

        # Title is the parent submission's title for context.
        try:
            parent_title = comment.submission.title
        except Exception:
            parent_title = ""

        records.append({
            "type": "comment",
            "id": comment.id,
            "username": author_name,
            "subreddit": subreddit_name,
            "title": parent_title,
            "content": body_text,
            "url": f"https://www.reddit.com{comment.permalink}",
            "created_utc": comment.created_utc,
            "timestamp": datetime.fromtimestamp(
                comment.created_utc, tz=timezone.utc
            ).isoformat(),
        })
        seen_ids.add(comment.id)
    return records


def run_live():
    reddit = get_reddit_client()
    cutoff_ts = time.time() - (config.LOOKBACK_HOURS * 3600)
    seen_ids = load_seen_ids(config.SEEN_IDS_PATH)

    all_records = []
    for sub_name in config.SUBREDDITS:
        print(f"Collecting from r/{sub_name} ...")
        posts = collect_submissions(reddit, sub_name, cutoff_ts, seen_ids)
        comments = collect_comments(reddit, sub_name, cutoff_ts, seen_ids)
        print(f"  {len(posts)} new posts, {len(comments)} new comments")
        all_records.extend(posts)
        all_records.extend(comments)

    save_seen_ids(config.SEEN_IDS_PATH, seen_ids)

    os.makedirs(os.path.dirname(config.RAW_OUTPUT_PATH), exist_ok=True)
    with open(config.RAW_OUTPUT_PATH, "w") as f:
        json.dump(all_records, f, indent=2)

    print(f"\nTotal new items collected: {len(all_records)}")
    print(f"Written to {config.RAW_OUTPUT_PATH}")
    return all_records


def run_dry():
    """Exercise the filtering logic against fixture data, no API calls."""
    fixture_path = os.path.join(os.path.dirname(__file__), "data", "sample_raw.json")
    with open(fixture_path, "r") as f:
        fixtures = json.load(f)

    kept = []
    for item in fixtures:
        text = (item.get("title", "") + " " + (item.get("content") or "")).strip()
        if is_noise(item.get("username"), text):
            print(f"  [filtered] {item['id']} -- {text[:50]!r}")
            continue
        kept.append(item)

    os.makedirs("data", exist_ok=True)
    with open(config.RAW_OUTPUT_PATH, "w") as f:
        json.dump(kept, f, indent=2)

    print(f"\nDry run: {len(kept)}/{len(fixtures)} items passed filters.")
    print(f"Written to {config.RAW_OUTPUT_PATH}")
    return kept


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Use sample fixture data instead of live Reddit API")
    args = parser.parse_args()

    if args.dry_run:
        run_dry()
    else:
        run_live()
