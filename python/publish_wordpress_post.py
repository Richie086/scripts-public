#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.parse
import urllib.request

def load_env():
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
                        os.environ[key] = val
        except Exception as e:
            print(f"Warning: Failed to load .env file: {e}", file=sys.stderr)

def main():
    load_env()
    parser = argparse.ArgumentParser(description="Publish a post to WordPress via Webhook")
    parser.add_argument("--title", required=True, help="Post Title")
    parser.add_argument("--content", help="Post Content")
    parser.add_argument("--file", help="Path to file containing Post Content")
    parser.add_argument("--webhook-url", help="WordPress Webhook URL")
    parser.add_argument("--status", default="private", help="Post Status (default: private)")
    parser.add_argument("--post-id", default="", help="Optional Post ID to update")
    args = parser.parse_args()

    if not args.content and not args.file:
        parser.error("Either --content or --file must be specified.")

    webhook_url = args.webhook_url or os.environ.get("WP_WEBHOOK_URL")
    if args.post_id:
        webhook_url = args.webhook_url or os.environ.get("WP_UPDATE_WEBHOOK_URL") or os.environ.get("WP_WEBHOOK_URL")

    if not webhook_url or webhook_url == "paste_your_uncanny_webhook_url_here":
        print("Error: Missing or invalid required webhook URL. Provide it via --webhook-url or set WP_WEBHOOK_URL.", file=sys.stderr)
        sys.exit(1)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = args.content

    content = content.strip()
    if content.startswith("[") and content.endswith("]"):
        content = f"<!-- wp:shortcode -->\n{content}\n<!-- /wp:shortcode -->"

    params = {
        "title": args.title,
        "content": content,
        "status": args.status
    }
    if args.post_id:
        params["post_id"] = args.post_id

    data = urllib.parse.urlencode(params).encode("utf-8")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        print(f"Triggering WordPress Webhook (POST) for post '{args.title}'...")
        req = urllib.request.Request(webhook_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            print("Webhook triggered successfully!")
            print(f"Response: {res_data}")
    except Exception as e:
        print(f"Failed to trigger webhook. Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
