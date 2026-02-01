# Truth to Threads

Automatically cross-posts Trump's Truth Social posts to a Threads account, running on a schedule via GitHub Actions.

## How it works

1. **Scraper** fetches recent posts from Truth Social's Mastodon-compatible API (with a CNN archive fallback)
2. **Publisher** posts them to Threads via the Meta Graph API, splitting long posts into multiple chunks
3. **State** is tracked in `data/state.json` (committed back to the repo) to avoid duplicate posts
4. A **GitHub Actions workflow** runs every 15 minutes

Each post ends with "— This was crossposted by a bot" to make clear this is an automated mirror, not an official account.

## Setup

### 1. Create a Meta Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com) and create an app
2. Add the **Threads** use case
3. Note your App ID and App Secret

### 2. Get a Threads access token

Authorize your Threads account and obtain a long-lived token (lasts 60 days, refreshable):

```bash
# Step 1: Open this URL in a browser and authorize
https://threads.net/oauth/authorize?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT_URI&scope=threads_basic,threads_content_publish&response_type=code

# Step 2: Exchange the code for a short-lived token
curl -X POST "https://graph.threads.net/oauth/access_token" \
  -d "client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&grant_type=authorization_code&redirect_uri=YOUR_REDIRECT_URI&code=YOUR_CODE"

# Step 3: Exchange for a long-lived token
curl "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=YOUR_APP_SECRET&access_token=SHORT_LIVED_TOKEN"
```

### 3. Configure GitHub Secrets

In your repo settings, add these secrets:

- `THREADS_USER_ID` — your Threads user ID
- `THREADS_ACCESS_TOKEN` — the long-lived access token from step 2

### 4. Enable the workflow

The workflow at `.github/workflows/crosspost.yml` runs every 15 minutes. You can also trigger it manually from the Actions tab.

## Local development

```bash
pip install -r requirements.txt
export THREADS_USER_ID=your_id
export THREADS_ACCESS_TOKEN=your_token
python main.py
```

## Token refresh

Long-lived Threads tokens expire after 60 days. Before expiry, refresh with:

```bash
curl "https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=YOUR_LONG_LIVED_TOKEN"
```

You'll need to update the `THREADS_ACCESS_TOKEN` secret in GitHub with the new token. Automating this refresh is a potential future enhancement.
