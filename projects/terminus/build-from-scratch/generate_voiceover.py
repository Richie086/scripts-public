#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.parse

def load_env():
    # Attempt to load from parent directory .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", "..", "..", "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip("'\"")
        except Exception:
            pass

def clean_markdown(md_text):
    # 1. Remove Mermaid blocks entirely
    md_text = re.sub(r"```mermaid.*?```", "", md_text, flags=re.DOTALL)
    
    # 2. Remove code blocks entirely (listening to full code blocks is awkward)
    md_text = re.sub(r"```.*?```", " [Code block omitted] ", md_text, flags=re.DOTALL)
    
    # 3. Clean up GitHub-style alerts (e.g. > [!IMPORTANT])
    md_text = re.sub(r">\s*\[!(IMPORTANT|NOTE|WARNING|CAUTION|TIP)\]", "", md_text, flags=re.IGNORECASE)
    
    # 4. Remove blockquote symbols at starts of lines
    md_text = re.sub(r"^\s*>\s*", "", md_text, flags=re.MULTILINE)
    
    # 5. Remove headers symbols (e.g. #, ##, ###)
    md_text = re.sub(r"^\s*#+\s*", "", md_text, flags=re.MULTILINE)
    
    # 6. Convert markdown links [Text](Url) to just Text
    md_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", md_text)
    
    # 7. Convert bold and italics (**Text**, *Text*) to just Text
    md_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", md_text)
    md_text = re.sub(r"\*([^*]+)\*", r"\1", md_text)
    
    # 8. Clean up table markup (remove dividers and pipes)
    md_text = re.sub(r"\|", " ", md_text)
    md_text = re.sub(r"^[-\s|]+$", "", md_text, flags=re.MULTILINE)
    
    # 9. Clean up multiple empty lines
    md_text = re.sub(r"\n\s*\n", "\n\n", md_text)
    
    return md_text.strip()

def chunk_text(text, max_chars=4000):
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if len(current_chunk) + len(p_clean) + 2 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = p_clean
        else:
            if current_chunk:
                current_chunk += "\n\n" + p_clean
            else:
                current_chunk = p_clean
                
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def main():
    load_env()
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please export it in your terminal: export ELEVENLABS_API_KEY=\"your_key\"", file=sys.stderr)
        sys.exit(1)
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(script_dir, "dev_workflow_guide.md")
    output_path = os.path.join(script_dir, "dev_workflow_guide.mp3")
    
    if not os.path.exists(md_path):
        print(f"Error: Target file not found at {md_path}", file=sys.stderr)
        sys.exit(1)
        
    print("Reading and cleaning markdown guide...")
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
        
    cleaned_text = clean_markdown(md_content)
    
    # Debug: Check if run in test-only mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=== TEST MODE: Cleaned Text ===")
        print(cleaned_text[:1000] + "\n...")
        print(f"Total cleaned characters: {len(cleaned_text)}")
        sys.exit(0)
        
    chunks = chunk_text(cleaned_text)
    print(f"Split text into {len(chunks)} chunks for API processing.")
    
    # Default Voice ID (User's cloned voice 'Richard')
    voice_id = "hh2saMRyaXl8c0mhWN6p"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    combined_audio = b""
    
    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1}/{len(chunks)} ({len(chunk)} characters)...")
        payload = {
            "text": chunk,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                audio_chunk = response.read()
                combined_audio += audio_chunk
                print(f"Chunk {idx + 1} processed successfully.")
        except Exception as e:
            print(f"Failed to synthesize chunk {idx + 1}: {e}", file=sys.stderr)
            sys.exit(1)
            
    print(f"Writing voiceover to {output_path}...")
    with open(output_path, "wb") as f:
        f.write(combined_audio)
        
    print("Voiceover generated successfully!")

if __name__ == "__main__":
    main()
