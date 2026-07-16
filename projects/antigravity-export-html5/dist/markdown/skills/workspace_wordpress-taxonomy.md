---
name: wordpress-taxonomy
description: |
  Automatically scans a markdown blog post file and suggests relevant categories and tags by matching against your existing WordPress taxonomies and identifying key proper nouns as new tag candidates.
---

# WordPress Taxonomy Suggester

This skill helps you automatically analyze a blog post and generate suggested categories and tags for it.

## Instructions

1. **Run the Taxonomy Suggestion Script**:
   - Execute the following command on the target blog post markdown file:
     ```bash
     python3 /home/rtroiano/repositories/scripts-public/scripts-public/python/wordpress_taxonomy_suggest.py <path_to_markdown_file>
     ```
   - This script will output a JSON payload containing:
     - `suggested_categories`: Existing categories matched in the article text.
     - `suggested_tags`: Existing tags matched in the article text.
     - `candidate_new_tags`: Suggested new tags based on key proper nouns in the article.

2. **Present Taxonomy Suggestions to the User**:
   - Output the matched categories, tags, and new tag suggestions to the user in a clean table format.
   - Format:
     - **Suggested Categories** (Existing): List category names.
     - **Suggested Tags** (Existing): List tag names.
     - **New Tag Recommendations**: List proposed new tags.
   - Ask the user for confirmation on which categories and tags to assign to the WordPress post.
