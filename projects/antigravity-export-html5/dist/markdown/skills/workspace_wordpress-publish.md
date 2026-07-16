---
name: wordpress-publish
description: |
  Automates the process of writing, formatting, committing, pushing, and publishing markdown-based articles to a WordPress blog using GitHub permalinks and the publish_wordpress_post.py script.
---

# WordPress Publishing Automation

This skill guides the agent through the complete lifecycle of writing, formatting, uploading to GitHub, wrapping in a shortcode, and triggering a WordPress webhook to publish the article.

## Instructions

1. **Draft/Format the Article**:
   - Write the post in markdown format.
   - Save the file inside the `wordpress` folder of the `scripts-public` repository: `/home/rtroiano/repositories/scripts-public/scripts-public/wordpress/<filename>.md`.
   - **CRITICAL Formatting Step**: Scan the markdown content and remove the very first H1 header (e.g. `# Title`) from the file content since WordPress will handle the title separately. Keep any subsequent headers.

2. **Length Validation**:
   - Ensure the article content is no less than 5,000 words and no more than 15,000 words.
   - If the content is longer than 15,000 words, break/split it into two separate posts/files.

3. **Commit and Push to GitHub**:
   - Change directory to `/home/rtroiano/repositories/scripts-public/scripts-public`.
   - Stage the changes: `git add wordpress/<filename>.md`.
   - Run a security scan on the staged changes (`git diff --cached`) to ensure no credentials, passwords, tokens, or API keys are accidentally committed.
   - Commit the staged files locally: `git commit -m "Add wordpress blog post: <filename> [auto-doc]"` (using the `[auto-doc]` label to prevent verification loops).
   - **Approval Step**: Stop and explicitly prompt the user for confirmation before running `git push`.
   - Once approved, push the changes to the remote main branch.

4. **Construct the GitHub Permalink**:
   - Build the public raw GitHub URL for the committed markdown file.
   - Format: `https://raw.githubusercontent.com/Richie086/scripts-public/main/wordpress/<filename>.md`.

5. **Construct the Shortcode**:
   - Construct the Gutenberg shortcode block enclosing the raw URL:
     ```text
     [git-github-markdown url="https://raw.githubusercontent.com/Richie086/scripts-public/main/wordpress/<filename>.md"]
     ```

6. **Publish to WordPress**:
   - Execute the publishing Python script, passing the title, shortcode content, and desired status (defaulting to `private`):
     ```bash
     python3 /home/rtroiano/repositories/scripts-public/scripts-public/python/publish_wordpress_post.py --title "<Post Title>" --content '[git-github-markdown url="https://raw.githubusercontent.com/Richie086/scripts-public/main/wordpress/<filename>.md"]' --status "private"
     ```
   - Print the script's output and response to the user.
