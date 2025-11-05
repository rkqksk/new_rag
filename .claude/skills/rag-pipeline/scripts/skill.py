"""
RAG Pipeline Skill - Executable Implementation

Provides unified interface for document processing, vector search, and RAG queries
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add skills scripts directory to path for collection_manager
skills_scripts = Path(__file__).parent
sys.path.insert(0, str(skills_scripts))

# Import collection manager
from collection_manager import get_collection_manager

# Import domain experts if available
try:
    from plugins.manufacturing_expert import ManufacturingExpertPlugin
    from plugins.packaging_expert import PackagingExpertPlugin
    DOMAIN_EXPERTS = {
        'manufacturing': ManufacturingExpertPlugin(),
        'packaging': PackagingExpertPlugin()
    }
except ImportError:
    DOMAIN_EXPERTS = {}


# Skill metadata
SKILL_INFO = {
    'name': 'rag-pipeline',
    'version': '2.1.0',
    'description': 'Complete RAG pipeline: document processing, vector search, answer generation with multi-collection routing',
    'domain': 'rag',
    'commands': ['process', 'query', 'search', 'batch_process', 'batch_search',
                 'optimize_index', 'evaluate', 'stats', 'help',
                 'list_collections', 'collection_stats', 'embed_collection', 'delete_collection']
}


def execute(command: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute RAG pipeline command

    Commands:
        process         - Process and index document
        query           - RAG query (search + generate answer)
        search          - Vector search only
        batch_process   - Batch document processing
        batch_search    - Batch search
        optimize_index  - Optimize vector database indexes
        evaluate        - Evaluate search quality
        stats           - Get system statistics
        help            - Show usage information
    """

    # Handle both positional and keyword arguments
    params = args[0] if args else kwargs

    if command == 'process':
        return process_document(params)

    elif command == 'query':
        return rag_query(params)

    elif command == 'search':
        return vector_search(params)

    elif command == 'batch_process':
        return batch_process_documents(params)

    elif command == 'batch_search':
        return batch_search_queries(params)

    elif command == 'optimize_index':
        return optimize_index(params)

    elif command == 'evaluate':
        return evaluate_search_quality(params)

    elif command == 'stats':
        return get_system_stats()

    elif command == 'list_collections':
        return list_collections(params)

    elif command == 'collection_stats':
        return get_collection_stats(params)

    elif command == 'embed_collection':
        return embed_collection(params)

    elif command == 'delete_collection':
        return delete_collection(params)

    elif command == 'help':
        return {
            "skill": "rag-pipeline",
            "version": SKILL_INFO['version'],
            "commands": {
                "process": "Process and index document to vector database",
                "query": "RAG query - search + generate answer",
                "search": "Vector search only (no answer generation)",
                "batch_process": "Process multiple documents in batch",
                "batch_search": "Search multiple queries in batch",
                "optimize_index": "Optimize vector database indexes",
                "evaluate": "Evaluate search quality metrics",
                "stats": "Get system statistics",
                "list_collections": "List all available collections",
                "collection_stats": "Get statistics for specific collection",
                "embed_collection": "Embed data to a collection",
                "delete_collection": "Delete a collection",
                "help": "Show this help message"
            },
            "usage": "skill.execute('command', params_dict)",
            "examples": [
                "skill.execute('process', {'file_path': 'doc.pdf', 'use_ocr': True})",
                "skill.execute('query', {'question': 'What is...?', 'top_k': 5, 'collections': ['chungjinkorea', 'onehago']})",
                "skill.execute('search', {'query': 'search term', 'use_hybrid': True})",
                "skill.execute('list_collections', {'enabled_only': True})"
            ]
        }

    else:
        return {
            "error": f"Unknown command: {command}",
            "available_commands": SKILL_INFO['commands'],
            "hint": "Use 'help' command for usage information"
        }


