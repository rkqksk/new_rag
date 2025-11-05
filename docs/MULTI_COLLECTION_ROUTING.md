# Multi-Collection Routing Design

> **Symbol Reference**: §rag.routing
> **Quick Access**: See `CLAUDE.md` for status
> **Purpose**: 크롤링/업로드된 데이터를 선별적으로 고객에게 라우팅

---

## 📊 Executive Summary

**목표**: 다중 데이터 소스를 독립적인 컬렉션으로 관리하고, 고객이 체크박스로 선택적으로 검색

**사용 사례**:
- 고객 A: 청진코리아 데이터만 활성화
- 고객 B: 원하고 + 프리몰드 데이터 활성화
- 관리자: 모든 데이터 소스 활성화

**현재 상태**: 설계 단계
**구현 예정**: 5단계 (3-4일 예상)

---

## 🎯 핵심 개념

### 컬렉션 = 데이터 소스

```
Qdrant Collections:
├── products         → 기존 (청진코리아 857개) - 유지
├── chungjinkorea    → 청진코리아 (신규, products와 동일 데이터)
├── onehago          → 원하고
├── freemold         → 프리몰드
├── cosmorning       → 코스모닝
├── jangup           → 장업
└── plastics_kr      → 플라스틱넷
```

**설계 결정**:
1. **컬렉션 네이밍**: 데이터 소스 이름 그대로 (chungjinkorea, onehago, ...)
2. **기존 "products"**: 그대로 유지 (삭제하지 않음)
3. **독립성**: 각 컬렉션은 완전히 독립적 (cross-collection 검색 지원)

---

## 📋 데이터 소스 현황

### 현재 크롤링된 데이터

| 소스 | 컬렉션 이름 | 경로 | 파일 수 | 상태 |
|------|------------|------|---------|------|
| 청진코리아 | chungjinkorea | data/crawled/chungjinkorea | 857 | ✅ Embedded (products) |
| 원하고 | onehago | data/crawled/onehago | TBD | ⏳ Pending |
| 프리몰드 | freemold | data/crawled/freemold | TBD | ⏳ Pending |
| 코스모닝 | cosmorning | data/crawled/cosmorning | TBD | ⏳ Pending |
| 장업 | jangup | data/crawled/jangup | TBD | ⏳ Pending |
| 플라스틱넷 | plastics_kr | data/crawled/plastics_kr | TBD | ⏳ Pending |

---

## 🏗️ 아키텍처 설계

### 1. Collection Registry (컬렉션 등록부)

**파일**: `config/collections.yaml` (신규)

```yaml
collections:
  chungjinkorea:
    name: "청진코리아"
    data_path: "data/crawled/chungjinkorea"
    description: "청진코리아 용기 제품"
    enabled: true
    embedded: true
    total_documents: 857
    last_updated: "2025-11-04"

  onehago:
    name: "원하고"
    data_path: "data/crawled/onehago"
    description: "원하고 포장 용기"
    enabled: true
    embedded: false
    total_documents: 0
    last_updated: null

  freemold:
    name: "프리몰드"
    data_path: "data/crawled/freemold"
    description: "프리몰드 제품"
    enabled: true
    embedded: false
    total_documents: 0
    last_updated: null
```

---

### 2. Skill 인터페이스 확장

#### 새로운 파라미터

**process_document()**:
```python
skill.execute('process', {
    'file_path': 'data/crawled/onehago/product_1.json',
    'options': {
        'collection_name': 'onehago'  # ← 컬렉션 지정
    }
})
```

**vector_search()**:
```python
skill.execute('search', {
    'query': '50ml bottle',
    'collections': ['chungjinkorea', 'onehago'],  # ← 다중 컬렉션
    'top_k': 10
})
```

**rag_query()**:
```python
skill.execute('query', {
    'question': 'What bottles are available?',
    'collections': ['chungjinkorea'],  # ← 선택된 컬렉션만
    'top_k': 5
})
```

#### 새로운 명령어

```python
# 1. 컬렉션 목록 조회
skill.execute('list_collections')
# Returns:
{
    'collections': [
        {'id': 'chungjinkorea', 'name': '청진코리아', 'count': 857, 'embedded': True},
        {'id': 'onehago', 'name': '원하고', 'count': 0, 'embedded': False},
        # ...
    ]
}

# 2. 컬렉션 통계
skill.execute('collection_stats', {'collection_name': 'chungjinkorea'})
# Returns:
{
    'collection_name': 'chungjinkorea',
    'total_documents': 857,
    'total_chunks': 1024,
    'embedding_dimension': 384,
    'last_updated': '2025-11-04'
}

# 3. 배치 임베딩 (폴더 단위)
skill.execute('embed_collection', {
    'collection_name': 'onehago',
    'data_path': 'data/crawled/onehago',
    'batch_size': 50
})

# 4. 컬렉션 삭제
skill.execute('delete_collection', {'collection_name': 'onehago'})
```

