# Phase 1: Domain Entities (TDD)

## 개요

SDK Track에서 사용할 Domain Entity들을 TDD로 구현합니다.

**TDD 순서:**
1. 테스트 파일 먼저 작성 (Red)
2. 최소 구현으로 테스트 통과 (Green)
3. 리팩토링 (Refactor)

---

## Step 1.1: 새 엔티티 생성

| 파일 | 목적 |
|------|------|
| `src/domain/entities/resource.py` | MCP Resource 메타데이터 + ResourceContent |
| `src/domain/entities/prompt_template.py` | Prompt 템플릿 + PromptArgument |
| `src/domain/entities/sampling_request.py` | Sampling HITL 요청 (상태머신) |
| `src/domain/entities/elicitation_request.py` | Elicitation HITL 요청 |

### 테스트 파일 (먼저 작성!)

- `tests/unit/domain/entities/test_resource.py`
- `tests/unit/domain/entities/test_prompt_template.py`
- `tests/unit/domain/entities/test_sampling_request.py`
- `tests/unit/domain/entities/test_elicitation_request.py`

---

### Resource 엔티티

**파일:** `src/domain/entities/resource.py`

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class Resource:
    """MCP Resource 메타데이터

    순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.

    Attributes:
        uri: 리소스 URI (예: "file:///path/to/file.txt")
        name: 사람이 읽을 수 있는 이름
        description: 설명 (선택)
        mime_type: MIME 타입 (선택)
    """
    uri: str
    name: str
    description: str = ""
    mime_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mime_type": self.mime_type,
        }

@dataclass
class ResourceContent:
    """Resource 콘텐츠

    Attributes:
        uri: 리소스 URI
        text: 텍스트 콘텐츠 (text/* MIME)
        blob: 바이너리 콘텐츠 (base64, 다른 MIME)
        mime_type: 콘텐츠 MIME 타입
    """
    uri: str
    text: str | None = None
    blob: str | None = None  # base64 encoded
    mime_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = {"uri": self.uri, "mime_type": self.mime_type}
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            result["blob"] = self.blob
        return result
```

**테스트 시나리오:**
1. `Resource` 생성 - 필수 필드만
2. `Resource` 생성 - 모든 필드
3. `ResourceContent.to_dict()` - text 콘텐츠
4. `ResourceContent.to_dict()` - blob 콘텐츠

---

### SamplingRequest 엔티티 (상태머신)

**파일:** `src/domain/entities/sampling_request.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from src.domain.entities.enums import SamplingStatus

@dataclass
class SamplingRequest:
    """Sampling HITL 요청

    상태 전이: PENDING → APPROVED → COMPLETED
                     └→ REJECTED

    Attributes:
        id: 요청 고유 ID
        endpoint_id: MCP 서버 엔드포인트 ID
        messages: 샘플링할 메시지 목록
        status: 현재 상태
        llm_result: LLM 응답 결과 (승인 후)
        created_at: 생성 시각
    """
    id: str
    endpoint_id: str
    messages: list[dict[str, Any]]
    model_preferences: dict[str, Any] | None = None
    system_prompt: str | None = None
    max_tokens: int = 1000
    status: SamplingStatus = SamplingStatus.PENDING
    llm_result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def approve(self, llm_result: dict[str, Any]) -> None:
        """요청 승인 및 결과 저장"""
        if self.status != SamplingStatus.PENDING:
            raise ValueError(f"Cannot approve request in status {self.status}")
        self.status = SamplingStatus.COMPLETED
        self.llm_result = llm_result

    def reject(self) -> None:
        """요청 거부"""
        if self.status != SamplingStatus.PENDING:
            raise ValueError(f"Cannot reject request in status {self.status}")
        self.status = SamplingStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "messages": self.messages,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }
```

**테스트 시나리오:**
1. 생성 시 기본 상태 PENDING
2. `approve()` - PENDING → COMPLETED, llm_result 저장
3. `reject()` - PENDING → REJECTED
4. 잘못된 상태에서 approve/reject → ValueError

---

## Step 1.2: Enums 추가

**파일:** `src/domain/entities/enums.py` (기존 파일에 추가)

```python
class SamplingStatus(str, Enum):
    """Sampling 요청 상태

    Attributes:
        PENDING: 대기 중 (HITL 승인 필요)
        COMPLETED: 완료 (LLM 응답 완료)
        REJECTED: 거부됨
    """
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ElicitationAction(str, Enum):
    """Elicitation 응답 액션

    Attributes:
        ACCEPT: 요청 수락 (content 제공)
        DECLINE: 요청 거부
        CANCEL: 요청 취소
    """
    ACCEPT = "accept"
    DECLINE = "decline"
    CANCEL = "cancel"

class ElicitationStatus(str, Enum):
    """Elicitation 요청 상태"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
```

---

## Step 1.3: Exceptions 추가

**파일:** `src/domain/exceptions.py` (기존 파일에 추가)

기존 패턴을 따라 ErrorCode와 함께 정의합니다.

먼저 `src/domain/constants.py`에 ErrorCode 추가:

```python
# src/domain/constants.py (기존 파일에 추가)
class ErrorCode:
    # ... 기존 코드 ...

    # MCP SDK Track
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PROMPT_NOT_FOUND = "PROMPT_NOT_FOUND"
    SAMPLING_NOT_FOUND = "SAMPLING_NOT_FOUND"
    ELICITATION_NOT_FOUND = "ELICITATION_NOT_FOUND"
    HITL_TIMEOUT = "HITL_TIMEOUT"
```

```python
# src/domain/exceptions.py (기존 파일에 추가)

# ============================================================
# MCP SDK Track 관련 예외
# ============================================================

class ResourceNotFoundError(DomainException):
    """리소스를 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.RESOURCE_NOT_FOUND)


class PromptNotFoundError(DomainException):
    """프롬프트를 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.PROMPT_NOT_FOUND)


class SamplingNotFoundError(DomainException):
    """Sampling 요청을 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.SAMPLING_NOT_FOUND)


class ElicitationNotFoundError(DomainException):
    """Elicitation 요청을 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.ELICITATION_NOT_FOUND)


class HitlTimeoutError(DomainException):
    """HITL 승인 대기 시간 초과"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.HITL_TIMEOUT)
```

---

## 테스트 실행

```bash
# Phase 1 테스트만 실행
pytest tests/unit/domain/entities/test_resource.py \
       tests/unit/domain/entities/test_prompt_template.py \
       tests/unit/domain/entities/test_sampling_request.py \
       tests/unit/domain/entities/test_elicitation_request.py \
       -v
```