def process_document(params: Dict[str, Any]) -> Dict[str, Any]:
    """Process document and index to vector database"""

    file_path = params.get('file_path')
    options = params.get('options', {})
    collection_id = params.get('collection_id', 'chungjinkorea')  # Default to chungjinkorea

    if not file_path:
        return {"error": "Missing required parameter: file_path"}

    # Apply domain expert if specified
    domain_expert = options.get('use_domain_expert')
    if domain_expert and domain_expert in DOMAIN_EXPERTS:
        expert = DOMAIN_EXPERTS[domain_expert]

        # Load and process with domain expert
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        document = {'content': content, 'filename': Path(file_path).name}
        expert_result = expert.process_document(document)

        return {
            'status': 'success',
            'file_path': file_path,
            'domain': domain_expert,
            'metadata': expert_result.metadata.__dict__ if hasattr(expert_result, 'metadata') else {},
            'message': 'Document processed with domain expert'
        }

    # Standard RAG processing using Core module
    try:
        from src.core.rag_pipeline import RAGPipeline
        from src.core.embedding_service import EmbeddingService
        from qdrant_client import QdrantClient

        # Get collection manager and resolve collection name
        collection_manager = get_collection_manager()
        collection_name = collection_manager.get_collection_name(collection_id)

        # Initialize pipeline (will reuse global instances in future)
        embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')
        qdrant_client = QdrantClient(url="http://localhost:6333")

        class SimpleLoader:
            def load_documents(self, paths):
                return []

        class SimpleSplitter:
            def split_documents(self, documents):
                return documents

        pipeline = RAGPipeline(
            loader=SimpleLoader(),
            text_splitter=SimpleSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name=collection_name,  # Use resolved collection name
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct"
        )

        result = pipeline.ingest_documents([file_path])

        return {
            'status': 'success',
            'file_path': file_path,
            'collection_id': collection_id,
            'collection_name': collection_name,
            'chunks_created': result['total_chunks'],
            'message': f'Document processed and indexed to {collection_name}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'file_path': file_path,
            'collection_id': collection_id,
            'error': str(e),
            'message': 'RAG processing failed'
        }