---

### 3. 다중 컬렉션 검색 로직

**구현 방식**: Sequential Search + Merge

```python
def search_multiple_collections(query, collections, top_k):
    """
    여러 컬렉션을 순차 검색 후 결과 병합

    Args:
        query: 검색 쿼리
        collections: ['chungjinkorea', 'onehago']
        top_k: 총 반환할 결과 수

    Returns:
        Merged and sorted results
    """
    all_results = []

    # 각 컬렉션 검색
    for collection_name in collections:
        pipeline = get_pipeline(collection_name)
        results = pipeline.retrieve(query, top_k=top_k * 2)  # 여유있게 가져오기

        # 메타데이터에 소스 추가
        for r in results:
            r['metadata']['source_collection'] = collection_name
            r['metadata']['source_name'] = COLLECTIONS[collection_name]['name']

        all_results.extend(results)

    # Score 기준 정렬
    all_results.sort(key=lambda x: x['score'], reverse=True)

    # Top-K만 반환
    return all_results[:top_k]
```

**성능 고려사항**:
- 컬렉션 3개, top_k=10 → 최대 30개 검색 → 10개 반환
- 병렬화 가능 (ThreadPoolExecutor)
- 캐싱 가능 (동일 쿼리 반복 시)

---

### 4. API 변경사항

#### POST /chat/query

**요청**:
```json
{
    "session_id": "abc123",
    "query": "50ml PET bottle",
    "collections": ["chungjinkorea", "onehago"]  // ← 새 파라미터
}
```

**응답**:
```json
{
    "session_id": "abc123",
    "query": "50ml PET bottle",
    "products": [
        {
            "idx": "1",
            "product_name": "50ml PET bottle",
            "source_collection": "chungjinkorea",
            "source_name": "청진코리아",
            "score": 0.8234
        }
    ],
    "response": "다음 50ml PET 용기를 찾았습니다...",
    "total_count": 5,
    "collections_searched": ["chungjinkorea", "onehago"]
}
```

#### GET /collections (신규)

**요청**:
```
GET /collections
```

**응답**:
```json
{
    "collections": [
        {
            "id": "chungjinkorea",
            "name": "청진코리아",
            "enabled": true,
            "embedded": true,
            "document_count": 857,
            "last_updated": "2025-11-04"
        },
        {
            "id": "onehago",
            "name": "원하고",
            "enabled": true,
            "embedded": false,
            "document_count": 0,
            "last_updated": null
        }
    ]
}
```

---

### 5. Frontend UI

#### 컬렉션 선택 UI

```html
<div class="collection-selector">
    <h4>데이터 소스 선택</h4>

    <label class="collection-checkbox">
        <input type="checkbox" value="chungjinkorea" checked>
        <span class="collection-name">청진코리아</span>
        <span class="collection-count">(857)</span>
        <span class="badge badge-success">활성</span>
    </label>

    <label class="collection-checkbox">
        <input type="checkbox" value="onehago">
        <span class="collection-name">원하고</span>
        <span class="collection-count">(0)</span>
        <span class="badge badge-pending">대기</span>
    </label>

    <!-- ... -->
</div>
```

#### JavaScript 로직

```javascript
// 선택된 컬렉션 가져오기
function getSelectedCollections() {
    const checkboxes = document.querySelectorAll('.collection-checkbox input:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// 쿼리 전송
async function sendQuery(query) {
    const collections = getSelectedCollections();

    if (collections.length === 0) {
        alert('최소 1개 이상의 데이터 소스를 선택하세요.');
        return;
    }

    const response = await fetch('/chat/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            query: query,
            collections: collections
        })
    });

    // ...
}

// 페이지 로드 시 컬렉션 목록 가져오기
async function loadCollections() {
    const response = await fetch('/collections');
    const data = await response.json();

    renderCollectionCheckboxes(data.collections);
}
```

---

## 🚀 5단계 구현 계획

### Phase 1: 전체 설계 문서화 (0.5일)
**현재 단계** ✅

**산출물**:
- ✅ `docs/MULTI_COLLECTION_ROUTING.md`
- ⏳ `config/collections.yaml` (컬렉션 등록부)
- ⏳ CLAUDE.md 업데이트 (§rag.routing)
- ⏳ CHANGELOG.md 업데이트

---

### Phase 2: Skill 수정 (1일)

**작업 항목**:

1. **컬렉션 파라미터 지원**
   - `process_document()`: collection_name 옵션 추가
   - `vector_search()`: collections 파라미터 추가
   - `rag_query()`: collections 파라미터 추가

