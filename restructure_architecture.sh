#!/bin/bash

# Architecture Redesign Script

# Ensure base directories exist
mkdir -p .claude/skills/{manufacturing-expert,packaging-expert,rag-pipeline,bottle-expert}
mkdir -p plugins/{base,manufacturing_expert,packaging_expert}
mkdir -p src/{api,core,models,services,utils}
mkdir -p docs/governance

# Create Standardization Templates
# SKILL Template
SKILL_TEMPLATE="# SKILL Documentation

## Domain
# Describe the specific domain and responsibilities

## Interface
# Define clear method signatures and expected behaviors

## Performance Targets
# List specific performance and quality metrics

## Governance
# Change management and approval process
"

# Governance Documentation
GOVERNANCE_TEMPLATE="# Change Management Governance

## Purpose
Maintain architectural integrity and consistent system behavior

## Change Request Process
1. RFC Submission
2. Technical Review
3. Performance Analysis
4. Approval Workflow
5. Controlled Deployment

## Approval Criteria
- 100% Architectural Compatibility
- Performance Improvement Metrics
- Test Coverage > 80%
"

# Create template files
for skill in manufacturing-expert packaging-expert rag-pipeline bottle-expert; do
    echo "$SKILL_TEMPLATE" > ".claude/skills/$skill/SKILL.md"
    touch ".claude/skills/$skill/skill.py"
done

echo "$GOVERNANCE_TEMPLATE" > "docs/governance/CHANGE_MANAGEMENT.md"

# Update main CLAUDE.md to reflect new structure
cat > CLAUDE.md << EOL
# RAG Enterprise - Architectural Governance

## 🏗️ Architecture Principles
- Consistency
- Modularity
- Strict Governance
- Minimal Complexity

## 📐 Key Components
- Local LLM (Ollama)
- SKILL-based Domain Experts
- Strict Plugin Management
- Controlled Configuration

## 🔒 Change Management
See \`docs/governance/CHANGE_MANAGEMENT.md\`

## 📝 Version
- **Version**: 3.2.0 (Architectural Governance Enhancement)
EOL

echo "Architecture redesign complete!"