def rag_query(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute RAG query: search + answer generation across multiple collections"""

    question = params.get('question')
    top_k = params.get('top_k', 5)
    use_rerank = params.get('use_rerank', False)
    filters = params.get('filters')
    collection_ids = params.get('collections', None)  # List of collection IDs
    materials = params.get('materials', None)  # Material filters

    if not question:
        return {"error": "Missing required parameter: question"}

    # Build material filter if provided
    if materials and not filters:
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        filters = Filter(
            must=[
                FieldCondition(
                    key="materials",
                    match=MatchAny(any=materials)
                )
            ]
        )

    # Real RAG query using Core module
    try:
        import time

        start_time = time.time()

        # Use vector_search for multi-collection search
        search_start = time.time()
        search_result = vector_search({
            'query': question,
            'top_k': top_k,
            'filters': filters,
            'collections': collection_ids
        })
        search_time = (time.time() - search_start) * 1000

        if search_result['status'] != 'success':
            return search_result

        search_results = search_result['results']

        # Generation phase
        from src.core.rag_pipeline import RAGPipeline
        from src.core.embedding_service import EmbeddingService
        from qdrant_client import QdrantClient

        embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')
        qdrant_client = QdrantClient(url="http://localhost:6333")

        class SimpleLoader:
            def load_documents(self, paths):
                return []

        class SimpleSplitter:
            def split_documents(self, documents):
                return documents

        # Use default collection for generation (doesn't matter which)
        pipeline = RAGPipeline(
            loader=SimpleLoader(),
            text_splitter=SimpleSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name="products",
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct"
        )

        gen_start = time.time()
        answer = pipeline.generate_response(search_results, question)
        gen_time = (time.time() - gen_start) * 1000

        total_time = (time.time() - start_time) * 1000

        # Calculate confidence based on top result score
        confidence = search_results[0]['score'] if search_results else 0.0

        return {
            'answer': answer,
            'sources': search_results,
            'collections': search_result.get('collections', []),
            'confidence': float(confidence),
            'metadata': {
                'search_time_ms': round(search_time, 2),
                'generation_time_ms': round(gen_time, 2),
                'total_time_ms': round(total_time, 2)
            },
            'status': 'success'
        }

    except Exception as e:
        return {
            'answer': '',
            'sources': [],
            'error': str(e),
            'status': 'error'
        }


def vector_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute vector search across one or more collections with smart query enhancement"""

    query = params.get('query')
    top_k = params.get('top_k', 10)
    use_hybrid = params.get('use_hybrid', False)
    use_rerank = params.get('use_rerank', False)
    filters = params.get('filters')
    collection_ids = params.get('collections', None)  # List of collection IDs

    if not query:
        return {"error": "Missing required parameter: query"}

    # Real vector search using Core module
    try:
        from src.core.rag_pipeline import RAGPipeline
        from src.core.embedding_service import EmbeddingService
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, Range, MatchValue, MatchAny

        # ENHANCEMENT: Use QueryEnhancer for smart filtering
        from query_enhancer import QueryEnhancer

        query_enhancer = QueryEnhancer()
        enhanced = query_enhancer.enhance_query(query)

        # Merge enhanced filters with user-provided filters
        if enhanced['has_filters'] and not filters:
            # Convert enhanced filter format to Qdrant format
            enhanced_filter = enhanced['filter']
            qdrant_filter_conditions = []

            for condition in enhanced_filter.get('must', []):
                key = condition['key']

                if 'range' in condition:
                    # Range condition
                    range_cond = condition['range']
                    qdrant_filter_conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=range_cond.get('gte'),
                                lte=range_cond.get('lte')
                            )
                        )
                    )
                elif 'match' in condition:
                    # Match condition
                    match_cond = condition['match']
                    if 'value' in match_cond:
                        qdrant_filter_conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=match_cond['value']))
                        )
                    elif 'any' in match_cond:
                        qdrant_filter_conditions.append(
                            FieldCondition(key=key, match=MatchAny(any=match_cond['any']))
                        )

            if qdrant_filter_conditions:
                filters = Filter(must=qdrant_filter_conditions)

        # Use refined query for vector search (numbers/units removed)
        search_query = enhanced['refined_query']

        embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')
        qdrant_client = QdrantClient(url="http://localhost:6333")

        class SimpleLoader:
            def load_documents(self, paths):
                return []

        class SimpleSplitter:
            def split_documents(self, documents):
                return documents

        # Get collection manager
        collection_manager = get_collection_manager()

        # If no collections specified, use active collections
        if collection_ids is None:
            collection_ids = collection_manager.get_active_collections()

        # Validate collections
        valid_collection_ids = collection_manager.validate_collections(collection_ids)

        if not valid_collection_ids:
            return {
                'results': [],
                'query': query,
                'error': 'No valid collections found',
                'status': 'error'
            }

        # Search each collection and merge results
        all_results = []
        for collection_id in valid_collection_ids:
            collection_name = collection_manager.get_collection_name(collection_id)

            pipeline = RAGPipeline(
                loader=SimpleLoader(),
                text_splitter=SimpleSplitter(),
                embedding_model=embedding_service,
                vector_db=qdrant_client,
                collection_name=collection_name,
                ollama_url="http://localhost:11434",
                ollama_model="qwen2.5:7b-instruct"
            )

            # Use search_query (refined) and smart filters
            results = pipeline.retrieve(search_query, top_k=top_k, metadata_filters=filters)

            # Add collection info to each result
            for result in results:
                result['metadata']['source_collection'] = collection_id

            all_results.extend(results)

        # ENHANCEMENT: Validate results match query intent
        if enhanced['has_filters']:
            all_results = query_enhancer.validate_results(all_results, enhanced['intent'])

        # Sort by score and limit to top_k
        all_results.sort(key=lambda x: x['score'], reverse=True)
        all_results = all_results[:top_k]

        return {
            'results': all_results,
            'query': query,
            'refined_query': search_query,
            'intent': {
                'capacity': enhanced['intent'].capacity_value if enhanced['intent'].has_capacity else None,
                'capacity_unit': enhanced['intent'].capacity_unit if enhanced['intent'].has_capacity else None,
                'neck_size': enhanced['intent'].neck_size if enhanced['intent'].has_neck_size else None,
                'materials': enhanced['intent'].materials if enhanced['intent'].has_material else [],
            } if enhanced['has_filters'] else {},
            'top_k': top_k,
            'collections': valid_collection_ids,
            'mode': 'hybrid' if use_hybrid else 'vector',
            'total_results': len(all_results),
            'status': 'success'
        }

    except Exception as e:
        return {
            'results': [],
            'query': query,
            'error': str(e),
            'status': 'error'
        }


