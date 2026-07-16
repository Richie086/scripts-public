---
name: post-to-pastebin
description: |
  Uploads a single file to a pastebin service (such as paste.rs) and returns the public URL.
---

# Post to Pastebin

This skill allows the agent to upload any single file from the local workspace to a free, anonymous pastebin service and display the resulting URL to the user.

## Instructions
1. Verify the target file exists.
2. Run curl to upload the file to `paste.rs`:
   ```bash
   curl --data-binary @<file_path> https://paste.rs
   ```
3. If `paste.rs` is unreachable, use `ix.io`:
   ```bash
   curl -F 'f:1=@<file_path>' ix.io
   ```
4. Output the URL clearly to the user.
