import time
from datetime import datetime, timezone

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _fetch_json(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"  [WARN] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code != 200:
                print(f"  [WARN] HTTP {response.status_code} for {url}")
                return None
            return response.json()
        except requests.RequestException as e:
            print(f"  [WARN] Request error (attempt {attempt + 1}/3): {e}")
            time.sleep(5)
    return None


def _item_from_post(post: dict, subreddit: str):
    data = post.get("data", {})
    if data.get("selftext") in ("", "[removed]", "[deleted]") or not data.get("author"):
        return None
    return {
        "id": f"post_{data['id']}",
        "type": "post",
        "username": data["author"],
        "subreddit": subreddit,
        "post_title": data.get("title", ""),
        "content": data.get("selftext", "")[:2000],
        "url": f"https://www.reddit.com{data['permalink']}",
        "timestamp": datetime.fromtimestamp(data["created_utc"], tz=timezone.utc).isoformat(),
        "parent_title": None,
    }


def _item_from_comment(comment: dict, post_title: str, subreddit: str):
    data = comment.get("data", {})
    if data.get("body") in ("[removed]", "[deleted]") or not data.get("author"):
        return None
    return {
        "id": f"comment_{data['id']}",
        "type": "comment",
        "username": data["author"],
        "subreddit": subreddit,
        "post_title": post_title,
        "content": data.get("body", "")[:2000],
        "url": f"https://www.reddit.com{data['permalink']}",
        "timestamp": datetime.fromtimestamp(data["created_utc"], tz=timezone.utc).isoformat(),
        "parent_title": post_title,
    }


def _extract_comments(comment_list: list, post_title: str, subreddit: str) -> list[dict]:
    items = []
    for comment in comment_list:
        if comment.get("kind") != "t1":
            continue
        item = _item_from_comment(comment, post_title, subreddit)
        if item:
            items.append(item)
        # Recurse into replies
        replies = comment.get("data", {}).get("replies", "")
        if isinstance(replies, dict):
            children = replies.get("data", {}).get("children", [])
            items.extend(_extract_comments(children, post_title, subreddit))
    return items


def fetch_subreddit_items(
    subreddit_name: str,
    post_limit: int = 50,
    processed_ids: set = None,
) -> list[dict]:
    if processed_ids is None:
        processed_ids = set()

    items = []
    after = None
    fetched = 0

    while fetched < post_limit:
        batch = min(100, post_limit - fetched)
        url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit={batch}"
        if after:
            url += f"&after={after}"

        data = _fetch_json(url)
        if not data:
            break

        posts = data.get("data", {}).get("children", [])
        if not posts:
            break

        for post in posts:
            post_item = _item_from_post(post, subreddit_name)
            if post_item and post_item["id"] not in processed_ids:
                items.append(post_item)

            # Fetch comments for this post
            post_id = post.get("data", {}).get("id")
            permalink = post.get("data", {}).get("permalink")
            post_title = post.get("data", {}).get("title", "")

            if post_id and permalink:
                comments_url = f"https://www.reddit.com{permalink}.json?limit=500"
                comments_data = _fetch_json(comments_url)
                if comments_data and len(comments_data) > 1:
                    comment_children = comments_data[1].get("data", {}).get("children", [])
                    for c_item in _extract_comments(comment_children, post_title, subreddit_name):
                        if c_item["id"] not in processed_ids:
                            items.append(c_item)
                time.sleep(0.5)  # be polite between comment fetches

        after = data.get("data", {}).get("after")
        fetched += len(posts)
        if not after:
            break

    return items


def collect_all_items(
    subreddits: list[str],
    processed_ids: set,
    post_limit: int = 50,
) -> list[dict]:
    all_items = []
    seen_ids = set()

    for subreddit_name in subreddits:
        print(f"  Fetching r/{subreddit_name}...")
        items = fetch_subreddit_items(subreddit_name, post_limit, processed_ids)
        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)
        print(f"  -> {len(items)} new items from r/{subreddit_name}")
        time.sleep(2)  # be polite between subreddit requests

    all_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return all_items
