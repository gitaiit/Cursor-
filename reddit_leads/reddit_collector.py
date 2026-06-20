import os
import time
import json
from datetime import datetime, timezone

import praw
import prawcore


def get_reddit_client() -> praw.Reddit:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "admit_co_bot/1.0")

    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def _item_from_post(post) -> dict | None:
    if post.author is None or post.selftext in ("[removed]", "[deleted]", ""):
        return None
    return {
        "id": f"post_{post.id}",
        "type": "post",
        "username": str(post.author),
        "subreddit": str(post.subreddit),
        "post_title": post.title,
        "content": post.selftext[:2000],
        "url": f"https://www.reddit.com{post.permalink}",
        "timestamp": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
        "parent_title": None,
    }


def _item_from_comment(comment, post_title: str) -> dict | None:
    if comment.author is None or comment.body in ("[removed]", "[deleted]"):
        return None
    return {
        "id": f"comment_{comment.id}",
        "type": "comment",
        "username": str(comment.author),
        "subreddit": str(comment.subreddit),
        "post_title": post_title,
        "content": comment.body[:2000],
        "url": f"https://www.reddit.com{comment.permalink}",
        "timestamp": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
        "parent_title": post_title,
    }


def fetch_subreddit_items(
    reddit: praw.Reddit,
    subreddit_name: str,
    post_limit: int = 50,
    processed_ids: set = None,
) -> list[dict]:
    if processed_ids is None:
        processed_ids = set()

    items = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = list(subreddit.new(limit=post_limit))
    except prawcore.exceptions.RequestException as e:
        print(f"  [WARN] Could not fetch r/{subreddit_name}: {e}")
        return items

    for post in posts:
        post_item = _item_from_post(post)
        if post_item and post_item["id"] not in processed_ids:
            items.append(post_item)

        # Fetch all comments for this post
        try:
            post.comments.replace_more(limit=0)  # flatten MoreComments objects
            for comment in post.comments.list():
                c_item = _item_from_comment(comment, post.title)
                if c_item and c_item["id"] not in processed_ids:
                    items.append(c_item)
        except prawcore.exceptions.RequestException as e:
            print(f"  [WARN] Could not fetch comments for {post.id}: {e}")
            continue

    return items


def collect_all_items(
    reddit: praw.Reddit,
    subreddits: list[str],
    processed_ids: set,
    post_limit: int = 50,
) -> list[dict]:
    all_items = []
    seen_ids = set()

    for subreddit_name in subreddits:
        print(f"  Fetching r/{subreddit_name}...")
        items = fetch_subreddit_items(reddit, subreddit_name, post_limit, processed_ids)
        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)
        print(f"  -> {len(items)} new items from r/{subreddit_name}")
        time.sleep(1)  # be polite between subreddit requests

    all_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return all_items
