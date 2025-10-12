import os
import json

import openai
from dotenv import load_dotenv

def load_chunk_texts(search_results, chunk_folder, max_chunks=3):
    texts = []
    for meta in search_results[:max_chunks]:
        path = os.path.join(chunk_folder, meta['chunk_file'])
        try:
            with open(path, encoding="utf-8") as f:
                texts.append(f.read().strip())
        except Exception as e:
            print(f"[오류] chunk 파일 로딩 실패: {path} — {e}")
    return texts

def build_prompt(query, chunk_texts, instruction="문서 내용에 근거해 답변하세요."):
    context = "\n---\n".join(chunk_texts)
    return f"{instruction}\n질문: {query}\n[참고 문서]\n{context}\n---\n답변:"

def qa_with_openai(prompt, model="gpt-3.5-turbo", temp=0.2):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()

def run_qa_from_config(config_path):
    # .env 파일에서 환경변수 로딩
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("[오류] OPENAI_API_KEY가 환경변수에 없습니다.")
        return

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    chunk_folder = config["chunk_folder"]
    model = config.get("openai_model", "gpt-3.5-turbo")
    max_chunks = config.get("max_chunks", 3)
    instruction = config.get("instruction", "문서 내용에 근거해 답변하세요.")

    print(f"QAAgent: {model}, chunk_folder: {chunk_folder} (환경변수 기반 키)")
    while True:
        srpath = input("검색 결과(meta json) 경로 (엔터 시 종료): ").strip()
        if not srpath: break
        try:
            with open(srpath, encoding="utf-8") as f: search_results = json.load(f)
            query = input("질문: ").strip()
            chunk_texts = load_chunk_texts(search_results, chunk_folder, max_chunks)
            prompt = build_prompt(query, chunk_texts, instruction)
            answer = qa_with_openai(prompt, model=model)
            print("\n--- 답변 ---\n" + answer + "\n----------------")
        except Exception as e:
            print(f"[QA 오류]: {e}")

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/qa_config.json 또는 agents/qa_config_test.json): ").strip()
    run_qa_from_config(config_fn)
