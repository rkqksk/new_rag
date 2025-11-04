# Document Processing Workflow

**Purpose**: Ingest documents, extract content, chunk, embed, and store in vector database with domain expert enrichment.

---

## Overview

This workflow handles the complete document ingestion pipeline from raw file upload to indexed vectors in Qdrant.

### Key Features
- Multi-format support (PDF, DOCX, XLSX, TXT, Markdown)
- OCR for scanned documents
- Domain expert metadata extraction
- Intelligent chunking strategies
- Vector embedding and storage

---

## Components Involved

### 1. SKILL: rag-pipeline
**Location**: `.claude/skills/rag-pipeline/`
**Role**: Orchestrates the entire processing pipeline
**Commands**: `process`, `batch_process`

### 2. Plugin: Domain Experts (Optional)
**Location**: `plugins/manufacturing_expert/` or `plugins/packaging_expert/`
**Role**: Extract domain-specific metadata and terminology
**Methods**: `process_document()`, `classify()`, `extract()`

### 3. MCP: filesystem
**Role**: Read document files
**Operations**: Read file contents

### 4. MCP: qdrant
**Role**: Store vectors and metadata
**Operations**: Create collection, upsert points

---

## Step-by-Step Flow

### Step 1: Document Upload
```python
# User provides document path
file_path = "manufacturing_sop.pdf"
```

### Step 2: SKILL Activation
```python
from .claude.skills.rag_pipeline import skill

result = skill.execute('process', {
    'file_path': file_path,
    'options': {
        'chunk_size': 512,
        'chunk_overlap': 50,
        'use_ocr': True,
        'extract_tables': True,
        'use_domain_expert': 'manufacturing'  # Optional
    }
})
```

### Step 3: File Reading
```
rag-pipeline SKILL → filesystem MCP → Read file contents
```

### Step 4: Content Extraction
```python
# Automatic format detection
if file_type == 'pdf':
    content = extract_pdf(file_path, use_ocr=True)
elif file_type == 'docx':
    content = extract_docx(file_path)
# ... other formats
```

### Step 5: Domain Expert Processing (If Enabled)
```python
if use_domain_expert:
    # Load domain plugin
    plugin = load_plugin(domain_expert)  # manufacturing or packaging

    # Extract metadata
    enriched = plugin.process_document({
        'filename': file_path,
        'content': content,
        'metadata': base_metadata
    })

    # Result includes:
    # - doc_type: 'sop', 'spec', 'drawing', etc.
    # - terminology: ['Cpk', 'OEE', 'ISO 9001']
    # - parameters: {'temperature': '150°C', 'pressure': '45 psi'}
    # - quality_metrics: extracted metrics
```

### Step 6: Chunking
```python
chunks = intelligent_chunker(
    content=enriched.content,
    chunk_size=512,
    overlap=50,
    preserve_structure=True  # Keep headings, sections together
)
```

### Step 7: Embedding
```python
# Generate embeddings for each chunk
embeddings = []
for chunk in chunks:
    vector = embed_text(chunk.text)  # Using sentence-transformers
    embeddings.append(vector)
```

### Step 8: Store in Qdrant
```python
# Prepare points for Qdrant
points = []
for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
    point = {
        'id': f"{doc_id}_{idx}",
        'vector': embedding,
        'payload': {
            'content': chunk.text,
            'doc_id': doc_id,
            'chunk_index': idx,
            'metadata': enriched.metadata,
            'doc_type': enriched.metadata.doc_type,
            'domain': enriched.metadata.domain,
            'terminology': enriched.metadata.terminology
        }
    }
    points.append(point)

# Upsert to Qdrant
qdrant.upsert(collection="documents", points=points)
```

### Step 9: Return Result
```python
return {
    'success': True,
    'doc_id': doc_id,
    'chunks_created': len(chunks),
    'metadata': enriched.metadata,
    'message': f"Processed {file_path} successfully"
}
```

---

## Usage Examples

### Basic Document Processing
```python
from .claude.skills.rag_pipeline import skill

result = skill.execute('process', {
    'file_path': 'document.pdf'
})

print(f"Created {result['chunks_created']} chunks")
```

### With Domain Expert (Manufacturing)
```python
result = skill.execute('process', {
    'file_path': 'manufacturing_sop.pdf',
    'options': {
        'use_domain_expert': 'manufacturing',
        'chunk_size': 512,
        'use_ocr': True
    }
})

# Enriched with manufacturing metadata
print(f"Doc Type: {result['metadata']['doc_type']}")
print(f"Terminology: {result['metadata']['terminology']}")
```

### With Domain Expert (Packaging)
```python
result = skill.execute('process', {
    'file_path': 'packaging_spec.pdf',
    'options': {
        'use_domain_expert': 'packaging',
        'extract_tables': True
    }
})

# Enriched with packaging metadata
print(f"Materials: {result['metadata']['materials']}")
print(f"Regulatory: {result['metadata']['regulatory']}")
```

### Batch Processing
```python
files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']

result = skill.execute('batch_process', {
    'file_paths': files,
    'options': {
        'use_domain_expert': 'manufacturing',
        'parallel': True
    }
})

print(f"Processed {result['successful']}/{result['total']} files")
```

---

## Error Handling

### Common Issues

#### 1. File Not Found
```
Error: File 'document.pdf' not found
Solution: Check file path, use absolute path if needed
```

#### 2. Unsupported Format
```
Error: Unsupported file format: .xyz
Solution: Convert to PDF, DOCX, TXT, or Markdown
```

#### 3. OCR Failure
```
Error: OCR failed on scanned PDF
Solution: Check image quality, try different OCR settings
```

#### 4. Qdrant Connection Error
```
Error: Cannot connect to Qdrant
Solution: Check Qdrant is running: docker-compose ps
```

#### 5. Domain Expert Not Found
```
Error: Domain expert 'xyz' not found
Solution: Use 'manufacturing' or 'packaging', or omit parameter
```

---

## Performance Considerations

### Processing Speed
- **Small docs** (<10 pages): ~2-5 seconds
- **Medium docs** (10-50 pages): ~10-30 seconds
- **Large docs** (50-200 pages): ~1-3 minutes

### Optimization Tips
1. **Adjust chunk size**: Smaller chunks = faster but more chunks
2. **Disable OCR**: If document is not scanned, skip OCR
3. **Batch processing**: Process multiple docs in parallel
4. **Cache embeddings**: Reuse embeddings for similar content

---

## Related Workflows

- `/workflow rag-query` - Query processed documents
- `/workflow domain-expert` - Deep dive into domain expert processing
- `/workflow vector-search` - Understand vector search mechanics

---

## Component Details

- `/component skills` - rag-pipeline SKILL details
- `/component plugins` - Domain expert plugin architecture
- `/component mcp` - Qdrant MCP configuration

---

**Last Updated**: 2025-11-03
