import os
import mimetypes
import pandas as pd
from pdfminer.high_level import extract_text as pdf_text
from PIL import Image
import easyocr
import docx
from bs4 import BeautifulSoup
import json

ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)

def safe_write(path, content, mode="w", encoding="utf-8"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if "b" in mode:
        with open(path, mode) as f: f.write(content)
    else:
        with open(path, mode, encoding=encoding) as f: f.write(content)

def parse_txt(file_path, output_folder):
    with open(file_path, encoding="utf-8") as f:
        text = f.read()
    safe_write(os.path.join(output_folder, "txt_text.txt"), text)

def parse_json_file(file_path, output_folder):
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    pretty = json.dumps(data, ensure_ascii=False, indent=2)
    safe_write(os.path.join(output_folder, "json_pretty.json"), pretty)

def parse_csv(file_path, output_folder):
    df = pd.read_csv(file_path)
    df.to_json(os.path.join(output_folder, "csv_table.json"), orient="records", force_ascii=False)

def parse_excel(file_path, output_folder):
    df = pd.read_excel(file_path)
    df.to_json(os.path.join(output_folder, "excel_table.json"), orient="records", force_ascii=False)

def parse_pdf(file_path, output_folder):
    text = pdf_text(file_path)
    safe_write(os.path.join(output_folder, "pdf_text.txt"), text)

def parse_image(file_path, output_folder):
    try:
        img = Image.open(file_path)
        img.save(os.path.join(output_folder, "image_copy"+os.path.splitext(file_path)[-1]))
        result = ocr_reader.readtext(file_path)
        text = "\n".join([line[1] for line in result])
        safe_write(os.path.join(output_folder, "image_ocr.txt"), text)
    except Exception as e:
        print(f"이미지 파싱/OCR 에러: {e}")

def parse_docx(file_path, output_folder):
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    safe_write(os.path.join(output_folder, "docx_text.txt"), "\n".join(paragraphs))

def parse_html(file_path, output_folder):
    with open(file_path, encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "lxml")
    safe_write(os.path.join(output_folder, "html_text.txt"), soup.get_text())
    tables = soup.find_all("table")
    if tables:
        safe_write(os.path.join(output_folder, "html_tables.html"), "\n\n".join(str(t) for t in tables))

def auto_parse_file(file_path, output_folder):
    mimetype, encoding = mimetypes.guess_type(file_path)
    ext = os.path.splitext(file_path)[-1].lower()
    try:
        if ext == ".json":
            parse_json_file(file_path, output_folder)
        elif ext == ".txt":
            parse_txt(file_path, output_folder)
        elif ext == ".csv":
            parse_csv(file_path, output_folder)
        elif ext in [".xls", ".xlsx"]:
            parse_excel(file_path, output_folder)
        elif ext == ".pdf":
            parse_pdf(file_path, output_folder)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"]:
            parse_image(file_path, output_folder)
        elif ext == ".docx":
            parse_docx(file_path, output_folder)
        elif ext in [".html", ".htm"]:
            parse_html(file_path, output_folder)
        else:
            raise Exception(f"지원하지 않는 파일 유형: {ext}")
    except Exception as e:
        print(f"[파싱 에러: {file_path}] — {e}")
    print(f"파싱 완료: {file_path}")

def run_file_parser_from_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    for job in config["parse_jobs"]:
        file_path = job["file_path"]
        output_folder = job["output_folder"]
        auto_parse_file(file_path, output_folder)

if __name__ == "__main__":
    config_fn = input("config 파일 (예: agents/file_parser_config.json 또는 agents/file_parser_config_test.json): ").strip()
    run_file_parser_from_config(config_fn)
