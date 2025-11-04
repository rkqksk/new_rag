# Symbol Loading Optimization Strategy

**목표**: 심볼 로드 시에도 토큰 소비를 최소화하는 계층적 시스템 구축

---

## 🎯 문제 정의

### 현재 상황
```
사용자: "§rag.phase2.vector 내용 확인"
시스템: RAG_ACTIVATION_STRATEGY.md 전체 로드 (18KB = ~4,500 tokens)
```

**문제**: 특정 섹션만 필요한데 전체 문서를 로드

### 목표 상황
```
사용자: "§rag.phase2.vector 내용 확인"
시스템: VectorSearch 섹션만 추출 (200 lines = ~500 tokens)
```

**개선**: 90% 토큰 절감 (4,500 → 500 tokens)

---

## 📊 전략 개요

### 1. 계층적 심볼 시스템 (3-Level)

```
Level 1: §category          → 목차 + 개요 (100-200 tokens)
Level 2: §category.section  → 섹션만 (500-1000 tokens)
Level 3: §category.section.detail → 전체 상세 (2000+ tokens)
```

**예시**:
```
§rag                    → RAG 전략 개요 + 목차
§rag.phase2             → Phase 2 섹션 (3가지 모듈 개요)
§rag.phase2.vector      → VectorSearch 모듈 상세 코드
§rag.phase2.vector.full → VectorSearch + 예제 + 테스트
```

---

### 2. 압축 요약본 (Compressed Summaries)

각 문서마다 3가지 버전 생성:

| 버전 | 크기 | 내용 | 토큰 | 사용 시점 |
|------|------|------|------|----------|
| `.summary.md` | 10% | 핵심 요약 | ~500 | 빠른 참조 |
| `.outline.md` | 30% | 목차 + 주요 내용 | ~1,500 | 구조 파악 |
| `.md` | 100% | 전체 문서 | ~5,000 | 상세 작업 |

**디렉토리 구조**:
```
docs/
├── ARCHITECTURE.md                    # 전체 (31KB)
├── .summaries/
│   ├── ARCHITECTURE.summary.md       # 요약 (3KB)
│   └── ARCHITECTURE.outline.md       # 목차 (9KB)
├── RAG_ACTIVATION_STRATEGY.md         # 전체 (18KB)
└── .summaries/
    ├── RAG_ACTIVATION_STRATEGY.summary.md   # 요약 (2KB)
    └── RAG_ACTIVATION_STRATEGY.outline.md   # 목차 (5KB)
```

---

### 3. 자동 섹션 추출 (Auto Section Extraction)

Markdown 헤더 기반 자동 섹션 추출:

```python
def extract_section(file_path: str, symbol: str) -> str:
    """
    심볼에 해당하는 섹션만 추출

    Example:
        extract_section('docs/RAG_ACTIVATION_STRATEGY.md', '§rag.phase2.vector')
        → "### Phase 2.1 VectorSearch 모듈" 섹션만 반환
    """
    # 1. 심볼 파싱: §rag.phase2.vector
    parts = symbol.replace('§', '').split('.')
    # ['rag', 'phase2', 'vector']

    # 2. 파일 읽기
    content = read_file(file_path)

    # 3. 헤더 매칭
    # "## Phase 2" → "### 2.1 VectorSearch" 섹션 추출

    # 4. 해당 섹션만 반환
    return extracted_section
```

**토큰 절감**:
- 전체 문서: ~4,500 tokens
- 추출된 섹션: ~500 tokens
- 절감: 89%

---

### 4. Skill 문서 심볼화

현재 `.claude/skills/` 문서들은 심볼화되지 않음:

```
.claude/skills/
├── rag-pipeline/
│   ├── README.md (5KB)           → §skill.rag
│   ├── USAGE.md (3KB)            → §skill.rag.usage
│   └── scripts/
│       ├── parsers/README.md     → §skill.rag.parsers
│       └── chunking/README.md    → §skill.rag.chunking
├── manufacturing-expert/
│   └── README.md                 → §skill.manufacturing
└── packaging-expert/
    └── README.md                 → §skill.packaging
```

**심볼 맵 확장**:
```yaml
§skill.rag:
  file: .claude/skills/rag-pipeline/README.md
  summary: .claude/skills/rag-pipeline/.summary.md
  sections:
    - §skill.rag.overview
    - §skill.rag.commands
    - §skill.rag.usage
    - §skill.rag.parsers
    - §skill.rag.chunking
```

---

## 🛠️ 구현 계획

### Phase 1: 섹션 추출 도구 (1시간)

**파일**: `scripts/symbol_extractor.py`

