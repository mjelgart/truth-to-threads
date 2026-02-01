"""Persist the ID of the last cross-posted Truth Social post."""

import json
import logging
import os

from config import STATE_FILE

logger = logging.getLogger(__name__)


def _ensure_dir():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def load_last_posted_id() -> str | None:
    """Return the last Truth Social post ID we successfully cross-posted, or None."""
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        return data.get("last_posted_id")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_last_posted_id(post_id: str) -> None:
    """Persist the most recently cross-posted Truth Social post ID."""
    _ensure_dir()
    with open(STATE_FILE, "w") as f:
        json.dump({"last_posted_id": post_id}, f, indent=2)
    logger.info("Saved last_posted_id: %s", post_id)
