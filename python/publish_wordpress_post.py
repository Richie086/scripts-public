#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.parse
import urllib.request

def main():
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

    query_string = urllib.parse.urlencode(params)
    separator = "&" if "?" in webhook_url else "?"
    full_url = f"{webhook_url}{separator}{query_string}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        print(f"Triggering WordPress Webhook for post '{args.title}'...")
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            print("Webhook triggered successfully!")
            print(f"Response: {res_data}")
    except Exception as e:
        print(f"Failed to trigger webhook. Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
