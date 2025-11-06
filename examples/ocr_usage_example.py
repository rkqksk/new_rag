"""
OCR Pipeline Usage Example
Phase 4: Multi-Modal Document Processing
"""
from src.core.ocr import DocumentProcessor

def main():
    # Initialize processor
    processor = DocumentProcessor(
        use_gpu=True,
        min_confidence=0.75,
        enable_preprocessing=True
    )
    
    print("=== Phase 4 OCR Pipeline ===\n")
    
    # Example 1: Process PDF
    print("1. Processing PDF...")
    pdf_result = processor.process_file('data/catalog.pdf')
    print(f"   - Pages: {pdf_result.get('pages', 0)}")
    print(f"   - Text length: {len(pdf_result.get('text', ''))}")
    if 'entities' in pdf_result:
        print(f"   - Extracted entities: {list(pdf_result['entities'].keys())}")
    
    # Example 2: Process Image
    print("\n2. Processing Image...")
    image_result = processor.process_file('data/product_image.jpg')
    print(f"   - OCR Engine: {image_result.get('ocr_engine')}")
    print(f"   - Confidence: {image_result.get('ocr_confidence', 0):.2f}")
    print(f"   - Text: {image_result.get('text', '')[:100]}...")
    
    # Example 3: Process Excel
    print("\n3. Processing Excel...")
    excel_result = processor.process_file('data/products.xlsx')
    print(f"   - Rows: {excel_result.get('num_rows', 0)}")
    if 'products' in excel_result:
        print(f"   - Products extracted: {len(excel_result['products'])}")
    
    # Example 4: Convert to RAG format
    print("\n4. Converting to RAG format...")
    rag_chunks = processor.process_to_rag_format('data/catalog.pdf')
    print(f"   - Generated chunks: {len(rag_chunks)}")
    if rag_chunks:
        print(f"   - First chunk preview: {rag_chunks[0]['text'][:80]}...")
    
    # Example 5: Batch processing
    print("\n5. Batch processing...")
    files = ['data/product1.jpg', 'data/product2.jpg', 'data/catalog.pdf']
    results = processor.process_batch(files)
    print(f"   - Processed {len(results)} files")
    
    print("\n=== OCR Pipeline Complete ===")

if __name__ == '__main__':
    main()
