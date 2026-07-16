---
name: social-publish
description: |
  Allows the agent to post articles/links to Facebook, X (Twitter), LinkedIn, and Reddit using the publish_social.py script.
---

# Social Media Publishing Automation

This skill allows the agent to automatically publish links and summaries of new articles to Facebook, X (formerly Twitter), LinkedIn, and Reddit.

## Instructions

1. **Verify Prerequisites**:
   - Check if the credentials for the target social media networks are configured in `/home/rtroiano/repositories/scripts-public/scripts-public/.env`.
   - Refer to `/home/rtroiano/repositories/scripts-public/scripts-public/.env.example` for the list of required variables:
     - **Facebook**: `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`
     - **X (Twitter)**: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
     - **LinkedIn**: `LINKEDIN_PERSON_URN`, `LINKEDIN_ACCESS_TOKEN`
     - **Reddit**: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_SUBREDDIT`, `REDDIT_USER_AGENT`

2. **Formulate the Command**:
   - Run the publishing python script from the `scripts-public` repository using its virtual environment:
     ```bash
     /home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/publish_social.py --title "<Article Title>" --url "<Article URL>"
     ```
   - **Custom Message**: To specify a custom message (instead of the default "New article published: <Title>\nRead it here: <URL>"), add the `--message` flag:
     ```bash
     /home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/publish_social.py --title "<Article Title>" --url "<Article URL>" --message "<Custom message content>"
     ```
   - **Specific Platforms**: To publish to a subset of platforms, use the `--platforms` flag (e.g. `--platforms "x,reddit"`):
     ```bash
     /home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/publish_social.py --title "<Article Title>" --url "<Article URL>" --platforms "x,reddit"
     ```
   - **Dry Run (Simulation)**: To simulate the requests without making real API calls:
     ```bash
     /home/rtroiano/repositories/scripts-public/scripts-public/.venv/bin/python /home/rtroiano/repositories/scripts-public/scripts-public/python/publish_social.py --title "<Article Title>" --url "<Article URL>" --dry-run
     ```

3. **Approval Step**:
   - Before executing the command without the `--dry-run` flag, stop and prompt the user for confirmation.
   - Print the title, url, platforms, and message to the user for review.

4. **Verify the Output**:
   - Review the console output summary block to check the status of each platform.
   - Report success/failure back to the user.
