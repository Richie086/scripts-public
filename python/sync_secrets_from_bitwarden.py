#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import argparse
import keyring

SERVICE_NAME = "antigravity_social_publish"

# List of all key names our scripts recognize
VALID_KEYS = [
    "FB_PAGE_ID",
    "FB_PAGE_ACCESS_TOKEN",
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET",
    "LINKEDIN_PERSON_URN",
    "LINKEDIN_ACCESS_TOKEN",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USERNAME",
    "REDDIT_PASSWORD",
    "REDDIT_SUBREDDIT",
    "REDDIT_USER_AGENT"
]

def run_cmd(args, env=None):
    try:
        res = subprocess.run(
            args,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return "", e.stderr.strip() if e.stderr else str(e)

def main():
    parser = argparse.ArgumentParser(description="Sync social media API credentials from Bitwarden CLI to Gnome Keyring.")
    parser.add_argument("--item-name", default="Developer API Keys", 
                        help="The name or search term of the Bitwarden vault item (default: 'Developer API Keys')")
    args = parser.parse_args()

    # 1. Verify bw is installed
    _, err = run_cmd(["which", "bw"])
    if err:
        print("Error: Bitwarden CLI ('bw') is not installed or not in your PATH.", file=sys.stderr)
        sys.exit(1)

    # 2. Check for BW_SESSION
    session = os.environ.get("BW_SESSION")
    if not session:
        print("\nError: BW_SESSION environment variable is not set.", file=sys.stderr)
        print("Please unlock your Bitwarden vault first by running:", file=sys.stderr)
        print("  export BW_SESSION=$(bw unlock --raw)", file=sys.stderr)
        print("and then re-run this script within the same terminal session.\n", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Searching for Bitwarden item matching '{args.item_name}'...")
    
    # We pass the session env variable to the subprocess
    env = os.environ.copy()
    env["BW_SESSION"] = session

    stdout, err = run_cmd(["bw", "list", "items", "--search", args.item_name], env=env)
    if err:
        print(f"Error querying Bitwarden vault: {err}", file=sys.stderr)
        sys.exit(1)

    if not stdout or stdout == "[]":
        print(f"Error: No items found in Bitwarden matching '{args.item_name}'.", file=sys.stderr)
        print("Please ensure you have a secure note or login item with this title.", file=sys.stderr)
        sys.exit(1)

    try:
        items = json.loads(stdout)
    except Exception as e:
        print(f"Error parsing Bitwarden response: {e}", file=sys.stderr)
        sys.exit(1)

    # Pick the best matching item
    item = items[0]
    if len(items) > 1:
        print(f"Warning: Found {len(items)} items matching '{args.item_name}'. Using the first match: '{item.get('name')}'")
    else:
        print(f"[+] Found item: '{item.get('name')}'")

    fields = item.get("fields", [])
    if not fields:
        print("[-] Warning: The selected item has no custom fields configured.", file=sys.stderr)
        print("Please add custom fields named exactly like the API variables (e.g. X_API_KEY, REDDIT_CLIENT_ID).", file=sys.stderr)
        sys.exit(0)

    updated_count = 0
    skipped_count = 0

    print("\nProcessing fields...")
    for field in fields:
        name = field.get("name")
        value = field.get("value")
        
        if not name or not value:
            continue

        # Check if the field name is a recognized key
        if name in VALID_KEYS:
            try:
                keyring.set_password(SERVICE_NAME, name, value)
                masked_val = value[:3] + "..." + value[-3:] if len(value) > 6 else "******"
                print(f"  [+] Saved {name} in Keyring: {masked_val}")
                updated_count += 1
            except Exception as e:
                print(f"  [-] Failed to save {name} to keyring: {e}", file=sys.stderr)
        else:
            print(f"  [-] Skipped field '{name}': Not in the list of recognized API keys.")
            skipped_count += 1

    print(f"\n[SUCCESS] Sync complete. Configured {updated_count} credentials, skipped {skipped_count} fields.")

if __name__ == "__main__":
    main()
