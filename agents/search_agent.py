import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch

def embed_query(model_name, query):
    try:
        if "sentence-transformers" in model_name or model_name.startswith("paraphrase") or model_name.startswith("multi-"):
            model = SentenceTransformer(model_name)
            vec = model.encode([query], show_progress_bar=False)[0]
            return np.array(vec, dtype="float32")
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            inputs = tokenizer(query, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = model(**inputs)
            vec = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            return np.array(vec, dtype="float32")
    except Exception as e:
        print(f"[임베딩 오류] {model_name}: {e}")
        raise e

def search_faiss(query_vec, faiss_path, meta_path, topk=5):
    index = faiss.read_index(faiss_path)
    with open(meta_path, encoding="utf-8") as f:
        meta_list = json.load(f)
    D, I = index.search(query_vec.reshape(1, -1), topk)
    results = []
    for idx, dist in zip(I[0], D[0]):
        if idx < 0 or idx >= len(meta_list): continue
        meta = meta_list[idx]
        meta['score'] = float(dist)
        results.append(meta)
    return results

def run_search_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    model_name = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    print(f"\n<SearchAgent> 임베딩 모델: {model_name}\n")
    for job in config["search_jobs"]:
        faiss_path = job["faiss_index_path"]
        meta_path = job["metadata_path"]
        topk = job.get("topk", 5)
        print(f"\n=== DB: {faiss_path} ===")
        while True:
            query = input("검색할 질문(엔터 입력 시 종료): ").strip()
            if not query: break
            try:
                query_vec = embed_query(model_name, query)
                results = search_faiss(query_vec, faiss_path, meta_path, topk)
                print("\n--- Top-K 검색 결과 ---")
                for i, chunk in enumerate(results):
                    print(f"\n[{i+1}] 파일: {chunk['chunk_file']} | 스코어: {chunk['score']:.2f}")
                    print(f"텍스트 길이: {chunk.get('text_length')}")
                print("-----------------------\n")
            except Exception as e:
                print(f"[검색 오류]: {e}")
        print(f"=== 이 DB 검색 종료 ===")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/search_config.json 또는 agents/search_config_test.json): ").strip()
    run_search_from_config(config_fn)