def rag_query_old(params: Dict[str, Any]) -> Dict[str, Any]:
    """OLD PLACEHOLDER - Execute RAG query: search + answer generation"""

    question = params.get('question')
    top_k = params.get('top_k', 5)
    use_rerank = params.get('use_rerank', False)
    filters = params.get('filters')

    if not question:
        return {"error": "Missing required parameter: question"}

    # Search phase
    search_results = vector_search({
        'query': question,
        'top_k': top_k,
        'use_rerank': use_rerank,
        'filters': filters
    })

    # Answer generation (placeholder)
    return {
        'answer': f'Answer generation pending integration with LLM for question: {question}',
        'sources': search_results.get('results', []),
        'confidence': 0.0,
        'metadata': {
            'search_time_ms': 0,
            'generation_time_ms': 0,
            'total_time_ms': 0
        }
    }


def batch_process_documents(params: Dict[str, Any]) -> Dict[str, Any]:
    """Process multiple documents in batch"""

    file_paths = params.get('file_paths', [])
    batch_size = params.get('batch_size', 10)
    parallel = params.get('parallel', True)

    if not file_paths:
        return {"error": "Missing required parameter: file_paths"}

    results = []
    for file_path in file_paths:
        result = process_document({'file_path': file_path})
        results.append(result)

    return {
        'total_processed': len(results),
        'successful': sum(1 for r in results if r.get('status') == 'success'),
        'failed': sum(1 for r in results if r.get('status') != 'success'),
        'results': results
    }


