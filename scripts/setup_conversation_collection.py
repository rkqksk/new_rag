#!/usr/bin/env python3
"""
Setup Qdrant collection for conversation history
Stores conversation turns for long-term memory and learning
"""

import httpx
import asyncio


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "conversation_history"


async def setup_conversation_collection():
    """Create conversation_history collection in Qdrant"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 80)
        print("🔧 Setting up Qdrant conversation_history collection")
        print("=" * 80)

        # Check if collection exists
        print(f"\n📍 Checking if collection '{COLLECTION_NAME}' exists...")
        try:
            response = await client.get(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}"
            )

            if response.status_code == 200:
                print(f"✅ Collection '{COLLECTION_NAME}' already exists")
                print("\n🔄 Deleting existing collection...")

                delete_response = await client.delete(
                    f"{QDRANT_URL}/collections/{COLLECTION_NAME}"
                )

                if delete_response.status_code == 200:
                    print("✅ Existing collection deleted")
                else:
                    print(f"❌ Failed to delete collection: {delete_response.status_code}")
                    return False

        except Exception as e:
            print(f"ℹ️  Collection does not exist (will create new): {e}")

        # Create new collection
        print(f"\n📍 Creating new collection '{COLLECTION_NAME}'...")

        collection_config = {
            "vectors": {
                "size": 768,  # nomic-embed-text embedding size
                "distance": "Cosine"
            },
            "optimizers_config": {
                "indexing_threshold": 10000
            },
            "hnsw_config": {
                "m": 16,
                "ef_construct": 100
            }
        }

        response = await client.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            json=collection_config
        )

        if response.status_code == 200:
            print(f"✅ Collection '{COLLECTION_NAME}' created successfully")

            # Create payload indexes for efficient filtering
            print("\n📍 Creating payload indexes...")

            indexes = [
                {"field_name": "user_id", "field_schema": "keyword"},
                {"field_name": "session_id", "field_schema": "keyword"},
                {"field_name": "intent", "field_schema": "keyword"},
                {"field_name": "timestamp", "field_schema": "datetime"},
                {"field_name": "type", "field_schema": "keyword"}
            ]

            for index in indexes:
                index_response = await client.put(
                    f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index",
                    json=index
                )

                if index_response.status_code == 200:
                    print(f"  ✅ Index created: {index['field_name']}")
                else:
                    print(f"  ⚠️  Failed to create index {index['field_name']}: {index_response.status_code}")

            print("\n" + "=" * 80)
            print("✅ Conversation history collection setup complete")
            print("=" * 80)
            print(f"\n📊 Collection info:")
            print(f"  - Name: {COLLECTION_NAME}")
            print(f"  - Vector size: 768 (nomic-embed-text)")
            print(f"  - Distance: Cosine")
            print(f"  - Indexes: user_id, session_id, intent, timestamp, type")
            print("\n💾 Ready to store conversation turns!")

            return True

        else:
            print(f"❌ Failed to create collection: {response.status_code}")
            print(response.text)
            return False


if __name__ == "__main__":
    success = asyncio.run(setup_conversation_collection())
    exit(0 if success else 1)
