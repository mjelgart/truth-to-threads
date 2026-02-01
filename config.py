import os

# Truth Social (Mastodon-compatible API)
TRUTH_SOCIAL_BASE_URL = "https://truthsocial.com/api/v1"
TRUMP_ACCOUNT_ID = "107780257626128497"
TRUTH_SOCIAL_FETCH_LIMIT = 20  # max per request

# Threads API (Meta Graph API)
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
THREADS_API_BASE = "https://graph.threads.net/v1.0"

# Posting behavior
THREADS_CHAR_LIMIT = 500
POST_FOOTER = "\n\n— This was crossposted by a bot"
FOOTER_LENGTH = len(POST_FOOTER)

# How long to wait between creating a Threads media container and publishing it.
# The Threads API needs time to process the container server-side.
THREADS_PUBLISH_DELAY_SECONDS = 30

# State file location (committed to repo for persistence across GH Actions runs)
STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "state.json")