2. **다중 컬렉션 검색 구현**
   ```python
   def _search_multiple_collections(self, query, collections, top_k):
       # 순차 검색 + 병합 로직
   ```

3. **새로운 명령어 추가**
   - `list_collections()`
   - `collection_stats(collection_name)`
   - `embed_collection(collection_name, data_path)`
   - `delete_collection(collection_name)`

4. **컬렉션 레지스트리 로딩**
   ```python
   import yaml

   def load_collection_registry():
       with open('config/collections.yaml') as f:
           return yaml.safe_load(f)
   ```

**테스트**:
```python
# 단일 컬렉션
result = skill.execute('search', {
    'query': '50ml bottle',
    'collections': ['chungjinkorea']
})

# 다중 컬렉션
result = skill.execute('search', {
    'query': '50ml bottle',
    'collections': ['chungjinkorea', 'onehago']
})
```

**산출물**:
- `.claude/skills/rag-pipeline/scripts/skill.py` (업데이트)
- `.claude/skills/rag-pipeline/scripts/collection_manager.py` (신규)

---

### Phase 3: API 업데이트 (1일)

**작업 항목**:

1. **chat.py 수정**
   ```python
   @router.post("/query")
   async def chat_query(request: ChatQueryRequest):
       # collections 파라미터 처리
       collections = request.collections or ['chungjinkorea']  # 기본값

       # Skill 호출
       result = skill.execute('query', {
           'question': request.query,
           'collections': collections,
           'top_k': 10
       })
   ```

2. **Pydantic 모델 업데이트**
   ```python
   class ChatQueryRequest(BaseModel):
       session_id: str
       query: str
       collections: Optional[List[str]] = None  # ← 새 필드
   ```

3. **새 엔드포인트 추가**
   ```python
   @router.get("/collections")
   async def get_collections():
       result = skill.execute('list_collections')
       return result
   ```

**테스트**:
```bash
# 컬렉션 목록 조회
curl http://localhost:8001/collections

# 다중 컬렉션 검색
curl -X POST http://localhost:8001/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "query": "50ml bottle",
    "collections": ["chungjinkorea", "onehago"]
  }'
```

**산출물**:
- `src/api/chat.py` (업데이트)
- `src/api/routes/collection_routes.py` (신규, 선택사항)

---

### Phase 4: Frontend UI (1일)

**작업 항목**:

1. **컬렉션 선택 UI 추가**
   ```html
   <!-- frontend/chat.html -->
   <div class="sidebar-section">
       <h4>데이터 소스</h4>
       <div id="collection-selector"></div>
   </div>
   ```

2. **JavaScript 로직**
   ```javascript
   // 컬렉션 목록 로드
   async function loadCollections() {
       const resp = await fetch('/collections');
       const data = await resp.json();
       renderCollections(data.collections);
   }

   // 체크박스 렌더링
   function renderCollections(collections) {
       const html = collections.map(c => `
           <label>
               <input type="checkbox" value="${c.id}"
                      ${c.embedded ? 'checked' : 'disabled'}>
               ${c.name} (${c.document_count})
               ${c.embedded ? '✅' : '⏳'}
           </label>
       `).join('');

       document.getElementById('collection-selector').innerHTML = html;
   }

   // 쿼리 전송 시 선택된 컬렉션 포함
   function getSelectedCollections() {
       return Array.from(
           document.querySelectorAll('#collection-selector input:checked')
       ).map(cb => cb.value);
   }
   ```

3. **CSS 스타일**
   ```css
   .collection-selector {
       padding: 16px;
       background: #f7f7f8;
       border-radius: 8px;
   }

   .collection-checkbox {
       display: flex;
       align-items: center;
       padding: 8px;
       cursor: pointer;
   }

   .collection-checkbox:hover {
       background: #ececf1;
   }

   .badge-success { color: #10a37f; }
   .badge-pending { color: #ef4444; }
   ```

**테스트**:
- [ ] 컬렉션 목록 로드 확인
- [ ] 체크박스 선택/해제 동작 확인
- [ ] 선택된 컬렉션으로 검색 확인
- [ ] 임베딩 안 된 컬렉션은 disabled 확인

**산출물**:
- `frontend/chat.html` (업데이트)
- `frontend/styles.css` (업데이트, 선택사항)

---

### Phase 5: 테스트 및 검증 (0.5일)

**테스트 시나리오**:

1. **단일 컬렉션 검색**
   - 청진코리아만 선택 → 857개 중 검색
   - 결과에 source_collection 확인

2. **다중 컬렉션 검색**
   - 청진코리아 + 원하고 선택
   - 두 소스에서 결과 병합 확인
   - Score 정렬 확인

3. **컬렉션 관리**
   - 컬렉션 목록 조회
   - 컬렉션 통계 조회
   - 새 컬렉션 임베딩 (onehago)

