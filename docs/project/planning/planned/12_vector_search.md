# Plan 12: Vector Search & Semantic Tool Routing (Draft)

> **상태:** 📋 Draft
> **선행 조건:** Plan 07 Complete (MCP SDK 통합)
> **목표:** Vector Search를 활용한 Semantic Tool Routing (50+ 도구 시 자동 활성화)

---

## Overview

**핵심 문제:**
- 현재: 도구 검색이 문자열 매칭에만 의존 (정확도 제한)
- 필요: 50개 이상의 도구가 등록되면 Semantic Search로 자동 전환

**구현 범위:**
1. **Vector Store**: ChromaDB 기반 임베딩 저장소
2. **Tool Embedding Service**: 도구 설명 → 벡터 변환
3. **Semantic Router**: 사용자 쿼리 → 관련 도구 검색
4. **Auto Activation**: 도구 수 임계값 기반 자동 활성화
5. **Optional Dependency**: `pip install agenthub[vector]` (선택적 설치)

**참고 문서:**
- 아카이브: `_archive/migration/20260204/plans/phase6/backup-20260203/phase6.0-original.md` (Step 15)

---

## Key Features

### 1. Vector Store (ChromaDB)

**Adapter (Outbound):**
```python
class VectorStoreAdapter:
    """ChromaDB 기반 벡터 저장소"""

    async def add_tool_embedding(self, tool_id: str, embedding: list[float], metadata: dict) -> None:
        """도구 임베딩 추가"""

    async def search_similar_tools(self, query_embedding: list[float], top_k: int = 5) -> list[str]:
        """유사 도구 검색 (코사인 유사도)"""

    async def delete_tool_embedding(self, tool_id: str) -> None:
        """도구 임베딩 삭제"""
```

**설정:**
```python
@dataclass
class VectorSearchConfig:
    """Vector Search 설정 (순수 Python)"""
    enabled: bool = False  # 기본값: 비활성화
    auto_activation_threshold: int = 50  # 도구 수 임계값
    embedding_model: str = "text-embedding-3-small"  # OpenAI 임베딩 모델
    top_k: int = 5  # 검색 결과 수
    similarity_threshold: float = 0.7  # 유사도 임계값 (0.0 ~ 1.0)
```

### 2. Tool Embedding Service

**Domain Service:**
```python
class ToolEmbeddingService:
    """도구 임베딩 생성 및 관리"""

    async def embed_tool(self, tool: Tool) -> list[float]:
        """도구 설명 → 벡터 변환 (LLM API)"""

    async def rebuild_index(self, tools: list[Tool]) -> None:
        """전체 도구 인덱스 재구축"""

    async def should_activate_vector_search(self, tool_count: int) -> bool:
        """Vector Search 활성화 여부 판단"""
```

**임베딩 소스:**
```python
def _get_tool_description(self, tool: Tool) -> str:
    """임베딩용 텍스트 생성"""
    return f"{tool.name}: {tool.description}\nInputs: {tool.input_schema}"
```

### 3. Semantic Router

**Domain Service:**
```python
class SemanticRouterService:
    """Semantic Tool Routing"""

    async def route_query(self, query: str, available_tools: list[Tool]) -> list[Tool]:
        """쿼리 → 관련 도구 추출 (Semantic Search)"""

    async def fallback_to_keyword_search(self, query: str, tools: list[Tool]) -> list[Tool]:
        """Vector Search 실패 시 키워드 검색으로 폴백"""
```

**Flow:**
```
사용자 쿼리 → 쿼리 임베딩 → ChromaDB 유사도 검색 → top_k 도구 반환
  ↓ (실패 시)
  키워드 검색 (기존 방식)
```

### 4. Auto Activation

**Configuration Service 확장:**
```python
class ConfigurationService:
    async def check_vector_search_activation(self) -> bool:
        """도구 수가 임계값 초과 시 자동 활성화"""
        tool_count = await self.get_total_tool_count()
        config = await self.get_vector_search_config()

        if tool_count >= config.auto_activation_threshold:
            await self.enable_vector_search()
            return True
        return False
```

**UI 알림 (Playground):**
```
⚡ Vector Search가 자동 활성화되었습니다 (도구 수: 52 > 임계값: 50)
   Settings 탭에서 비활성화할 수 있습니다.
```

---

## Phases (Preliminary)

| Phase | 설명 | Playground | Status |
|-------|------|------------|--------|
| **1** | Domain Entities (VectorSearchConfig, EmbeddingResult) | - | ⏸️ |
| **2** | Port Interface (VectorStorePort, EmbeddingPort) | - | ⏸️ |
| **3** | Domain Services (ToolEmbeddingService, SemanticRouterService) | - | ⏸️ |
| **4** | Adapter Implementation (ChromaDB, OpenAI Embedding) | - | ⏸️ |
| **5** | Integration (DI Container, Auto Activation) | - | ⏸️ |
| **6** | HTTP Routes + Playground UI | ✅ | ⏸️ |
| **7** | E2E Tests + Performance Benchmarks | ✅ | ⏸️ |

**Phase 상세는 Plan 승인 후 작성 예정**

---

## Design Considerations

### Optional Dependency

