# LLM Test Failures Fix Plan - TDD 준수

## 문제 분석

### 발견된 버그 (4개 LLM 테스트 실패)

| # | 에러 | 원인 | 파일 |
|---|------|------|------|
| 1 | `TypeError: unexpected keyword argument 'conversation_id'` | `orchestrator_adapter.py` 파라미터명 `_conversation_id` (언더스코어) | `orchestrator_adapter.py:87` |
| 2 | `ConversationNotFoundError: test-conv-1` | 테스트가 대화 세션 생성 없이 메시지 전송 | `test_chat_routes.py:32` |

### 로드맵과의 불일치 (검증 결과)

| # | 불일치 | Phase 2.0 설계 | 현재 구현 |
|---|--------|---------------|-----------|
| 3 | `ChatRequest.conversation_id` 타입 | `str \| None` (자동 생성 지원) | `str = Field(..., min_length=1)` (필수) |
| 4 | `conversation_created` SSE 이벤트 | Step 7에서 첫 이벤트로 전달 설계 | 미구현 |
| 5 | Conversation CRUD API | Phase 2.5 Extension에서 필요 | **미구현 (어떤 Step에도 없음)** |

---

## TDD 원칙 준수 판단

### 간단한 수정으로 충분한 것
- **버그 1**: `_conversation_id` → `conversation_id` (Port 계약 위반, 즉시 수정)

### TDD Red-Green-Refactor 필요한 것
- **버그 2 + 불일치 3~5**: 대화 생성 API 구현 + ChatRequest 스키마 수정 + 테스트 수정

---

## 구현 순서 (4 Steps)

### Step 1: 파라미터 이름 수정 (즉시)

**파일**: `src/adapters/outbound/adk/orchestrator_adapter.py:84-88`

```python
# 변경 전
async def process_message(
    self,
    message: str,
    _conversation_id: str,  # ← Port 계약 위반
) -> AsyncIterator[str]:

# 변경 후
async def process_message(
    self,
    message: str,
    conversation_id: str,  # ← Port 인터페이스와 일치
) -> AsyncIterator[str]:
```

**검증**: `pytest tests/integration/adapters/test_orchestrator_adapter.py -v`

---

### Step 2: Conversation CRUD API (TDD)

Phase 2.0 설계에 **누락된 기능**입니다. Phase 2.5 Extension의 사이드패널 UI에서 대화 목록/생성이 필수이므로 지금 구현합니다.

#### 2.1 RED: 테스트 먼저 작성

**신규 파일**: `tests/integration/adapters/test_conversation_routes.py`

테스트 케이스:
- `test_create_conversation_with_title` → 201 Created
- `test_create_conversation_without_title` → 201 Created (빈 제목)
- `test_create_conversation_without_auth` → 403 Forbidden

#### 2.2 GREEN: 최소 구현

**신규 파일** (3개):
- `src/adapters/inbound/http/routes/conversations.py` - 라우터
- `src/adapters/inbound/http/schemas/conversations.py` - Pydantic 모델

**수정 파일** (1개):
- `src/adapters/inbound/http/app.py` - 라우터 등록

엔드포인트:
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/conversations` | 대화 생성 (201) |

#### 2.3 REFACTOR

- `routes/__init__.py`에 conversations import 추가 확인
- `app.py`에 `conversations.router` 등록

---

### Step 3: ChatRequest 스키마 수정 + conversation_created 이벤트

Phase 2.0 Step 7 설계에 따라 `conversation_id`를 Optional로 변경합니다.

**수정 파일**:
- `src/adapters/inbound/http/schemas/chat.py`: `conversation_id: str | None = None`
- `src/adapters/inbound/http/routes/chat.py`: `conversation_created` 이벤트 추가

**수정 후 SSE 이벤트 흐름**:
```
conversation_id=None 시:
  data: {"type": "conversation_created", "conversation_id": "uuid..."}\n\n
  data: {"type": "text", "content": "Hello"}\n\n
  data: {"type": "done"}\n\n

