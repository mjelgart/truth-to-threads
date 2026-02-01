"""Dry run: test the scraper and post-splitting without publishing to Threads."""

import json
import logging

from scraper import fetch_posts
from publisher import split_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("DRY RUN — Fetching latest Trump Truth Social posts")
    print("=" * 60)

    posts = fetch_posts(since_id=None)

    if not posts:
        print("\nNo posts returned. Both the API and CNN fallback may be down.")
        return

    print(f"\nFetched {len(posts)} post(s)\n")

    for i, post in enumerate(posts, 1):
        print(f"--- Post {i} (ID: {post['id']}) ---")
        print(f"Date: {post['created_at']}")
        print(f"URL:  {post['url']}")
        if post["media"]:
            for m in post["media"]:
                print(f"Media: {m['type']} — {m['url']}")
        print(f"\nOriginal text ({len(post['text'])} chars):")
        print(post["text"][:500])
        if len(post["text"]) > 500:
            print(f"  ... [{len(post['text']) - 500} more chars]")

        chunks = split_text(post["text"])
        print(f"\nWould post as {len(chunks)} Threads post(s):")
        for j, chunk in enumerate(chunks, 1):
            print(f"  [{j}] ({len(chunk)} chars): {chunk[:120]}...")
        print()

    print("=" * 60)
    print(f"Total: {len(posts)} Truth(s) → would become "
          f"{sum(len(split_text(p['text'])) for p in posts)} Threads post(s)")
    print("=" * 60)


if __name__ == "__main__":
    main()
