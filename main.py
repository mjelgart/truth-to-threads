"""Orchestrator: fetch new Truth Social posts and cross-post them to Threads."""

import logging
import sys

from config import THREADS_ACCESS_TOKEN, THREADS_USER_ID
from scraper import fetch_posts
from state import load_last_posted_id, save_last_posted_id
from publisher import publish_truth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        logger.error("THREADS_ACCESS_TOKEN and THREADS_USER_ID must be set")
        sys.exit(1)

    last_id = load_last_posted_id()
    logger.info("Last posted ID: %s", last_id)

    posts = fetch_posts(since_id=last_id)
    if not posts:
        logger.info("No new posts found")
        return

    logger.info("Found %d new post(s) to cross-post", len(posts))

    for post in posts:
        logger.info("Cross-posting Truth %s: %.80s...", post["id"], post["text"])
        success = publish_truth(post)
        if success:
            save_last_posted_id(post["id"])
            logger.info("Successfully cross-posted Truth %s", post["id"])
        else:
            logger.error("Failed to cross-post Truth %s, stopping", post["id"])
            sys.exit(1)

    logger.info("Done — cross-posted %d post(s)", len(posts))


if __name__ == "__main__":
    main()
