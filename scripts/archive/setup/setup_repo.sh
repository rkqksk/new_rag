#!/bin/bash

# Create initial project structure and commit
mkdir -p src/{core,api,models,services,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs
mkdir -p scripts

# Create placeholder files
touch src/core/__init__.py
touch src/api/__init__.py
touch tests/__init__.py
touch docs/ARCHITECTURE.md

# Add initial documentation
cat > docs/ARCHITECTURE.md << EOL
# RAG Enterprise Architecture

## Overview
Open-source Retrieval-Augmented Generation (RAG) project

## Key Components
- LangChain Framework
- Qdrant Vector Database
- FastAPI Web Framework
EOL

# Stage and commit changes
git add src tests docs
git commit -m "🏗️ Add initial project structure and architecture documentation"

# Push changes
git push origin main