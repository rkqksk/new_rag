#!/bin/bash

# Project Restructuring Script for RAG Enterprise

# Create base directory structure
mkdir -p .claude/skills/{rag-pipeline,manufacturing-expert,packaging-expert,bottle-expert}
mkdir -p plugins/{base,manufacturing_expert,packaging_expert}
mkdir -p src/{api,core,models,services,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p config/{dev,staging,production}
mkdir -p docs/{architecture,api_reference,guides}
mkdir -p scripts/maintenance

# Move and Organize Skills
# RAG Pipeline
mv scripts/run_chat_server.py .claude/skills/rag-pipeline/skill.py
touch .claude/skills/rag-pipeline/SKILL.md

# Manufacturing Expert
mv scripts/analyze_product_detail.py plugins/manufacturing_expert/plugin.py
touch .claude/skills/manufacturing-expert/skill.py
touch .claude/skills/manufacturing-expert/SKILL.md

# Packaging Expert
mv scripts/packaging_image_orchestrator.py plugins/packaging_expert/plugin.py
touch .claude/skills/packaging-expert/skill.py
touch .claude/skills/packaging-expert/SKILL.md

# Organize Source Code
# Move API related scripts
mv scripts/test_*_api.py tests/unit/
mv app/api/* src/api/
mv app/services/* src/services/

# Move Core Logic
mv app/core/* src/core/
mv scripts/test_phase*_integration.py tests/integration/

# Organize Models
mv app/models/* src/models/

# Utility Scripts
mv scripts/maintenance/* scripts/maintenance/

# Clean up unnecessary files
find . -type f -name "*.py.old" -delete
find . -type f -name "*.py.backup" -delete
find . -type f -name "api_simple.py*" -delete

# Update README with new structure
cat > README.md << EOL
# RAG Enterprise

## Project Structure

- \`.claude/skills/\`: SKILL-based domain experts
- \`plugins/\`: Domain logic implementations
- \`src/\`: Core application source code
  - \`api/\`: FastAPI endpoints
  - \`core/\`: Business logic
  - \`models/\`: Data schemas
  - \`services/\`: External service integrations
  - \`utils/\`: Utility functions
- \`tests/\`: Comprehensive test suite
- \`config/\`: Environment configurations
- \`docs/\`: Project documentation
- \`scripts/\`: Utility and maintenance scripts

## Quick Start

\`\`\`bash
# Setup
pip install -r requirements.txt

# Test
pytest tests/ -v --cov=src

# Run
python .claude/skills/rag-pipeline/skill.py
\`\`\`
EOL

echo "Project restructuring complete!"