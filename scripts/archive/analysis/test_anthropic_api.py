#!/usr/bin/env python3
"""
Anthropic API Connection Test
Tests both Claude Haiku 4.5 and Sonnet 4.5 API connectivity
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_api_connection():
    """Test Anthropic API connection with both models"""

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False

    print(f"✅ API Key found (starts with: {api_key[:20]}...)")

    try:
        from anthropic import Anthropic
        print("✅ anthropic package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import anthropic package: {e}")
        print("   Install with: pip install anthropic")
        return False

    # Initialize client
    try:
        client = Anthropic(api_key=api_key)
        print("✅ Anthropic client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False

    # Test 1: Haiku 4.5
    print("\n" + "="*60)
    print("Test 1: Claude Haiku 4.5 (claude-haiku-4-5)")
    print("="*60)

    try:
        haiku_response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'Haiku 4.5 connected successfully' in Korean"
            }]
        )

        haiku_text = haiku_response.content[0].text
        print(f"✅ Haiku 4.5 Response: {haiku_text}")
        print(f"   Tokens used: {haiku_response.usage.input_tokens} input, {haiku_response.usage.output_tokens} output")

    except Exception as e:
        print(f"❌ Haiku 4.5 API call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

    # Test 2: Sonnet 4.5
    print("\n" + "="*60)
    print("Test 2: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)")
    print("="*60)

    try:
        sonnet_response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": "Say 'Sonnet 4.5 connected successfully' in Korean and explain what you are good at in one sentence"
            }]
        )

        sonnet_text = sonnet_response.content[0].text
        print(f"✅ Sonnet 4.5 Response: {sonnet_text}")
        print(f"   Tokens used: {sonnet_response.usage.input_tokens} input, {sonnet_response.usage.output_tokens} output")

    except Exception as e:
        print(f"❌ Sonnet 4.5 API call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

    # Success summary
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print(f"Haiku 4.5: Available (cost: $0.25/1M tokens input)")
    print(f"Sonnet 4.5: Available (cost: $3/1M tokens input)")
    print(f"\nYou can now use both models for the hybrid system:")
    print(f"  - Sonnet 4.5: Planning, reasoning, complex tasks")
    print(f"  - Haiku 4.5: Code execution, file operations, simple tasks")

    return True


if __name__ == "__main__":
    print("🔍 Testing Anthropic API Connection...")
    print("="*60)

    success = test_api_connection()

    if success:
        print("\n✅ API connection verified - ready for Phase 2 implementation")
        sys.exit(0)
    else:
        print("\n❌ API connection failed - check error messages above")
        sys.exit(1)
