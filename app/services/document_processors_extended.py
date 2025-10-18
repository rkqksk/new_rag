"""
확장 문서 포맷 프로세서
- HWP (한글), YAML, TOML, LATEX, SQL 등 추가 형식 지원
- 다양한 마크업 및 데이터 형식 처리
- 프로그래밍 소스코드 파일 처리
"""

import logging
import os
from typing import List, Dict, Any
from pathlib import Path

from app.services.document_ingestion_service import DocumentChunk

logger = logging.getLogger(__name__)


class ExtendedDocumentProcessors:
    """
    기본 프로세서를 확장한 추가 형식 지원
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def process_hwp(self, file_path: str, doc_id: str,
                         metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        한글 파일 처리 (.hwp)

        한글 문서 형식 처리를 위해 python-pptx와 유사한
        한글 파일 파서 라이브러리 필요 (예: python-hwp)
        """
        chunks = []
        metadata.update({
            "source": "hwp",
            "file_path": file_path,
        })

        try:
            try:
                from hwp_tools import HWPDocument

                doc = HWPDocument(file_path)
                text_buffer = []
                token_count = 0

                for para in doc.paragraphs:
                    text = para.strip()
                    if not text:
                        continue

                    token_estimate = len(text.split()) * 1.3

                    if token_count + token_estimate > self.chunk_size and text_buffer:
                        chunk_text = " ".join(text_buffer)
                        chunk = DocumentChunk(
                            text=chunk_text,
                            doc_id=doc_id,
                            chunk_index=len(chunks),
                            metadata=metadata.copy()
                        )
                        chunks.append(chunk)
                        text_buffer = []
                        token_count = 0

                    text_buffer.append(text)
                    token_count += token_estimate

                if text_buffer:
                    chunk_text = " ".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)

            except ImportError:
                logger.warning("python-hwp not installed, attempting alternative method")
                # Fallback: HWP 파일을 텍스트로 추출하는 대체 방법
                # 한글 2014 이상 버전: ZIP 형식 기반
                import zipfile
                import xml.etree.ElementTree as ET

                try:
                    with zipfile.ZipFile(file_path, 'r') as hwp_zip:
                        # content.xml에서 텍스트 추출
                        if 'content.xml' in hwp_zip.namelist():
                            with hwp_zip.open('content.xml') as f:
                                tree = ET.parse(f)
                                root = tree.getroot()
                                text_content = ET.tostring(root, encoding='unicode')

                                chunk = DocumentChunk(
                                    text=text_content[:5000],  # 제한
                                    doc_id=doc_id,
                                    chunk_index=0,
                                    metadata=metadata.copy()
                                )
                                chunks.append(chunk)
                except Exception as e:
                    logger.error(f"Failed to extract text from HWP: {e}")

        except Exception as e:
            logger.error(f"Error processing HWP {file_path}: {e}")
            raise

        return chunks

    async def process_yaml(self, file_path: str, doc_id: str,
                          metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """YAML 파일 처리 (.yaml, .yml)"""
        chunks = []
        metadata.update({
            "source": "yaml",
            "file_path": file_path,
        })

        try:
            try:
                import yaml

                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                # YAML을 포맷된 텍스트로 변환
                yaml_text = yaml.dump(data, default_flow_style=False, allow_unicode=True)

                text_buffer = []
                token_count = 0

                for line in yaml_text.split('\n'):
                    if not line.strip():
                        continue

                    token_estimate = len(line.split()) * 1.3

                    if token_count + token_estimate > self.chunk_size and text_buffer:
                        chunk_text = "\n".join(text_buffer)
                        chunk = DocumentChunk(
                            text=chunk_text,
                            doc_id=doc_id,
                            chunk_index=len(chunks),
                            metadata=metadata.copy()
                        )
                        chunks.append(chunk)
                        text_buffer = []
                        token_count = 0

                    text_buffer.append(line)
                    token_count += token_estimate

                if text_buffer:
                    chunk_text = "\n".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)

            except ImportError:
                logger.warning("PyYAML not installed, processing as text")
                # Fallback: 평문 처리
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    chunk = DocumentChunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=0,
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing YAML {file_path}: {e}")
            raise

        return chunks

    async def process_toml(self, file_path: str, doc_id: str,
                          metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """TOML 파일 처리 (.toml)"""
        chunks = []
        metadata.update({
            "source": "toml",
            "file_path": file_path,
        })

        try:
            try:
                import toml

                with open(file_path, 'r', encoding='utf-8') as f:
                    data = toml.load(f)

                # TOML을 포맷된 텍스트로 변환
                toml_text = toml.dumps(data)

                text_buffer = []
                token_count = 0

                for line in toml_text.split('\n'):
                    if not line.strip():
                        continue

                    token_estimate = len(line.split()) * 1.3

                    if token_count + token_estimate > self.chunk_size and text_buffer:
                        chunk_text = "\n".join(text_buffer)
                        chunk = DocumentChunk(
                            text=chunk_text,
                            doc_id=doc_id,
                            chunk_index=len(chunks),
                            metadata=metadata.copy()
                        )
                        chunks.append(chunk)
                        text_buffer = []
                        token_count = 0

                    text_buffer.append(line)
                    token_count += token_estimate

                if text_buffer:
                    chunk_text = "\n".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)

            except ImportError:
                logger.warning("toml not installed, processing as text")
                # Fallback: 평문 처리
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    chunk = DocumentChunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=0,
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing TOML {file_path}: {e}")
            raise

        return chunks

    async def process_sql(self, file_path: str, doc_id: str,
                         metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """SQL 스크립트 처리 (.sql)"""
        chunks = []
        metadata.update({
            "source": "sql",
            "file_path": file_path,
        })

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # SQL 문을 세미콜론으로 분할
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]

            text_buffer = []
            token_count = 0

            for statement in statements:
                token_estimate = len(statement.split()) * 1.3

                if token_count + token_estimate > self.chunk_size and text_buffer:
                    chunk_text = ";\n".join(text_buffer) + ";"
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata={**metadata, "chunk_type": "sql_statements"}
                    )
                    chunks.append(chunk)
                    text_buffer = []
                    token_count = 0

                text_buffer.append(statement)
                token_count += token_estimate

            if text_buffer:
                chunk_text = ";\n".join(text_buffer) + ";"
                chunk = DocumentChunk(
                    text=chunk_text,
                    doc_id=doc_id,
                    chunk_index=len(chunks),
                    metadata={**metadata, "chunk_type": "sql_statements"}
                )
                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing SQL {file_path}: {e}")
            raise

        return chunks

    async def process_source_code(self, file_path: str, doc_id: str,
                                 metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        프로그래밍 소스코드 처리
        (.py, .js, .java, .cpp, .go, .rs, .php, .rb, .swift, 등)
        """
        chunks = []

        # 파일 확장자로 언어 감지
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.h': 'c_header',
            '.hpp': 'cpp_header',
            '.go': 'golang',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'shell',
            '.bash': 'bash',
            '.sh': 'shell',
        }

        language = language_map.get(ext, 'unknown')

        metadata.update({
            "source": "source_code",
            "file_path": file_path,
            "language": language,
            "encoding": "utf-8",
        })

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            # 함수/클래스 기반 청킹 시도 (간단한 파서)
            text_buffer = []
            token_count = 0

            for line in code_content.split('\n'):
                token_estimate = len(line.split()) * 1.3

                if token_count + token_estimate > self.chunk_size and text_buffer:
                    chunk_text = "\n".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata={**metadata, "chunk_type": "code_block"}
                    )
                    chunks.append(chunk)
                    text_buffer = []
                    token_count = 0

                text_buffer.append(line)
                token_count += token_estimate

            if text_buffer:
                chunk_text = "\n".join(text_buffer)
                chunk = DocumentChunk(
                    text=chunk_text,
                    doc_id=doc_id,
                    chunk_index=len(chunks),
                    metadata={**metadata, "chunk_type": "code_block"}
                )
                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing source code {file_path}: {e}")
            raise

        return chunks

    async def process_latex(self, file_path: str, doc_id: str,
                           metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """LaTeX 문서 처리 (.tex)"""
        chunks = []
        metadata.update({
            "source": "latex",
            "file_path": file_path,
        })

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                latex_content = f.read()

            # LaTeX 명령 제거하고 텍스트만 추출
            import re

            # 수식 제거
            text = re.sub(r'\$\$.*?\$\$', '', latex_content, flags=re.DOTALL)
            text = re.sub(r'\$.*?\$', '', text)

            # LaTeX 명령 제거
            text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
            text = re.sub(r'\\[a-zA-Z]+', '', text)
            text = re.sub(r'\{|\}', '', text)

            text_buffer = []
            token_count = 0

            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                token_estimate = len(line.split()) * 1.3

                if token_count + token_estimate > self.chunk_size and text_buffer:
                    chunk_text = " ".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata=metadata.copy()
                    )
                    chunks.append(chunk)
                    text_buffer = []
                    token_count = 0

                text_buffer.append(line)
                token_count += token_estimate

            if text_buffer:
                chunk_text = " ".join(text_buffer)
                chunk = DocumentChunk(
                    text=chunk_text,
                    doc_id=doc_id,
                    chunk_index=len(chunks),
                    metadata=metadata.copy()
                )
                chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing LaTeX {file_path}: {e}")
            raise

        return chunks

    async def process_markdown(self, file_path: str, doc_id: str,
                              metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Markdown 파일 처리 (.md, .markdown)"""
        chunks = []
        metadata.update({
            "source": "markdown",
            "file_path": file_path,
        })

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # 마크다운을 섹션 단위로 처리
            sections = markdown_content.split('\n#')

            for section in sections:
                section = section.strip()
                if not section:
                    continue

                # 섹션이 크면 추가 분할
                text_buffer = []
                token_count = 0

                for line in section.split('\n'):
                    token_estimate = len(line.split()) * 1.3

                    if token_count + token_estimate > self.chunk_size and text_buffer:
                        chunk_text = "\n".join(text_buffer)
                        chunk = DocumentChunk(
                            text=chunk_text,
                            doc_id=doc_id,
                            chunk_index=len(chunks),
                            metadata={**metadata, "chunk_type": "markdown_section"}
                        )
                        chunks.append(chunk)
                        text_buffer = []
                        token_count = 0

                    text_buffer.append(line)
                    token_count += token_estimate

                if text_buffer:
                    chunk_text = "\n".join(text_buffer)
                    chunk = DocumentChunk(
                        text=chunk_text,
                        doc_id=doc_id,
                        chunk_index=len(chunks),
                        metadata={**metadata, "chunk_type": "markdown_section"}
                    )
                    chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing Markdown {file_path}: {e}")
            raise

        return chunks