```python
#!/usr/bin/env python3
"""
Symbol-based section extractor for efficient document loading
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

class SymbolExtractor:
    """Extract specific sections from Markdown documents based on symbols"""

    SYMBOL_MAP = {
        'rag': {
            'file': 'docs/RAG_ACTIVATION_STRATEGY.md',
            'sections': {
                'status': ('## 📊 Executive Summary', '## 🎯 전략 개요'),
                'phase2': ('## Phase 2', '## Phase 3'),
                'phase2.vector': ('#### 2.1 VectorSearch', '#### 2.2 DocumentProcessor'),
                'phase2.processor': ('#### 2.2 DocumentProcessor', '#### 2.3 RAGEngine'),
                'phase2.engine': ('#### 2.3 RAGEngine', '## Phase 3'),
            }
        },
        'arch': {
            'file': 'docs/ARCHITECTURE.md',
            'sections': {
                'overview': ('## 5계층 아키텍처', '## Layer 1'),
                'core.layers': ('## 5계층 아키텍처', '## Layer 1'),
                'core.skills': ('### SKILL', '### Plugin'),
            }
        },
        'ui': {
            'file': 'docs/FRONTEND_UI_POLICY.md',
            'sections': {
                'design.colors': ('#### 색상 팔레트', '#### 타이포그래피'),
                'design.typography': ('#### 타이포그래피', '#### 레이아웃'),
            }
        }
    }

    def extract(self, symbol: str) -> str:
        """
        Extract section by symbol

        Args:
            symbol: Symbol like '§rag.phase2.vector'

        Returns:
            Extracted section content
        """
        # Parse symbol
        symbol_clean = symbol.replace('§', '')
        parts = symbol_clean.split('.')

        category = parts[0]
        section_key = '.'.join(parts[1:]) if len(parts) > 1 else 'overview'

        # Get file path
        if category not in self.SYMBOL_MAP:
            return f"❌ Unknown symbol category: {category}"

        file_path = self.SYMBOL_MAP[category]['file']

        # Load full if no specific section
        if section_key == 'overview' or section_key not in self.SYMBOL_MAP[category]['sections']:
            return self._load_file(file_path)

        # Extract section
        start_marker, end_marker = self.SYMBOL_MAP[category]['sections'][section_key]
        return self._extract_section(file_path, start_marker, end_marker)

    def _load_file(self, file_path: str) -> str:
        """Load full file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_section(self, file_path: str, start: str, end: str) -> str:
        """Extract section between start and end markers"""
        content = self._load_file(file_path)

        # Find start position
        start_pos = content.find(start)
        if start_pos == -1:
            return f"❌ Section start not found: {start}"

        # Find end position
        end_pos = content.find(end, start_pos + len(start))
        if end_pos == -1:
            # If no end marker, take until next same-level header
            end_pos = len(content)

        section = content[start_pos:end_pos].strip()

        # Add header
        header = f"# Extracted Section: {start}\n\n"
        return header + section

    def get_outline(self, symbol: str) -> str:
        """Get outline/TOC for a symbol"""
        symbol_clean = symbol.replace('§', '')
        parts = symbol_clean.split('.')
        category = parts[0]

        if category not in self.SYMBOL_MAP:
            return f"❌ Unknown symbol: {symbol}"

        file_path = self.SYMBOL_MAP[category]['file']
        content = self._load_file(file_path)

        # Extract all headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

        outline = f"# Outline: {symbol}\n\n"
        for level, title in headers:
            indent = '  ' * (len(level) - 1)
            outline += f"{indent}- {title}\n"

        return outline


# CLI Interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python symbol_extractor.py <symbol>")
        print("Example: python symbol_extractor.py §rag.phase2.vector")
        sys.exit(1)

    symbol = sys.argv[1]
    extractor = SymbolExtractor()

    # Check for --outline flag
    if '--outline' in sys.argv:
        result = extractor.get_outline(symbol)
    else:
        result = extractor.extract(symbol)

    print(result)
```

**사용법**:
```bash
# 특정 섹션만 추출
python scripts/symbol_extractor.py §rag.phase2.vector

# 목차만 보기
python scripts/symbol_extractor.py §rag --outline

# 전체 문서
python scripts/symbol_extractor.py §rag
```

---

### Phase 2: 압축 요약본 생성 (2시간)

**파일**: `scripts/generate_summaries.py`

