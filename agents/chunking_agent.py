import os
import json
import re

def safe_write(path, content, mode="w", encoding="utf-8"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding=encoding) as f:
        f.write(content)

def chunk_text(text, chunk_size=500, overlap=50):
    # 의미기반 chunk: 문장 단위 분할 후 토큰 수 기준 청킹, overlap(겹침) 지원
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        current += s + " "
        if len(current) > chunk_size:
            chunks.append(current.strip())
            current = " ".join(current.split()[-overlap:]) if overlap else ""
    if current.strip():
        chunks.append(current.strip())
    return chunks

def chunk_table(table_json, chunk_by="row"):
    # 행 단위 chunk(실무: 표는 row 기반이 일반적)
    if chunk_by == "row":
        return [json.dumps(row, ensure_ascii=False) for row in table_json]
    else:
        cols = list(table_json[0].keys())
        return [json.dumps({col: [row[col] for row in table_json]}, ensure_ascii=False) for col in cols]

def chunk_paragraphs(doc_text, chunk_size=400):
    # 문단 기준 청크 분할
    paragraphs = [p.strip() for p in doc_text.split("\n") if p.strip()]
    chunks, temp = [], ""
    for para in paragraphs:
        temp += para + " "
        if len(temp) > chunk_size:
            chunks.append(temp.strip())
            temp = ""
    if temp.strip():
        chunks.append(temp.strip())
    return chunks

def chunk_image_ocr(ocr_txt, chunk_size=300):
    # OCR 결과를 라인·토큰 기준 청킹
    return chunk_text(ocr_txt, chunk_size)

def run_chunking_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    for job in config["chunking_jobs"]:
        type_ = job["type"]
        input_file = job["input_file"]
        output_folder = job["output_folder"]
        chunk_size = job.get("chunk_size", 500)
        chunk_by = job.get("chunk_by", "row")

        # 입력 파일 로드
        with open(input_file, encoding="utf-8") as f:
            data = f.read()

        # 타입별 청킹 처리
        if type_ == "text":
            chunks = chunk_text(data, chunk_size)
        elif type_ == "table":
            table_json = json.loads(data)
            chunks = chunk_table(table_json, chunk_by)
        elif type_ == "paragraph":
            chunks = chunk_paragraphs(data, chunk_size)
        elif type_ == "image_ocr":
            chunks = chunk_image_ocr(data, chunk_size)
        else:
            print(f"지원하지 않는 청킹 타입: {type_}")
            continue

        for i, chunk in enumerate(chunks):
            safe_write(os.path.join(output_folder, f"chunk_{i+1}.txt"), chunk)

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/chunking_config.json 또는 agents/chunking_config_test.json): ").strip()
    run_chunking_from_config(config_fn)
