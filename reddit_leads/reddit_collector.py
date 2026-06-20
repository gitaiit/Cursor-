import os
import time
from datetime import datetime, timezone

import praw
import prawcore


def get_reddit_client() -> praw.Reddit:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "admit_co_bot/1.0")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env")

    kwargs = dict(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    # Username + password required to read inbox/DMs
    if username and password:
        kwargs["username"] = username
        kwargs["password"] = password

    return praw.Reddit(**kwargs)


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


def fetch_inbox_dms(
    reddit: praw.Reddit,
    processed_ids: set,
    limit: int = 100,
) -> list[dict]:
    """
    Fetches private messages (DMs) from the authenticated account's inbox.
    Requires REDDIT_USERNAME and REDDIT_PASSWORD to be set in .env.
    Returns items with type="dm".
    """
    items = []
    try:
        for message in reddit.inbox.messages(limit=limit):
            item_id = f"dm_{message.id}"
            if item_id in processed_ids:
                continue
            if message.author is None:
                continue
            items.append({
                "id": item_id,
                "type": "dm",
                "username": str(message.author),
                "subreddit": "DM",
                "post_title": message.subject or "(no subject)",
                "content": message.body[:2000],
                "url": f"https://www.reddit.com/message/messages/{message.id}",
                "timestamp": datetime.fromtimestamp(message.created_utc, tz=timezone.utc).isoformat(),
                "parent_title": None,
            })
    except prawcore.exceptions.OAuthException:
        print("  [WARN] Cannot read inbox: REDDIT_USERNAME/REDDIT_PASSWORD not set or invalid.")
    except prawcore.exceptions.RequestException as e:
        print(f"  [WARN] Could not fetch inbox DMs: {e}")

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
        time.sleep(1)

    # Fetch inbox DMs (requires REDDIT_USERNAME + REDDIT_PASSWORD in .env)
    print("  Fetching inbox DMs...")
    dm_items = fetch_inbox_dms(reddit, processed_ids)
    for item in dm_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            all_items.append(item)
    print(f"  -> {len(dm_items)} new DMs")

    all_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return all_items
