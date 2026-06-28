#!/bin/bash

# Ensure we are in the root of the existing repo
if [ ! -d ".git" ]; then
    echo "Error: This does not appear to be a git repository."
    exit 1
fi

echo "Adding structural directories to scripts-public..."

# 1. Create the Directory Structure
mkdir -p scripts/{bash,powershell,python}
mkdir -p projects/{app-dashboard,infrastructure}
mkdir -p docs/{standard-ops,planning,architecture}
mkdir -p artifacts/templates

# 2. Update .gitignore
# We append these rules if they don't already exist
cat << 'EOF' >> .gitignore

# Automation environment/structure ignores
__pycache__/
*.py[cod]
.env
.venv/
env/

# Ignore zip files except in the templates directory
*.zip
!artifacts/templates/*.zip
EOF

# 3. Create .gitattributes (Preparing for Git LFS)
cat << 'EOF' > .gitattributes
*.pdf filter=lfs diff=lfs merge=lfs -text
*.docx filter=lfs diff=lfs merge=lfs -text
*.xlsx filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
EOF

# 4. Commit and Push
echo "Staging and committing new structure..."
git add .
git commit -m "chore: add standardized project structure"

echo "Pushing to GitHub (origin)..."
git push origin main

echo "Done! Your structure is now live in the scripts-public repo."
