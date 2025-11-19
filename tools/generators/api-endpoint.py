#!/usr/bin/env python3
"""Generate FastAPI endpoint with tests"""

import sys
import os

if len(sys.argv) < 2:
    print("Usage: python tools/generators/api-endpoint.py endpoint_name")
    sys.exit(1)

endpoint_name = sys.argv[1]
endpoint_path = endpoint_name.replace('_', '-')

# Router file
router_content = f'''"""
{endpoint_name.title()} API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/{endpoint_path}", tags=["{endpoint_name}"])

class {endpoint_name.title()}Request(BaseModel):
    """Request model for {endpoint_name}"""
    pass

class {endpoint_name.title()}Response(BaseModel):
    """Response model for {endpoint_name}"""
    message: str

@router.get("/")
async def get_{endpoint_name}():
    """Get {endpoint_name}"""
    return {{"message": "{endpoint_name} endpoint"}}

@router.post("/")
async def create_{endpoint_name}(request: {endpoint_name.title()}Request):
    """Create {endpoint_name}"""
    return {endpoint_name.title()}Response(message="Created")
'''

# Test file
test_content = f'''"""
Tests for {endpoint_name} endpoints
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_get_{endpoint_name}():
    response = client.get("/{endpoint_path}/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_{endpoint_name}():
    response = client.post("/{endpoint_path}/", json={{}})
    assert response.status_code == 200
'''

# Create files
os.makedirs(f"apps/api/routes", exist_ok=True)
with open(f"apps/api/routes/{endpoint_name}.py", 'w') as f:
    f.write(router_content)

os.makedirs(f"tests/api", exist_ok=True)
with open(f"tests/api/test_{endpoint_name}.py", 'w') as f:
    f.write(test_content)

print(f"✅ Generated API endpoint: {endpoint_name}")
print(f"   Router: apps/api/routes/{endpoint_name}.py")
print(f"   Tests: tests/api/test_{endpoint_name}.py")
