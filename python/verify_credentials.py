#!/usr/bin/env python3
import os
import sys
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if not os.environ.get(k):
                        os.environ[k] = v

def check_facebook():
    token = get_cred("FB_PAGE_ACCESS_TOKEN")
    page_id = get_cred("FB_PAGE_ID")
    if not token or not page_id:
        return "Missing variables"
    url = f"https://graph.facebook.com/v18.0/{page_id}?access_token={token}"
    res = requests.get(url)
    if res.status_code == 200:
        return f"OK (Page Name: {res.json().get('name')})"
    return f"Error: {res.status_code} - {res.text}"

def check_x():
    api_key = get_cred("X_API_KEY")
    api_secret = get_cred("X_API_SECRET")
    access_token = get_cred("X_ACCESS_TOKEN")
    access_token_secret = get_cred("X_ACCESS_TOKEN_SECRET")
    if not all([api_key, api_secret, access_token, access_token_secret]):
        return "Missing variables"
    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
    res = requests.get("https://api.twitter.com/2/users/me", auth=auth)
    if res.status_code == 200:
        return f"OK (Username: @{res.json().get('data', {}).get('username')})"
    return f"Error: {res.status_code} - {res.text}"

def check_linkedin():
    token = get_cred("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return "Missing variable"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    if res.status_code == 200:
        data = res.json()
        urn = f"urn:li:person:{data.get('id')}"
        return f"OK (Name: {data.get('localizedFirstName')} {data.get('localizedLastName')}, URN: {urn})"
    return f"Error: {res.status_code} - {res.text}"

def check_reddit():
    client_id = get_cred("REDDIT_CLIENT_ID")
    client_secret = get_cred("REDDIT_CLIENT_SECRET")
    username = get_cred("REDDIT_USERNAME")
    password = get_cred("REDDIT_PASSWORD")
    user_agent = get_cred("REDDIT_USER_AGENT") or "verify-script:v1.0"
    if not all([client_id, client_secret, username, password]):
        return "Missing variables"
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {"grant_type": "password", "username": username, "password": password}
    res = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers={"User-Agent": user_agent})
    if res.status_code == 200 and "access_token" in res.json():
        return "OK (Authenticated successfully)"
    return f"Error: {res.status_code} - {res.text}"

def main():
    load_env()
    print("Facebook :", check_facebook())
    print("X (Twitter):", check_x())
    print("LinkedIn   :", check_linkedin())
    print("Reddit     :", check_reddit())

if __name__ == "__main__":
    main()