4. **엣지 케이스**
   - 컬렉션 0개 선택 → 에러 처리
   - 존재하지 않는 컬렉션 → 에러 처리
   - 임베딩 안 된 컬렉션 검색 → 빈 결과

**테스트 스크립트**: `scripts/test_multi_collection.py`

```python
#!/usr/bin/env python3
"""Multi-Collection Routing Test"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from .claude.skills.rag_pipeline.scripts.skill import execute

def test_single_collection():
    """단일 컬렉션 검색"""
    result = execute('search', {
        'query': '50ml PET bottle',
        'collections': ['chungjinkorea'],
        'top_k': 5
    })

    assert result['status'] == 'success'
    assert len(result['results']) <= 5
    assert all(r['metadata']['source_collection'] == 'chungjinkorea'
               for r in result['results'])
    print("✅ Single collection test passed")

def test_multi_collection():
    """다중 컬렉션 검색"""
    result = execute('search', {
        'query': '50ml bottle',
        'collections': ['chungjinkorea', 'onehago'],
        'top_k': 10
    })

    assert result['status'] == 'success'
    assert len(result['results']) <= 10

    sources = set(r['metadata']['source_collection'] for r in result['results'])
    print(f"✅ Multi collection test passed (sources: {sources})")

def test_list_collections():
    """컬렉션 목록 조회"""
    result = execute('list_collections')

    assert 'collections' in result
    assert len(result['collections']) > 0

    for c in result['collections']:
        assert 'id' in c
        assert 'name' in c
        assert 'embedded' in c

    print(f"✅ List collections test passed ({len(result['collections'])} collections)")

if __name__ == '__main__':
    test_single_collection()
    test_multi_collection()
    test_list_collections()
    print("\n✅ All tests passed!")
```

**성능 테스트**:
```python
def test_search_performance():
    """검색 성능 측정"""
    import time

    # 단일 컬렉션
    start = time.time()
    execute('search', {'query': 'bottle', 'collections': ['chungjinkorea']})
    single_time = time.time() - start

    # 다중 컬렉션 (3개)
    start = time.time()
    execute('search', {
        'query': 'bottle',
        'collections': ['chungjinkorea', 'onehago', 'freemold']
    })
    multi_time = time.time() - start

    print(f"Single collection: {single_time:.2f}s")
    print(f"Multi collection (3): {multi_time:.2f}s")
    print(f"Overhead: {(multi_time/single_time - 1)*100:.1f}%")
```

**산출물**:
- `scripts/test_multi_collection.py` (신규)
- 테스트 결과 문서
- 성능 벤치마크

---

## 📊 기대 효과

### 1. 선택적 데이터 제공
- 고객별로 다른 데이터 소스 제공 가능
- 라이선스/계약에 따른 데이터 접근 제어

### 2. 데이터 격리
- 각 소스의 독립성 보장
- 크롤링 오류 시 다른 소스에 영향 없음

### 3. 확장성
- 새 데이터 소스 추가 간편 (config 파일만 수정)
- 임베딩/삭제 독립적으로 가능

### 4. 유연한 검색
- 단일/다중 컬렉션 검색
- 소스별 가중치 적용 가능 (추후)

---

## ⚠️ 고려사항

### 1. 검색 성능
- **문제**: 컬렉션 N개 → N배 검색 시간
- **해결**:
  - 병렬 검색 (ThreadPoolExecutor)
  - 캐싱
  - 컬렉션 수 제한 (최대 5개)

### 2. 결과 중복
- **문제**: 같은 제품이 여러 소스에 존재할 수 있음
- **해결**:
  - product_code 기준 중복 제거
  - 또는 모두 표시 (소스 정보 포함)

### 3. 컬렉션 동기화
- **문제**: collections.yaml과 실제 Qdrant 불일치
- **해결**:
  - 시작 시 검증
  - 자동 sync 기능

### 4. 메모리/디스크
- **문제**: 컬렉션 증가 시 리소스 부족
- **해결**:
  - 컬렉션 아카이빙 (사용 안 하는 것 삭제)
  - Qdrant 용량 모니터링

---

## 🔄 다음 단계

**Phase 2 시작 조건**:
- ✅ 설계 문서 작성 완료
- ✅ collections.yaml 작성 완료
- ✅ CLAUDE.md 업데이트 완료
- ✅ 사용자 승인

**Phase 2 작업**:
1. collections.yaml 생성
2. skill.py 수정 (collection_name 파라미터)
3. 다중 컬렉션 검색 로직 구현
4. 새 명령어 추가 (list_collections, etc.)

---

**Version**: 1.0.0
**Created**: 2025-11-04
**Status**: Design Complete, Ready for Implementation