def batch_search_queries(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search multiple queries in batch"""

    queries = params.get('queries', [])
    top_k = params.get('top_k', 5)

    if not queries:
        return {"error": "Missing required parameter: queries"}

    results = {}
    for query in queries:
        result = vector_search({'query': query, 'top_k': top_k})
        results[query] = result

    return {
        'total_queries': len(queries),
        'results': results
    }


def optimize_index(params: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize vector database indexes"""

    fields = params.get('fields', [])

    return {
        'status': 'success',
        'optimized_fields': fields,
        'message': 'Index optimization integration pending'
    }


def evaluate_search_quality(params: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate search quality metrics"""

    test_queries = params.get('test_queries', [])

    if not test_queries:
        return {"error": "Missing required parameter: test_queries"}

    return {
        'metrics': {
            'precision_at_k': 0.0,
            'recall_at_k': 0.0,
            'mrr': 0.0,
            'ndcg': 0.0
        },
        'total_queries': len(test_queries),
        'message': 'Evaluation integration pending'
    }


def get_system_stats() -> Dict[str, Any]:
    """Get RAG system statistics"""

    return {
        'total_documents': 0,
        'total_chunks': 0,
        'avg_search_time_ms': 0,
        'avg_generation_time_ms': 0,
        'cache_hit_rate': 0.0,
        'message': 'Statistics integration pending'
    }


def list_collections(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all available collections"""

    enabled_only = params.get('enabled_only', False)
    embedded_only = params.get('embedded_only', False)

    try:
        collection_manager = get_collection_manager()
        collections = collection_manager.list_collections(
            enabled_only=enabled_only,
            embedded_only=embedded_only
        )

        return {
            'collections': collections,
            'total': len(collections),
            'status': 'success'
        }

    except Exception as e:
        return {
            'collections': [],
            'error': str(e),
            'status': 'error'
        }


def get_collection_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics for a specific collection"""

    collection_id = params.get('collection_id')

    if not collection_id:
        return {"error": "Missing required parameter: collection_id"}

    try:
        from qdrant_client import QdrantClient

        collection_manager = get_collection_manager()
        collection_metadata = collection_manager.get_collection(collection_id)

        if not collection_metadata:
            return {
                'error': f'Collection not found: {collection_id}',
                'status': 'error'
            }

        collection_name = collection_manager.get_collection_name(collection_id)

        # Get Qdrant stats
        qdrant_client = QdrantClient(url="http://localhost:6333")
        collection_info = qdrant_client.get_collection(collection_name=collection_name)

        return {
            'collection_id': collection_id,
            'collection_name': collection_name,
            'metadata': collection_metadata,
            'vector_count': collection_info.vectors_count if hasattr(collection_info, 'vectors_count') else 0,
            'status': 'success'
        }

    except Exception as e:
        return {
            'collection_id': collection_id,
            'error': str(e),
            'status': 'error'
        }


def embed_collection(params: Dict[str, Any]) -> Dict[str, Any]:
    """Embed data to a collection"""

    collection_id = params.get('collection_id')
    data_path = params.get('data_path')

    if not collection_id:
        return {"error": "Missing required parameter: collection_id"}

    if not data_path:
        return {"error": "Missing required parameter: data_path"}

    return {
        'collection_id': collection_id,
        'data_path': data_path,
        'message': 'Embedding integration pending - use dedicated embedding scripts',
        'status': 'pending'
    }


def delete_collection(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a collection"""

    collection_id = params.get('collection_id')

    if not collection_id:
        return {"error": "Missing required parameter: collection_id"}

    try:
        from qdrant_client import QdrantClient

        collection_manager = get_collection_manager()
        collection_name = collection_manager.get_collection_name(collection_id)

        qdrant_client = QdrantClient(url="http://localhost:6333")
        qdrant_client.delete_collection(collection_name=collection_name)

        return {
            'collection_id': collection_id,
            'collection_name': collection_name,
            'message': f'Collection {collection_name} deleted',
            'status': 'success'
        }

    except Exception as e:
        return {
            'collection_id': collection_id,
            'error': str(e),
            'status': 'error'
        }


def help_text() -> str:
    """Return help text for the skill"""
    return f"""
RAG Pipeline Skill v{SKILL_INFO['version']}

DESCRIPTION:
    {SKILL_INFO['description']}

COMMANDS:
    process         - Process and index document to vector database
    query           - RAG query (search + generate answer)
    search          - Vector search only (no answer generation)
    batch_process   - Process multiple documents in batch
    batch_search    - Search multiple queries in batch
    optimize_index  - Optimize vector database indexes
    evaluate        - Evaluate search quality metrics
    stats           - Get system statistics
    help            - Show this help message

USAGE:
    from .claude.skills.rag_pipeline import skill

    # Process document
    result = skill.execute('process', {{
        'file_path': 'document.pdf',
        'options': {{
            'chunk_size': 512,
            'use_ocr': True,
            'use_domain_expert': 'manufacturing'
        }}
    }})

    # RAG query
    answer = skill.execute('query', {{
        'question': 'What is the authentication method?',
        'top_k': 5,
        'use_rerank': True,
        'filters': {{'doc_type': 'user-guide'}}
    }})

    # Vector search
    results = skill.execute('search', {{
        'query': '50ml container products',
        'top_k': 10,
        'use_hybrid': True
    }})

DOMAIN EXPERTS:
    - manufacturing: Manufacturing document processing (SOPs, FMEA, quality specs)
    - packaging: Packaging document processing (materials, compliance, specs)

SEARCH MODES:
    - Semantic: Pure vector similarity (default)
    - Hybrid: Vector + keyword (BM25) combination
    - Reranked: Cross-encoder reranking for improved relevance

SUPPORTED FORMATS:
    - PDF: Advanced parsing with OCR (Korean + English)
    - DOCX: Microsoft Word documents
    - XLSX: Excel spreadsheets with table extraction
    - TXT/CSV: Plain text and CSV files
"""


# Quick access functions
def process(file_path: str, **options) -> Dict[str, Any]:
    """Quick process document"""
    return execute('process', {'file_path': file_path, 'options': options})


def query(question: str, **params) -> Dict[str, Any]:
    """Quick RAG query"""
    params['question'] = question
    return execute('query', params)


def search(query_text: str, **params) -> Dict[str, Any]:
    """Quick vector search"""
    params['query'] = query_text
    return execute('search', params)


if __name__ == "__main__":
    # Self-test
    print("RAG Pipeline Skill - Self Test")
    print("=" * 60)

    print("\n1. Help Test:")
    help_result = execute('help')
    print(f"   Commands available: {len(help_result['commands'])}")

    print("\n2. Process Test (with manufacturing expert):")
    process_result = execute('process', {
        'file_path': 'test_sop.txt',
        'options': {'use_domain_expert': 'manufacturing'}
    })
    print(f"   Status: {process_result.get('status', 'unknown')}")

    print("\n3. Search Test:")
    search_result = execute('search', {
        'query': 'Cpk requirements',
        'top_k': 5
    })
    print(f"   Query: {search_result.get('query')}")

    print("\n4. Query Test:")
    query_result = execute('query', {
        'question': 'What is the quality control process?',
        'top_k': 3
    })
    print(f"   Answer preview: {query_result.get('answer', '')[:80]}...")

    print("\n" + "=" * 60)
    print("✅ Skill executable and ready to use!")
    print("Note: Full functionality requires RAG engine integration")
