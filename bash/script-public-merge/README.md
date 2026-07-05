<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `script-public-merge`</summary>

```mermaid
graph TD
	root["script-public-merge"]:::root --> n1["README.md"]:::file-md
	root["script-public-merge"]:::root --> n2["script-public-merge.sh"]:::file-sh
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-sh fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# script-public-merge.sh

## Intended function
Bootstrap/restructure helper for this repository that creates directories, appends ignore rules, writes `.gitattributes`, then commits and pushes.

## How to use
Run from repository root (where `.git` exists):

```bash
bash script-public-merge.sh
```

## Example
```bash
cd /path/to/scripts-public
bash bash/script-public-merge/script-public-merge.sh
```

## Warnings
- The script performs `git add .`, `git commit`, and `git push origin main`.
- It can unintentionally stage and push unrelated or sensitive files.
- It appends to `.gitignore` and overwrites `.gitattributes` in current form.
- Review and possibly edit script behavior before use in active branches.