conversation_id 지정 시:
  data: {"type": "text", "content": "Hello"}\n\n
  data: {"type": "done"}\n\n
```

**테스트 추가** (`test_chat_routes.py`):
- `test_chat_stream_auto_create_conversation` - conversation_id=None 시 자동 생성 + conversation_created 이벤트
- 기존 `test_chat_stream_invalid_request` 수정 (빈 문자열 → None 허용으로 변경)

---

### Step 4: LLM 테스트 수정

**수정 파일**: `tests/integration/adapters/test_chat_routes.py`

#### test_chat_stream_basic 수정
```python
@pytest.mark.llm
def test_chat_stream_basic(self, authenticated_client, request):
    if not request.config.getoption("--run-llm"):
        pytest.skip("LLM 테스트는 --run-llm 옵션 필요 (비용 발생)")

    # Given: 대화 생성 (전제 조건)
    create_resp = authenticated_client.post(
        "/api/conversations", json={"title": "Test"}
    )
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    # Given: 채팅 요청
    payload = {"conversation_id": conv_id, "message": "Say hello"}

    # When: 스트리밍 채팅
    with authenticated_client.stream("POST", "/api/chat/stream", json=payload) as response:
        # ... 기존 검증 코드
```

#### test_chat_stream_multiple_messages 수정
동일 패턴 적용 (대화 생성 후 메시지 전송)

---

## 수정 대상 파일 전체 목록

### 수정 (4개)
| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | `_conversation_id` → `conversation_id` |
| `src/adapters/inbound/http/schemas/chat.py` | `conversation_id: str \| None = None` |
| `src/adapters/inbound/http/routes/chat.py` | `conversation_created` 이벤트 추가 |
| `src/adapters/inbound/http/app.py` | `conversations.router` 등록 |

### 신규 생성 (3개)
| 파일 | 용도 |
|------|------|
| `src/adapters/inbound/http/routes/conversations.py` | 대화 CRUD 라우터 |
| `src/adapters/inbound/http/schemas/conversations.py` | Pydantic 스키마 |
| `tests/integration/adapters/test_conversation_routes.py` | 대화 API 테스트 |

### 테스트 수정 (2개)
| 파일 | 변경 내용 |
|------|----------|
| `tests/integration/adapters/test_chat_routes.py` | LLM 테스트에 대화 생성 추가 + auto-create 테스트 |
| `tests/integration/adapters/test_chat_routes.py` | `test_chat_stream_invalid_request` 검증 조건 수정 |

---

## 검증 방법

```bash
# 1. Step별 검증
pytest tests/integration/adapters/test_orchestrator_adapter.py -v     # Step 1
pytest tests/integration/adapters/test_conversation_routes.py -v      # Step 2
pytest tests/integration/adapters/test_chat_routes.py -v              # Step 3-4

# 2. 전체 기본 테스트 (regression 확인)
pytest --cov=src --cov-report=html

# 3. LLM 테스트 (API 키 필요, 비용 발생)
pytest -m llm --run-llm -v

# 4. 커버리지 확인 (88% 유지 또는 향상)
```

## 예상 결과

```
# 기본 테스트: 기존 242 + 신규 ~3 = 245+ passed
# LLM 테스트: 4 passed (현재 4 failed → 4 passed)
# 커버리지: 88%+ (conversation routes 추가로 향상 예상)
```

## 로드맵 일관성 체크

| 항목 | Phase 2.0 설계 | 수정 후 | 일관성 |
|------|---------------|---------|:------:|
| `ChatRequest.conversation_id` | `str \| None` | `str \| None = None` | ✅ |
| `conversation_created` SSE 이벤트 | Step 7 설계 | 구현 | ✅ |
| Conversation CRUD | 누락 | `POST /api/conversations` 구현 | ✅ |
| Port 계약 준수 | `conversation_id` | `conversation_id` (언더스코어 제거) | ✅ |
| TDD 원칙 | Red-Green-Refactor | 테스트 먼저 작성 후 구현 | ✅ |
