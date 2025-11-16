"""
Product Routes
Handles all product-related endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from apps.api.conversation import ConversationManager
from apps.api.conversation.compatibility import find_compatible_accessories

# Import models
from apps.api.models.schemas import ProductSearchRequest
from apps.api.services.ambiguity_detector import detect_ambiguity

# Import services
from apps.api.services.product_loader import load_products
from apps.api.services.product_search import filter_previous_results, search_products

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["products"])

# Initialize conversation manager
conversation_manager = ConversationManager(
    ollama_url="http://localhost:11434", qdrant_url="http://localhost:6333"
)


@router.get("/products")
async def list_products():
    """List all products"""
    products = load_products()
    return {
        "total": len(products),
        "products": [{**product, "product_id": pid} for pid, product in products.items()],
    }


@router.get("/products/search")
async def api_search_products(
    query: str, limit: int = 1000, session_id: Optional[str] = None, user_id: Optional[str] = None
):
    """Hybrid context-aware product search with LLM intent analysis"""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Process query through ConversationManager
    conversation_result = await conversation_manager.process_query(
        query=query, session_id=session_id, user_id=user_id
    )

    session_id = conversation_result["session_id"]
    intent = conversation_result["intent"]
    criteria = conversation_result["criteria"]
    should_search_new = conversation_result["should_search_new"]
    should_filter_previous = conversation_result["should_filter_previous"]
    should_recommend_accessory = conversation_result.get("should_recommend_accessory", False)
    should_answer_qa = conversation_result.get("should_answer_qa", False)

    # Execute search based on intent
    if should_answer_qa:
        qa_answer = conversation_result.get("qa_answer")
        qa_product = conversation_result.get("qa_product")

        response = {
            "query": query,
            "total": 0,
            "products": [],
            "session_id": session_id,
            "conversation": {
                "intent": intent,
                "state": conversation_result["state"],
                "previous_state": conversation_result["previous_state"],
                "confidence": conversation_result["confidence"],
                "explanation": conversation_result["explanation"],
            },
            "qa_response": {"answer": qa_answer, "product": qa_product, "question": query},
            "context": {
                "turn_count": conversation_result["context_info"]["turn_count"],
                "query_history": conversation_result["context_info"]["query_history"],
                "is_filtering": False,
                "is_recommending_accessory": False,
                "is_answering_qa": True,
                "previous_count": 0,
            },
        }

        return response

    elif should_recommend_accessory:
        current_bottles = conversation_result.get("current_bottles", [])

        if current_bottles:
            products = load_products()
            accessories_data = find_compatible_accessories(current_bottles, products, limit=1000)

            # Flatten groups into results list
            results = []
            for group in accessories_data["groups"]:
                neck_size = group["neck_size"]

                for pump in group["pumps"]:
                    pump["is_accessory"] = True
                    pump["accessory_type"] = "pump"
                    pump["compatible_neck_size"] = neck_size
                    pump["group_info"] = {
                        "neck_size": neck_size,
                        "bottle_count": len(group["bottles"]),
                        "bottle_codes": [b.get("product_code", "N/A") for b in group["bottles"]],
                    }
                    results.append(pump)

                for cap in group["caps"]:
                    cap["is_accessory"] = True
                    cap["accessory_type"] = "cap"
                    cap["compatible_neck_size"] = neck_size
                    cap["group_info"] = {
                        "neck_size": neck_size,
                        "bottle_count": len(group["bottles"]),
                        "bottle_codes": [b.get("product_code", "N/A") for b in group["bottles"]],
                    }
                    results.append(cap)
        else:
            results = []
            accessories_data = {
                "groups": [],
                "summary": {
                    "total_groups": 0,
                    "neck_sizes": [],
                    "total_bottles": 0,
                    "total_accessories": 0,
                },
            }

    elif should_search_new:
        products = load_products()
        all_results = search_products(query, products, limit=1000)

        # Detect ambiguity
        criteria_dict = (
            criteria
            if isinstance(criteria, dict)
            else {
                "capacity": getattr(criteria, "capacity", None),
                "material": getattr(criteria, "material", None),
                "product_type": getattr(criteria, "product_type", None),
                "neck_size": getattr(criteria, "neck_size", None),
            }
        )
        ambiguity_check = detect_ambiguity(query, all_results, criteria_dict)

        if ambiguity_check["is_ambiguous"]:
            results = all_results[:5]
        else:
            results = all_results[:limit]

    elif should_filter_previous:
        previous_results = conversation_result["previous_results"]
        if previous_results:
            results = filter_previous_results(query, previous_results, limit)
        else:
            products = load_products()
            results = search_products(query, products, limit)

    else:
        products = load_products()
        results = search_products(query, products, limit)

    # Update conversation manager with results
    await conversation_manager.update_results(session_id, results)

    # Save to Qdrant for long-term memory
    if user_id:
        await conversation_manager.save_to_qdrant(
            session_id=session_id, query=query, intent=intent, results=results, user_id=user_id
        )

    # Build response
    response = {
        "query": query,
        "total": len(results),
        "products": results,
        "session_id": session_id,
        "conversation": {
            "intent": intent,
            "state": conversation_result["state"],
            "previous_state": conversation_result["previous_state"],
            "confidence": conversation_result["confidence"],
            "explanation": conversation_result["explanation"],
        },
        "context": {
            "turn_count": conversation_result["context_info"]["turn_count"],
            "query_history": conversation_result["context_info"]["query_history"],
            "is_filtering": should_filter_previous,
            "is_recommending_accessory": should_recommend_accessory,
            "previous_count": (
                conversation_result["context_info"]["previous_results_count"]
                if should_filter_previous
                else 0
            ),
        },
    }

    # Add ambiguity info if applicable
    if should_search_new and "ambiguity_check" in locals():
        response["ambiguity"] = ambiguity_check

    # Add accessory grouping info if applicable
    if should_recommend_accessory and "accessories_data" in locals():
        response["accessory_groups"] = accessories_data["groups"]
        response["accessory_summary"] = accessories_data["summary"]

    return response


@router.get("/products/{product_id}")
async def get_product_detail(product_id: str):
    """Get detailed product information"""
    products = load_products()

    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products[product_id]

    return {"product": product}
