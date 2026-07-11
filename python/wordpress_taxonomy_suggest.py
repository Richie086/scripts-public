#!/usr/bin/env python3
import os
import sys
import re
import json
import requests

def load_post_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    # Strip markdown code blocks to focus on text content
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    return text

def fetch_existing_taxonomies():
    # Try loading from the private scripts folder
    sys.path.insert(0, "/home/rtroiano/repositories/scripts/python")
    try:
        import wp_update
        auth = (wp_update.WP_USER, wp_update.WP_APP_PASSWORD)
        url = wp_update.WP_URL.rstrip("/")
    except Exception:
        # Fallback to anonymous API
        url = "https://extremesarcasm.org"
        auth = None
        
    categories = []
    tags = []
    
    # Fetch categories
    try:
        resp = requests.get(f"{url}/?rest_route=/wp/v2/categories&per_page=100", auth=auth, timeout=10)
        if resp.status_code == 200:
            categories = [{"id": c["id"], "name": c["name"]} for c in resp.json()]
    except Exception as e:
        print(f"Warning: Failed to fetch categories: {e}", file=sys.stderr)
        
    # Fetch tags (supports paging to fetch all tags)
    try:
        page = 1
        while True:
            resp = requests.get(f"{url}/?rest_route=/wp/v2/tags&per_page=100&page={page}", auth=auth, timeout=10)
            if resp.status_code == 200:
                page_tags = [{"id": t["id"], "name": t["name"]} for t in resp.json()]
                if not page_tags:
                    break
                tags.extend(page_tags)
                page += 1
            else:
                break
    except Exception as e:
        print(f"Warning: Failed to fetch tags: {e}", file=sys.stderr)
        
    return categories, tags

def suggest_taxonomies(text, categories, tags):
    suggested_categories = []
    suggested_tags = []
    
    # Normalize text for matching
    normalized_text = re.sub(r'\s+', ' ', text)
    
    # Match existing categories
    for cat in categories:
        cat_name = cat["name"]
        pattern = r'\b' + re.escape(cat_name) + r'\b'
        if re.search(pattern, normalized_text, re.IGNORECASE):
            suggested_categories.append(cat)
            
    # Match existing tags
    for tag in tags:
        tag_name = tag["name"]
        # Skip very short tags to avoid false positives (e.g. "ai" matched inside "air")
        if len(tag_name) <= 2:
            pattern = r'\b' + re.escape(tag_name) + r'\b'
        else:
            pattern = r'\b' + re.escape(tag_name) + r'\b'
            
        if re.search(pattern, normalized_text, re.IGNORECASE):
            suggested_tags.append(tag)
            
    return suggested_categories, suggested_tags

def extract_candidate_new_tags(text, existing_tags):
    existing_names = {t["name"].lower() for t in existing_tags}
    
    # Extract capitalized proper nouns
    words = re.findall(r'\b[A-Z][a-zA-Z0-9-]+\b', text)
    stop_words = {
        "The", "And", "But", "For", "This", "That", "With", "From", "Here", "There",
        "Linux", "Unix", "Windows", "Apple", "Google", "Microsoft", "Tux", "GPL", "BSD"
    }
    
    candidates = {}
    for w in words:
        if w in stop_words or len(w) < 3:
            continue
        if w.lower() in existing_names:
            continue
        candidates[w] = candidates.get(w, 0) + 1
        
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    return [name for name, freq in sorted_candidates[:10]]

def main():
    if len(sys.argv) < 2:
        print("Usage: wordpress_taxonomy_suggest.py <path_to_markdown_file>", file=sys.stderr)
        sys.exit(1)
        
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        text = load_post_text(filepath)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)
        
    print("Fetching existing taxonomies from WordPress...", file=sys.stderr)
    categories, tags = fetch_existing_taxonomies()
    
    print("Analyzing text and generating suggestions...", file=sys.stderr)
    suggested_categories, suggested_tags = suggest_taxonomies(text, categories, tags)
    candidate_new_tags = extract_candidate_new_tags(text, tags)
    
    output = {
        "suggested_categories": suggested_categories,
        "suggested_tags": suggested_tags,
        "candidate_new_tags": candidate_new_tags
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