```python
#!/usr/bin/env python3
"""
Generate compressed summaries for all documentation
"""
import ollama
from pathlib import Path

def generate_summary(file_path: Path) -> str:
    """Generate 10% summary using Ollama"""

    # Read full document
    with open(file_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Calculate target length (10% of original)
    original_lines = len(full_content.split('\n'))
    target_lines = max(10, original_lines // 10)

    # Prompt for Ollama
    prompt = f"""다음 문서를 {target_lines}줄 이내로 요약해주세요.
핵심 내용만 추출하고, 마크다운 형식을 유지하세요.

원본 문서:
{full_content}

요약 (핵심만, {target_lines}줄 이내):"""

    # Call Ollama
    response = ollama.generate(
        model='qwen2.5:7b-instruct',
        prompt=prompt
    )

    return response['response']

def generate_outline(file_path: Path) -> str:
    """Generate 30% outline using Ollama"""

    with open(file_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    original_lines = len(full_content.split('\n'))
    target_lines = original_lines // 3

    prompt = f"""다음 문서의 목차와 주요 내용을 {target_lines}줄 이내로 정리해주세요.
각 섹션의 핵심 포인트만 포함하세요.

원본 문서:
{full_content}

목차 및 주요 내용 ({target_lines}줄 이내):"""

    response = ollama.generate(
        model='qwen2.5:7b-instruct',
        prompt=prompt
    )

    return response['response']

def main():
    """Generate summaries for all docs"""

    docs_dir = Path('docs')
    summaries_dir = docs_dir / '.summaries'
    summaries_dir.mkdir(exist_ok=True)

    # Target files
    target_files = [
        'ARCHITECTURE.md',
        'RAG_ACTIVATION_STRATEGY.md',
        'FRONTEND_UI_POLICY.md',
        'OLLAMA_MODEL_POLICY.md',
    ]

    for filename in target_files:
        file_path = docs_dir / filename
        if not file_path.exists():
            continue

        print(f"Processing {filename}...")

        # Generate summary (10%)
        summary = generate_summary(file_path)
        summary_path = summaries_dir / f"{file_path.stem}.summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# {file_path.stem} - Summary\n\n")
            f.write(f"> Auto-generated 10% summary\n\n")
            f.write(summary)
        print(f"  ✅ Summary: {summary_path}")

        # Generate outline (30%)
        outline = generate_outline(file_path)
        outline_path = summaries_dir / f"{file_path.stem}.outline.md"
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(f"# {file_path.stem} - Outline\n\n")
            f.write(f"> Auto-generated 30% outline\n\n")
            f.write(outline)
        print(f"  ✅ Outline: {outline_path}")

if __name__ == '__main__':
    main()
```

**실행**:
```bash
python scripts/generate_summaries.py
```

---

### Phase 3: CLAUDE.md 통합 (30분)

CLAUDE.md에 로딩 레벨 가이드 추가:

```markdown
## 📖 Symbol Loading Levels

### Level 1: Quick Reference (기본)
```bash
§rag                    # 요약만 (~500 tokens)
§arch                   # 개요만 (~200 tokens)
```

### Level 2: Section Load
```bash
§rag.phase2             # Phase 2 섹션만 (~1,000 tokens)
§arch.core.skills       # SKILL 섹션만 (~800 tokens)
```

### Level 3: Full Detail
```bash
§rag.full               # 전체 문서 (~4,500 tokens)
§arch.full              # 전체 문서 (~7,750 tokens)
```

### 자동 추출
```bash
# 명령어로 섹션 추출
python scripts/symbol_extractor.py §rag.phase2.vector
```
```

---

## 📊 예상 토큰 절감

### 시나리오 1: RAG 개발 작업

**기존 방식**:
```
1. CLAUDE.md 로드: 500 tokens
2. RAG_ACTIVATION_STRATEGY.md 전체: 4,500 tokens
3. ARCHITECTURE.md 전체: 7,750 tokens
─────────────────────────────────
Total: 12,750 tokens
```

**새 방식**:
```
1. CLAUDE.md (symbolized): 150 tokens
2. §rag.phase2 (section only): 1,000 tokens
3. §arch.core.layers (section only): 800 tokens
─────────────────────────────────
Total: 1,950 tokens
```

**절감**: 84.7% (12,750 → 1,950 tokens)

---

### 시나리오 2: UI 색상 변경

**기존**:
```
1. CLAUDE.md: 500 tokens
2. FRONTEND_UI_POLICY.md 전체: 3,250 tokens
─────────────────────────────────
Total: 3,750 tokens
```

**새 방식**:
```
1. CLAUDE.md: 150 tokens
2. §ui.design.colors (section): 200 tokens
─────────────────────────────────
Total: 350 tokens
```

**절감**: 90.7% (3,750 → 350 tokens)

---

## 🎯 최종 토큰 절감 전망

| 작업 유형 | 기존 | 새 방식 | 절감 |
|----------|------|---------|------|
| RAG 개발 | 12,750 | 1,950 | 84.7% |
| UI 변경 | 3,750 | 350 | 90.7% |
| 모델 관리 | 7,000 | 600 | 91.4% |
| 일반 참조 | 5,000 | 500 | 90.0% |
| **평균** | **7,125** | **850** | **88.1%** |

**100 세션 영향**:
- 기존: 712,500 tokens
- 새 방식: 85,000 tokens
- **절감: 627,500 tokens (~88%)**

---

## 🚀 실행 우선순위

### Immediate (지금 바로)
1. ✅ `scripts/symbol_extractor.py` 개발
2. ✅ SYMBOL_MAP 정의

### High Priority (오늘)
3. `scripts/generate_summaries.py` 개발
4. 주요 문서 요약본 생성

### Medium Priority (내일)
5. Skill 문서 심볼화
6. CLAUDE.md 로딩 레벨 가이드 추가

### Low Priority (필요시)
7. 자동화 스크립트 (문서 업데이트 시 자동 요약)
8. 심볼 검색 도구

---

**Version**: 1.0.0
**Created**: 2025-11-04
**Next Review**: After Phase 1 implementation