**설치:**
```bash
# 기본 설치 (Vector Search 없음)
pip install agenthub

# Vector Search 포함 설치
pip install agenthub[vector]  # chromadb, openai 추가
```

**Runtime 체크:**
```python
try:
    import chromadb
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    # Vector Search 비활성화 (키워드 검색으로 폴백)
```

### Performance

**임베딩 캐싱:**
- 도구 설명이 변경되지 않으면 재임베딩 불필요
- 캐시 키: `hash(tool.name + tool.description + tool.input_schema)`

**인덱스 재구축:**
- 도구 추가/삭제 시 자동 재구축
- 백그라운드 작업 (async)

**검색 성능:**
- ChromaDB: ~1ms per query (1000개 도구 기준)
- 임베딩 API: ~50ms per query (OpenAI text-embedding-3-small)

### Fallback Strategy

**Vector Search 실패 시:**
1. 키워드 검색으로 자동 폴백
2. 사용자에게 경고 표시 (Playground)
3. 로그 기록 (디버깅용)

---

## Testing Strategy

### Unit Tests

**Domain:**
- `test_vector_search_config_creation`
- `test_embedding_result_entity`
- `test_semantic_router_fallback`

**Service:**
- `test_tool_embedding_service` (Mock LLM)
- `test_auto_activation_threshold`

### Integration Tests

**Vector Store:**
- `test_chromadb_add_embedding`
- `test_chromadb_search_similar`
- `test_chromadb_persistence` (재시작 후 데이터 유지)

**E2E:**
- `test_semantic_routing_accuracy` (쿼리 → 올바른 도구 매칭)
- `test_auto_activation` (50개 도구 등록 → 자동 활성화)

**Marker:**
- `@pytest.mark.vector` (ChromaDB 필요)

### Performance Benchmarks

**목표:**
- 100개 도구: < 100ms per query
- 1000개 도구: < 500ms per query

**테스트:**
```python
@pytest.mark.vector
@pytest.mark.benchmark
async def test_semantic_search_performance():
    # 1000개 도구 생성 → 임베딩 → 검색 → 시간 측정
    pass
```

---

## Example Usage

### Playground UI (Settings 탭)

**Vector Search 섹션:**
```
[ ] Enable Vector Search (자동 활성화: 도구 50개 이상)

Auto Activation Threshold: [50] 개

Embedding Model: [text-embedding-3-small v]

Top K Results: [5]

Similarity Threshold: [0.7] (0.0 - 1.0)

[ Save Settings ]
```

### API

**검색 엔드포인트:**
```http
POST /api/tools/search
{
  "query": "read a file from disk",
  "use_vector_search": true
}

# Response
{
  "tools": [
    {"name": "filesystem_read", "similarity": 0.95},
    {"name": "file_loader", "similarity": 0.87},
    {"name": "document_reader", "similarity": 0.82}
  ],
  "search_method": "vector"  # or "keyword" (폴백 시)
}
```

---

## Dependencies

**Python Packages:**
- `chromadb` (벡터 DB)
- `openai` (임베딩 API, 기존 의존성)
- 기존: `litellm`, `sqlalchemy`

**Optional:**
- `sentence-transformers` (로컬 임베딩 대안, 추후 고려)

---

## Risks

| 위험 | 심각도 | 대응 |
|------|:------:|------|
| ChromaDB 의존성 크기 (~200MB) | 🟡 | 선택적 의존성 (`pip install agenthub[vector]`) |
| 임베딩 API 비용 | 🟡 | 캐싱 + 변경 시에만 재임베딩 |
| 검색 정확도 저하 | 🟡 | 키워드 검색 폴백 + 유사도 임계값 조정 |
| ChromaDB 버전 호환성 | 🟢 | 버전 고정 + 마이그레이션 가이드 |

---

## Definition of Done

### Functionality
- [ ] ChromaDB 벡터 저장소 동작
- [ ] 도구 임베딩 생성 동작
- [ ] Semantic Search 동작 (쿼리 → 도구 매칭)
- [ ] 자동 활성화 동작 (50개 도구 임계값)
- [ ] 키워드 검색 폴백 동작
- [ ] Playground Settings 탭 동작

### Quality
- [ ] Backend coverage >= 80%
- [ ] Performance 목표 달성 (100개 < 100ms, 1000개 < 500ms)
- [ ] TDD Red-Green-Refactor 사이클 준수

### Documentation
- [ ] `docs/operators/deployment/README.md` 업데이트 (Vector Search 설치)
- [ ] `extension/README.md` 업데이트 (Vector Search 기능)
- [ ] ADR 작성 (ChromaDB 선택, 임베딩 모델 선택)

---

## Related Plans

- **Plan 07**: Hybrid-Dual Architecture (선행 조건 - MCP SDK)
- **Plan 09**: Dynamic Configuration (독립적, 병렬 가능)
- **Plan 10**: stdio Transport (독립적, 병렬 가능)
- **Plan 11**: MCP App UI Rendering (독립적, 병렬 가능)
- **Plan 13**: i18n (독립적, 병렬 가능)

---

*Draft Created: 2026-02-07*
*Reference: _archive/migration/20260204/plans/phase6/backup-20260203/phase6.0-original.md (Step 15)*
*Next: Plan 승인 후 Phase 상세 계획 작성*
