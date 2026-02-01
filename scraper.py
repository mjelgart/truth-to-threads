"""Fetch recent posts from Trump's Truth Social account."""

import logging
import re
from html import unescape

import requests

from config import TRUTH_SOCIAL_BASE_URL, TRUMP_ACCOUNT_ID, TRUTH_SOCIAL_FETCH_LIMIT

logger = logging.getLogger(__name__)

# Fallback: CNN maintains a live archive of Trump's Truth Social posts.
CNN_ARCHIVE_URL = "https://ix.cnn.io/data/truth-social/truth_archive.json"


def _strip_html(html: str) -> str:
    """Convert simple HTML (as returned by the Mastodon API) to plain text."""
    # Replace <br> and </p> with newlines
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>\s*<p>", "\n\n", text)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def _extract_media(post: dict) -> list[dict]:
    """Pull out media attachments from a Truth Social post.

    Returns a list of dicts with keys: type ("image" | "video"), url, description.
    """
    media = []
    for attachment in post.get("media_attachments", []):
        kind = attachment.get("type", "unknown")
        url = attachment.get("url") or attachment.get("remote_url")
        if kind in ("image", "gifv") and url:
            media.append({
                "type": "image",
                "url": url,
                "description": attachment.get("description", ""),
            })
        elif kind == "video" and url:
            media.append({
                "type": "video",
                "url": url,
                "description": attachment.get("description", ""),
            })
    return media


def fetch_posts(since_id: str | None = None) -> list[dict]:
    """Fetch recent original posts (no reblogs) from Trump's account.

    Returns posts oldest-first so we can cross-post in chronological order.

    Each returned dict has keys:
        id, created_at, text, url, media
    """
    posts = _fetch_from_api(since_id)
    if posts is None:
        logger.warning("Primary API failed, trying CNN archive fallback")
        posts = _fetch_from_cnn(since_id)
    return posts


def _fetch_from_api(since_id: str | None) -> list[dict] | None:
    """Try the Mastodon-compatible Truth Social API."""
    url = f"{TRUTH_SOCIAL_BASE_URL}/accounts/{TRUMP_ACCOUNT_ID}/statuses"
    params: dict = {
        "limit": TRUTH_SOCIAL_FETCH_LIMIT,
        "exclude_reblogs": "true",
    }
    if since_id:
        params["since_id"] = since_id

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Truth Social API request failed: %s", exc)
        return None

    raw_posts = resp.json()
    if not isinstance(raw_posts, list):
        logger.error("Unexpected API response type: %s", type(raw_posts))
        return None

    results = []
    for post in raw_posts:
        # Skip reblogs/retruths
        if post.get("reblog"):
            continue
        results.append({
            "id": post["id"],
            "created_at": post.get("created_at", ""),
            "text": _strip_html(post.get("content", "")),
            "url": post.get("url", f"https://truthsocial.com/@realDonaldTrump/{post['id']}"),
            "media": _extract_media(post),
        })

    # Return oldest first
    results.sort(key=lambda p: p["id"])
    return results


def _fetch_from_cnn(since_id: str | None) -> list[dict]:
    """Fallback: use the CNN archive JSON."""
    try:
        resp = requests.get(CNN_ARCHIVE_URL, timeout=30)
        resp.raise_for_status()
        raw_posts = resp.json()
    except requests.RequestException as exc:
        logger.error("CNN archive request failed: %s", exc)
        return []

    results = []
    for post in raw_posts:
        post_id = str(post.get("id", ""))
        if since_id and post_id <= since_id:
            continue
        # Skip retruths
        if post.get("reblog"):
            continue
        results.append({
            "id": post_id,
            "created_at": post.get("created_at", ""),
            "text": _strip_html(post.get("content", "")),
            "url": post.get("url", f"https://truthsocial.com/@realDonaldTrump/{post_id}"),
            "media": _extract_media(post),
        })

    results.sort(key=lambda p: p["id"])
    return results
