#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import keyring
from requests_oauthlib import OAuth1

SERVICE_NAME = "antigravity_social_publish"

def get_cred(key):
    # 1. Check direct env
    val = os.environ.get(key)
    if val:
        return val
    # 2. Check Keyring
    try:
        val = keyring.get_password(SERVICE_NAME, key)
        if val:
            return val
    except Exception:
        pass
    return None

def load_env():
    """Loads environment variables from the parent directory's .env file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if not os.environ.get(key):
                            os.environ[key] = val
        except Exception as e:
            print(f"Warning: Failed to load .env file: {e}", file=sys.stderr)

def post_to_facebook(title, url_to_post, message, dry_run=False):
    """Publishes a link/message to a Facebook Page."""
    print("\n--- Facebook Posting ---")
    page_id = get_cred("FB_PAGE_ID")
    access_token = get_cred("FB_PAGE_ACCESS_TOKEN")

    if not page_id or not access_token:
        print("[-] Missing FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN. Skipping Facebook.", file=sys.stderr)
        return False

    api_url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    payload = {
        "message": message,
        "link": url_to_post,
        "access_token": access_token
    }

    if dry_run:
        print(f"[DRY-RUN] Would POST to {api_url}")
        print(f"[DRY-RUN] Payload: {payload}")
        return True

    try:
        response = requests.post(api_url, data=payload, timeout=10)
        res_data = response.json()
        if response.status_code == 200:
            print(f"[+] Successfully posted to Facebook! Post ID: {res_data.get('id')}")
            return True
        else:
            print(f"[-] Facebook API Error (Status {response.status_code}): {res_data}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[-] Facebook Connection Error: {e}", file=sys.stderr)
        return False

def post_to_x(message, dry_run=False):
    """Publishes a tweet to X (formerly Twitter) using OAuth 1.0a User Context."""
    print("\n--- X (Twitter) Posting ---")
    api_key = get_cred("X_API_KEY")
    api_secret = get_cred("X_API_SECRET")
    access_token = get_cred("X_ACCESS_TOKEN")
    access_token_secret = get_cred("X_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("[-] Missing X API credentials (X_API_KEY, X_API_SECRET, etc.). Skipping X.", file=sys.stderr)
        return False

    api_url = "https://api.twitter.com/2/tweets"
    payload = {"text": message}

    if dry_run:
        print(f"[DRY-RUN] Would POST to {api_url}")
        print(f"[DRY-RUN] Payload: {payload}")
        return True

    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

    try:
        response = requests.post(api_url, json=payload, auth=auth, timeout=10)
        res_data = response.json()
        if response.status_code in (200, 201):
            tweet_id = res_data.get("data", {}).get("id")
            print(f"[+] Successfully posted to X! Tweet ID: {tweet_id}")
            return True
        else:
            print(f"[-] X API Error (Status {response.status_code}): {res_data}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[-] X Connection Error: {e}", file=sys.stderr)
        return False

def post_to_linkedin(title, url_to_post, message, dry_run=False):
    """Publishes an article share to LinkedIn using UGC Share API."""
    print("\n--- LinkedIn Posting ---")
    person_urn = get_cred("LINKEDIN_PERSON_URN")
    access_token = get_cred("LINKEDIN_ACCESS_TOKEN")

    if not person_urn or not access_token:
        print("[-] Missing LINKEDIN_PERSON_URN or LINKEDIN_ACCESS_TOKEN. Skipping LinkedIn.", file=sys.stderr)
        return False

    api_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": message
                },
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": title
                        },
                        "originalUrl": url_to_post,
                        "title": {
                            "text": title
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    if dry_run:
        print(f"[DRY-RUN] Would POST to {api_url}")
        print(f"[DRY-RUN] Headers: {headers}")
        print(f"[DRY-RUN] Payload: {payload}")
        return True

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        if response.status_code in (200, 201):
            post_id = res_data.get("id")
            print(f"[+] Successfully posted to LinkedIn! Post URN: {post_id}")
            return True
        else:
            print(f"[-] LinkedIn API Error (Status {response.status_code}): {res_data}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[-] LinkedIn Connection Error: {e}", file=sys.stderr)
        return False

def post_to_reddit(title, url_to_post, message, dry_run=False):
    """Publishes a link post to a subreddit on Reddit."""
    print("\n--- Reddit Posting ---")
    client_id = get_cred("REDDIT_CLIENT_ID")
    client_secret = get_cred("REDDIT_CLIENT_SECRET")
    username = get_cred("REDDIT_USERNAME")
    password = get_cred("REDDIT_PASSWORD")
    subreddit = get_cred("REDDIT_SUBREDDIT") or "test"
    user_agent = get_cred("REDDIT_USER_AGENT") or "social-publisher-script:v1.0"

    if not all([client_id, client_secret, username, password]):
        print("[-] Missing Reddit credentials. Skipping Reddit.", file=sys.stderr)
        return False

    if dry_run:
        print("[DRY-RUN] Would authenticate with Reddit via /api/v1/access_token")
        print(f"[DRY-RUN] Would POST to https://oauth.reddit.com/api/submit in r/{subreddit}")
        print(f"[DRY-RUN] Submit payload: sr={subreddit}, kind=link, title={title}, url={url_to_post}")
        return True

    try:
        # 1. Authenticate to get OAuth Access Token
        auth_url = "https://www.reddit.com/api/v1/access_token"
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        auth_data = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        auth_headers = {"User-Agent": user_agent}
        
        token_res = requests.post(auth_url, auth=auth, data=auth_data, headers=auth_headers, timeout=10)
        if token_res.status_code != 200:
            print(f"[-] Reddit Auth failed (Status {token_res.status_code}): {token_res.text}", file=sys.stderr)
            return False

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            print(f"[-] Reddit Auth failed to return access token: {token_data}", file=sys.stderr)
            return False

        # 2. Submit Link to subreddit
        submit_url = "https://oauth.reddit.com/api/submit"
        submit_headers = {
            "User-Agent": user_agent,
            "Authorization": f"Bearer {access_token}"
        }
        submit_payload = {
            "sr": subreddit,
            "kind": "link",
            "title": title,
            "url": url_to_post
        }
        
        response = requests.post(submit_url, data=submit_payload, headers=submit_headers, timeout=10)
        res_data = response.json()
        if response.status_code == 200 and res_data.get("json", {}).get("errors") == []:
            post_data = res_data.get("json", {}).get("data", {})
            print(f"[+] Successfully posted to Reddit! Subreddit: r/{subreddit}, URL: {post_data.get('url')}")
            return True
        else:
            print(f"[-] Reddit API Error (Status {response.status_code}): {res_data}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"[-] Reddit Connection/Posting Error: {e}", file=sys.stderr)
        return False

def main():
    load_env()
    
    parser = argparse.ArgumentParser(description="Publish article links and messages to social networks.")
    parser.add_argument("--title", required=True, help="Title of the article/post")
    parser.add_argument("--url", required=True, help="Public URL of the article")
    parser.add_argument("--message", help="Custom text message (fallbacks to a default template)")
    parser.add_argument("--platforms", default="facebook,x,linkedin,reddit", 
                        help="Comma-separated list of target platforms (default: facebook,x,linkedin,reddit)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate API requests without executing them")
    
    args = parser.parse_args()

    message = args.message or f"New article published: {args.title}\nRead it here: {args.url}"
    platforms = [p.strip().lower() for p in args.platforms.split(",")]
    
    print(f"Preparing to publish: '{args.title}'")
    print(f"URL: {args.url}")
    print(f"Message: {message}")
    if args.dry_run:
        print("[!] Running in DRY-RUN mode.")

    success_map = {}

    if "facebook" in platforms:
        success_map["facebook"] = post_to_facebook(args.title, args.url, message, args.dry_run)
        
    if "x" in platforms or "twitter" in platforms:
        success_map["x"] = post_to_x(message, args.dry_run)
        
    if "linkedin" in platforms:
        success_map["linkedin"] = post_to_linkedin(args.title, args.url, message, args.dry_run)
        
    if "reddit" in platforms:
        success_map["reddit"] = post_to_reddit(args.title, args.url, message, args.dry_run)

    print("\n=== Summary ===")
    all_success = True
    for platform, success in success_map.items():
        status = "Success" if success else "Failed/Skipped"
        print(f"- {platform.capitalize()}: {status}")
        if not success:
            all_success = False

    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()
