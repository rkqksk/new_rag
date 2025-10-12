"""
RAG Enterprise API Server
Basic implementation for document upload and search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import redis
import psycopg2
from typing import List, Dict, Any
import uuid
import os
from datetime import datetime

# Initialize FastAPI
app = FastAPI(
    title="RAG Enterprise API",
    description="Document processing and semantic search system",
    version="1.0.0"
)

# Initialize services
qdrant_client = QdrantClient(host="localhost", port=6333)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Collection name
COLLECTION_NAME = "documents"

# Initialize Qdrant collection
try:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Created collection: {COLLECTION_NAME}")
except:
    print(f"Collection {COLLECTION_NAME} already exists")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Enterprise API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = {
        "api": "healthy",
        "qdrant": False,
        "redis": False,
        "postgres": False
    }
    
    # Check Qdrant
    try:
        collections = qdrant_client.get_collections()
        health["qdrant"] = True
    except:
        pass
    
    # Check Redis
    try:
        redis_client.ping()
        health["redis"] = True
    except:
        pass
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="rag_enterprise",
            user="raguser",
            password="changeme"
        )
        conn.close()
        health["postgres"] = True
    except:
        pass
    
    return health

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Save file
        doc_id = str(uuid.uuid4())
        file_path = f"/tmp/{doc_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text (simple version)
        text_content = ""
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # For PDF, we'll need PyPDF2
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
        else:
            text_content = f"Uploaded file: {file.filename}"
        
        # Chunk text (simple version - every 500 chars)
        chunks = [text_content[i:i+500] for i in range(0, len(text_content), 500)]
        
        # Generate embeddings and store
        points = []
        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()
            
            point = PointStruct(
                id=f"{doc_id}_{i}",
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "chunk_id": i,
                    "text": chunk,
                    "filename": file.filename,
                    "upload_time": datetime.now().isoformat()
                }
            )
            points.append(point)
        
        # Store in Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        # Cache in Redis
        redis_client.setex(
            f"doc:{doc_id}",
            3600,  # 1 hour TTL
            text_content[:1000]  # Store first 1000 chars
        )
        
        # Clean up temp file
        os.remove(file_path)
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"Document processed with {len(chunks)} chunks"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/search")
async def search(query: str, top_k: int = 5):
    """Search for relevant documents"""
    try:
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "doc_id": result.payload.get("doc_id", ""),
                "filename": result.payload.get("filename", ""),
                "chunk_id": result.payload.get("chunk_id", 0)
            })
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics"""
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        
        return {
            "total_documents": collection_info.vectors_count,
            "collection": COLLECTION_NAME,
            "embedding_dimension": 384,
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)