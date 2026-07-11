---
name: wikipedia-fact-check
description: |
  Scans an article (typically in markdown) to extract factual and historical claims, queries the Wikipedia Search and Summary APIs to retrieve the corresponding entries, compares the claims against Wikipedia summaries, and generates a structured fact-checking report highlighting any discrepancies or unverified statements.
---

# Wikipedia Fact-Check

This skill guides the agent through scanning a text or markdown document for factual claims, querying Wikipedia, and generating a detailed fact-checking accuracy report.

## Instructions

1. **Extract Claims and Retrieve Wikipedia Context**:
   - Run the python retriever script on the target article file:
     ```bash
     python3 /home/rtroiano/repositories/scripts-public/scripts-public/python/wikipedia_fact_checker.py <path_to_article>
     ```
   - This script parses the document, identifies the top 20-25 factual claims (dates, versions, history), searches Wikipedia, and outputs a JSON mapping of each claim to the closest Wikipedia summary.

2. **Verify Factual Accuracy**:
   - Read the output of the retriever script.
   - For each claim, analyze whether it is:
     - **Accurate**: The claim matches the historical details/dates/versions in the Wikipedia summary.
     - **Discrepancy**: The claim contradicts Wikipedia (e.g. wrong year, wrong person, wrong version).
     - **Unverified**: Wikipedia does not contain this information or the page summary is insufficient/inconclusive.
   - If a claim has an ambiguous or inconclusive Wikipedia summary in the script output, use the `search_web` tool with `site:en.wikipedia.org` to find the exact Wikipedia page and verify the details manually.

3. **Generate the Fact-Checking Report**:
   - Formulate a detailed markdown report.
   - Organize the report into three primary sections:
     - **Discrepancies**: Highlighting facts in the article that conflict with Wikipedia, detailing the original text, the Wikipedia fact, and the proposed correction.
     - **Unverified Claims**: Claims in the article that were not found on Wikipedia.
     - **Accurate Claims**: A table or list of validated claims with their Wikipedia page links as references.
   - Conclude with a brief summary of the overall accuracy score (e.g., "18 of 20 claims verified correct, 2 discrepancies found").
