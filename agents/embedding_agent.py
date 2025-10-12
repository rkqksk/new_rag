import os
import json
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch

def safe_write(path, content, mode="w", encoding="utf-8"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding=encoding) as f:
        f.write(content)

def embed_with_sentence_transformer(model_name, text):
    model = SentenceTransformer(model_name)
    vec = model.encode([text], show_progress_bar=False)[0]
    return vec.tolist()

def embed_with_huggingface(model_name, text):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    vec = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return vec.tolist()

def embed_with_model(model_name, text):
    try:
        if "sentence-transformers" in model_name or model_name.startswith("paraphrase") or model_name.startswith("multi-"):
            return embed_with_sentence_transformer(model_name, text)
        else:
            return embed_with_huggingface(model_name, text)
    except Exception as e:
        print(f"임베딩 오류 [{model_name}]: {e}")
        raise e

def try_embedding_with_fallback(primary_model, fallback_model, text, chunk_name=""):
    try:
        print(f"[PRIMARY] {chunk_name} → {primary_model}")
        return embed_with_model(primary_model, text)
    except Exception as e:
        print(f"[PRIMARY 실패] {chunk_name} → FALLBACK 시도: {fallback_model}")
        try:
            return embed_with_model(fallback_model, text)
        except Exception as e2:
            print(f"[FALLBACK도 실패] {chunk_name} — {e2}")
            return None

def run_embedding_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    
    primary_model = config.get("primary_embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    fallback_model = config.get("fallback_embedding_model", "jhgan/ko-sbert-nli")
    
    print(f"임베딩 모델 설정:")
    print(f"  Primary: {primary_model}")
    print(f"  Fallback: {fallback_model}")
    
    for job in config["embedding_jobs"]:
        chunk_folder = job["input_folder"]
        output_folder = job["output_folder"]
        
        print(f"\n=== 임베딩 작업 시작: {chunk_folder} → {output_folder} ===")
        os.makedirs(output_folder, exist_ok=True)
        
        if not os.path.exists(chunk_folder):
            print(f"[경고] 입력 폴더가 존재하지 않습니다: {chunk_folder}")
            continue
            
        chunk_files = [f for f in os.listdir(chunk_folder) if f.endswith('.txt')]
        if not chunk_files:
            print(f"[경고] 처리할 .txt 파일이 없습니다: {chunk_folder}")
            continue
            
        for fname in sorted(chunk_files):
            fpath = os.path.join(chunk_folder, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    text = f.read().strip()
                
                if not text:
                    print(f"[건너뛰기] 빈 파일: {fname}")
                    continue
                    
                vec = try_embedding_with_fallback(primary_model, fallback_model, text, fname)
                
                if vec is not None:
                    output_file = fname.replace(".txt", "_embedding.json")
                    embedding_data = {
                        "chunk_file": fname,
                        "text_length": len(text),
                        "embedding_dim": len(vec),
                        "embedding": vec
                    }
                    safe_write(
                        os.path.join(output_folder, output_file),
                        json.dumps(embedding_data, ensure_ascii=False, indent=2)
                    )
                    print(f"[성공] {fname} → {output_file} (dim: {len(vec)})")
                else:
                    print(f"[실패] {fname} - 임베딩 생성 실패")
                    
            except Exception as e:
                print(f"[오류] {fname} 처리 중 오류: {e}")
        
        print(f"=== 임베딩 작업 완료: {output_folder} ===")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/embedding_config.json 또는 agents/embedding_config_test.json): ").strip()
    run_embedding_from_config(config_fn)
