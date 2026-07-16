#!/usr/bin/env python3
import sys
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

def set_credential(key, value=None):
    if key not in VALID_KEYS:
        print(f"[-] Warning: '{key}' is not in the list of recognized keys. Storing anyway.")
    
    if not value:
        import getpass
        value = getpass.getpass(f"Enter value for {key}: ")
        
    try:
        keyring.set_password(SERVICE_NAME, key, value)
        print(f"[+] Successfully stored {key} in Gnome Keyring.")
    except Exception as e:
        print(f"[-] Failed to store {key}: {e}", file=sys.stderr)

def get_credential(key):
    try:
        val = keyring.get_password(SERVICE_NAME, key)
        if val:
            print(f"{key}: {val[:3]}...{val[-3:] if len(val) > 6 else ''} (Length: {len(val)})")
        else:
            print(f"{key}: Not set in keyring")
    except Exception as e:
        print(f"[-] Error retrieving {key}: {e}", file=sys.stderr)

def delete_credential(key):
    try:
        keyring.delete_password(SERVICE_NAME, key)
        print(f"[+] Successfully deleted {key} from Gnome Keyring.")
    except keyring.errors.PasswordDeleteError:
        print(f"[-] {key} was not found in Gnome Keyring.")
    except Exception as e:
        print(f"[-] Error deleting {key}: {e}", file=sys.stderr)

def list_credentials():
    print(f"Checking configured credentials in service '{SERVICE_NAME}':")
    for key in VALID_KEYS:
        try:
            val = keyring.get_password(SERVICE_NAME, key)
            status = "SET (Encrypted)" if val else "NOT SET"
            print(f"- {key}: {status}")
        except Exception:
            print(f"- {key}: Error checking")

def main():
    parser = argparse.ArgumentParser(description="Manage social media credentials in native Gnome Keyring.")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")
    
    # set
    set_parser = subparsers.add_parser("set", help="Set a credential value")
    set_parser.add_argument("key", help="The name of the credential key")
    set_parser.add_argument("--value", help="The value to set (omitting prompts for secret input)")
    
    # get
    get_parser = subparsers.add_parser("get", help="Show status/metadata of a key")
    get_parser.add_argument("key", help="The name of the credential key")
    
    # delete
    del_parser = subparsers.add_parser("delete", help="Delete a key")
    del_parser.add_argument("key", help="The name of the credential key")
    
    # list
    subparsers.add_parser("list", help="List all recognized keys and their status")
    
    args = parser.parse_args()
    
    if args.command == "set":
        set_credential(args.key, args.value)
    elif args.command == "get":
        get_credential(args.key)
    elif args.command == "delete":
        delete_credential(args.key)
    elif args.command == "list":
        list_credentials()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
