import os
import json
import numpy as np
import faiss

def load_embeddings_from_folder(embedding_folder):
    embeddings, metadata = [], []
    for fname in sorted(os.listdir(embedding_folder)):
        if fname.endswith('_embedding.json'):
            with open(os.path.join(embedding_folder, fname), encoding="utf-8") as f:
                emb_data = json.load(f)
                emb = np.array(emb_data["embedding"], dtype="float32")
                embeddings.append(emb)
                metadata.append({
                    "chunk_file": emb_data["chunk_file"],
                    "text_length": emb_data["text_length"],
                    "embedding_dim": emb_data["embedding_dim"]
                })
    if embeddings:
        emb_arr = np.vstack(embeddings)
        return emb_arr, metadata
    return None, None

def save_faiss_index(emb_arr, faiss_path):
    dim = emb_arr.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(emb_arr)
    faiss.write_index(index, faiss_path)

def save_metadata(meta_list, meta_path):
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

def run_loader_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    for job in config["vector_db_loader_jobs"]:
        embedding_folder = job["embedding_folder"]
        faiss_path = job["faiss_index_path"]
        meta_path = job["metadata_path"]
        print(f"\n=== 벡터DB 적재 작업 시작: {embedding_folder} ===")
        emb_arr, meta = load_embeddings_from_folder(embedding_folder)
        if emb_arr is None or meta is None:
            print(f"[오류] 벡터 임베딩 로드 실패: {embedding_folder}")
            continue
        print(f"임베딩 배열 shape: {emb_arr.shape}")
        save_faiss_index(emb_arr, faiss_path)
        save_metadata(meta, meta_path)
        print(f"[완료] FAISS index: {faiss_path}, 메타데이터: {meta_path}")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/vector_db_loader_config.json 또는 agents/vector_db_loader_config_test.json): ").strip()
    run_loader_from_config(config_fn)
