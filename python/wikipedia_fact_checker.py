#!/usr/bin/env python3
import os
import sys
import re
import json
import urllib.request
import urllib.parse

def get_sentences(text):
    # Strip markdown code blocks to avoid checking code syntax
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    abbreviations = {
        "e.g.", "i.e.", "vs.", "mr.", "mrs.", "dr.", "jan.", "feb.", "mar.", 
        "apr.", "jun.", "jul.", "aug.", "sept.", "oct.", "nov.", "dec.", "u.s.", "st."
    }
    
    sentences = []
    current_start = 0
    for match in re.finditer(r'[.!?]\s+(?=[A-Z0-9])', text):
        end_idx = match.start() + 1
        last_space = text.rfind(' ', current_start, end_idx)
        last_word = text[last_space + 1:end_idx].lower()
        if last_word in abbreviations or (len(last_word) == 2 and last_word[1] == '.'):
            continue
        sentences.append(text[current_start:match.end()].strip())
        current_start = match.end()
        
    if current_start < len(text):
        remaining = text[current_start:].strip()
        if remaining:
            sentences.append(remaining)
            
    return [s for s in sentences if len(s) > 15]

def score_sentence(s):
    score = 0
    # Years 19xx or 20xx
    if re.search(r'\b(19\d{2}|20\d{2})\b', s):
        score += 5
    # Version numbers
    if re.search(r'\b\d+\.\d+(?:\.\d+)?\b', s):
        score += 3
    # Key historical nouns
    keywords = [
        "Linus", "Torvalds", "Stallman", "Thompson", "Ritchie", "Tanenbaum", 
        "AT&T", "Bell Labs", "IBM", "Intel", "Microsoft", "Red Hat", "SCO", 
        "Novell", "GNU", "BSD", "POSIX", "Tux", "Hurd", "Slackware", "Debian", 
        "SUSE", "lawsuit", "copyright", "license", "trademark", "GPL", "Linux", "Unix"
    ]
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', s, re.IGNORECASE):
            score += 2
    return score

def extract_query(s):
    keywords = [
        "Linus", "Torvalds", "Stallman", "Thompson", "Ritchie", "Tanenbaum", 
        "AT&T", "Bell Labs", "IBM", "Intel", "Microsoft", "Red Hat", "SCO", 
        "Novell", "GNU", "BSD", "POSIX", "Tux", "Hurd", "Slackware", "Debian", "SUSE"
    ]
    entities = []
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', s, re.IGNORECASE):
            entities.append(kw)
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', s)
    query_parts = entities + years
    if not query_parts:
        # Fallback to first 8 words
        words = [w for w in re.findall(r'\b\w+\b', s) if len(w) > 3][:8]
        return " ".join(words)
    return " ".join(query_parts[:6])

def search_wikipedia(query):
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": 1
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityFactChecker/1.0 (contact: admin@extremesarcasm.org)"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                return search_results[0]["title"]
    except Exception as e:
        print(f"Warning: Failed to search Wikipedia for '{query}': {e}", file=sys.stderr)
    return None

def get_wikipedia_summary(title):
    safe_title = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityFactChecker/1.0 (contact: admin@extremesarcasm.org)"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "title": data.get("title"),
                "extract": data.get("extract"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page")
            }
    except Exception as e:
        print(f"Warning: Failed to fetch summary for '{title}': {e}", file=sys.stderr)
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: wikipedia_fact_checker.py <path_to_markdown_file>", file=sys.stderr)
        sys.exit(1)
        
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)
        
    sentences = get_sentences(content)
    scored_sentences = []
    for s in sentences:
        score = score_sentence(s)
        if score >= 5:
            scored_sentences.append((score, s))
            
    # Sort by score descending and take top 25 claims
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    claims = [s for _, s in scored_sentences[:25]]
    
    results = []
    print(f"Processing {len(claims)} potential historical/factual claims...", file=sys.stderr)
    for i, claim in enumerate(claims, 1):
        query = extract_query(claim)
        print(f"[{i}/{len(claims)}] Querying Wikipedia for: '{query}'...", file=sys.stderr)
        title = search_wikipedia(query)
        summary_info = None
        if title:
            summary_info = get_wikipedia_summary(title)
            
        results.append({
            "claim": claim,
            "query": query,
            "wikipedia_title": title,
            "wikipedia_summary": summary_info.get("extract") if summary_info else None,
            "wikipedia_url": summary_info.get("url") if summary_info else None
        })
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
