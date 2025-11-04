#!/bin/bash

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements
pip install -r requirements_crawler.txt

# Run crawler
python3 scripts/onehago_jina_crawler.py