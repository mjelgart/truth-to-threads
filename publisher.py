"""Publish posts to Threads via the Meta Graph API."""

import logging
import time

import requests

from config import (
    THREADS_ACCESS_TOKEN,
    THREADS_API_BASE,
    THREADS_CHAR_LIMIT,
    THREADS_PUBLISH_DELAY_SECONDS,
    THREADS_USER_ID,
    POST_FOOTER,
    FOOTER_LENGTH,
)

logger = logging.getLogger(__name__)


def split_text(text: str) -> list[str]:
    """Split text into chunks that fit within the Threads character limit.

    Each chunk will have the footer appended, plus a part indicator if there
    are multiple chunks (e.g. "[1/3]").

    Splits on paragraph boundaries first, then sentence boundaries, then
    word boundaries as a last resort.
    """
    # If the whole thing fits in one post, just return it
    if len(text) + FOOTER_LENGTH <= THREADS_CHAR_LIMIT:
        return [text + POST_FOOTER]

    # We need to split. First figure out max content length per chunk.
    # Reserve space for footer + part indicator like " [1/3]" (max 7 chars)
    part_indicator_reserve = 7
    max_content = THREADS_CHAR_LIMIT - FOOTER_LENGTH - part_indicator_reserve

    chunks = _split_into_chunks(text, max_content)

    # Format with part indicators and footer
    total = len(chunks)
    result = []
    for i, chunk in enumerate(chunks, 1):
        if total > 1:
            result.append(f"{chunk} [{i}/{total}]{POST_FOOTER}")
        else:
            result.append(chunk + POST_FOOTER)
    return result


def _split_into_chunks(text: str, max_len: int) -> list[str]:
    """Recursively split text into chunks of at most max_len characters."""
    if len(text) <= max_len:
        return [text]

    # Try splitting on double-newline (paragraph boundary)
    split_point = _find_split_point(text, max_len, "\n\n")
    if split_point is None:
        # Try single newline
        split_point = _find_split_point(text, max_len, "\n")
    if split_point is None:
        # Try sentence boundary (period followed by space)
        split_point = _find_split_point(text, max_len, ". ")
        if split_point is not None:
            split_point += 1  # include the period
    if split_point is None:
        # Last resort: split on space
        split_point = text.rfind(" ", 0, max_len)
    if split_point is None or split_point <= 0:
        # Absolute last resort: hard cut
        split_point = max_len

    first = text[:split_point].rstrip()
    rest = text[split_point:].lstrip()

    return [first] + _split_into_chunks(rest, max_len)


def _find_split_point(text: str, max_len: int, delimiter: str) -> int | None:
    """Find the last occurrence of delimiter within the first max_len chars."""
    pos = text.rfind(delimiter, 0, max_len)
    return pos if pos > 0 else None


def publish_text_post(text: str) -> str | None:
    """Create and publish a text-only Threads post. Returns the post ID or None."""
    return _create_and_publish({"media_type": "TEXT", "text": text})


def publish_image_post(text: str, image_url: str) -> str | None:
    """Create and publish a Threads post with an image."""
    return _create_and_publish({
        "media_type": "IMAGE",
        "text": text,
        "image_url": image_url,
    })


def publish_video_post(text: str, video_url: str) -> str | None:
    """Create and publish a Threads post with a video."""
    return _create_and_publish({
        "media_type": "VIDEO",
        "text": text,
        "video_url": video_url,
    })


def _create_and_publish(params: dict) -> str | None:
    """Two-step Threads publish: create media container, wait, then publish."""
    params["access_token"] = THREADS_ACCESS_TOKEN

    # Step 1: create the media container
    create_url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads"
    try:
        resp = requests.post(create_url, data=params, timeout=30)
        resp.raise_for_status()
        creation_id = resp.json().get("id")
    except requests.RequestException as exc:
        logger.error("Failed to create Threads media container: %s", exc)
        return None

    if not creation_id:
        logger.error("No creation_id returned from Threads API")
        return None

    # Step 2: wait for server-side processing
    logger.info("Waiting %ds for Threads to process container %s",
                THREADS_PUBLISH_DELAY_SECONDS, creation_id)
    time.sleep(THREADS_PUBLISH_DELAY_SECONDS)

    # Step 3: publish
    publish_url = f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish"
    try:
        resp = requests.post(publish_url, data={
            "creation_id": creation_id,
            "access_token": THREADS_ACCESS_TOKEN,
        }, timeout=30)
        resp.raise_for_status()
        post_id = resp.json().get("id")
        logger.info("Published Threads post: %s", post_id)
        return post_id
    except requests.RequestException as exc:
        logger.error("Failed to publish Threads post: %s", exc)
        return None


def publish_truth(post: dict) -> bool:
    """Publish a Truth Social post to Threads. Handles splitting and media.

    Args:
        post: dict with keys: id, text, url, media (list of {type, url, description})

    Returns True if at least the first chunk was published successfully.
    """
    text = post["text"]
    media = post.get("media", [])

    chunks = split_text(text)
    first_chunk = True

    for chunk in chunks:
        if first_chunk and media:
            # Attach the first media item to the first chunk
            attachment = media[0]
            if attachment["type"] == "image":
                result = publish_image_post(chunk, attachment["url"])
            elif attachment["type"] == "video":
                result = publish_video_post(chunk, attachment["url"])
            else:
                result = publish_text_post(chunk)
        else:
            result = publish_text_post(chunk)

        if result is None and first_chunk:
            return False
        first_chunk = False

    return True
