# Phase 1: Domain Entities

## 개요

SDK Track에 필요한 Domain Entity를 정의합니다. 순수 Python으로 작성하며 외부 라이브러리에 의존하지 않습니다.

**TDD Required:** ✅ 각 엔티티 작성 전 테스트 먼저 작성

---

## Step 1.1: Resource 엔티티

**파일:** `src/domain/entities/resource.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_resource.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_resource.py

from src.domain.entities.resource import Resource, ResourceContent

class TestResource:
    def test_resource_creation_with_required_fields(self):
        """리소스 생성 - 필수 필드"""
        resource = Resource(
            uri="file:///test.txt",
            name="Test File",
        )
        assert resource.uri == "file:///test.txt"
        assert resource.name == "Test File"
        assert resource.description == ""
        assert resource.mime_type == ""

    def test_resource_creation_with_all_fields(self):
        """리소스 생성 - 모든 필드"""
        resource = Resource(
            uri="file:///test.txt",
            name="Test File",
            description="Test description",
            mime_type="text/plain",
        )
        assert resource.mime_type == "text/plain"

class TestResourceContent:
    def test_text_content_creation(self):
        """텍스트 콘텐츠 생성"""
        content = ResourceContent(
            uri="file:///test.txt",
            text="Hello, World!",
            mime_type="text/plain",
        )
        assert content.text == "Hello, World!"
        assert content.blob is None

    def test_blob_content_creation(self):
        """바이너리 콘텐츠 생성"""
        content = ResourceContent(
            uri="file:///image.png",
            blob=b"\x89PNG...",
            mime_type="image/png",
        )
        assert content.blob == b"\x89PNG..."
        assert content.text is None
```

### 구현

```python
# src/domain/entities/resource.py

"""Resource 엔티티

MCP Resource를 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Resource:
    """
    MCP Resource 메타데이터

    MCP 서버가 제공하는 리소스의 메타 정보를 표현합니다.

    Attributes:
        uri: 리소스 URI (file://, http://, custom://)
        name: 리소스 이름
        description: 리소스 설명 (선택)
        mime_type: MIME 타입 (선택)
    """

    uri: str
    name: str
    description: str = ""
    mime_type: str = ""


@dataclass(frozen=True, slots=True)
class ResourceContent:
    """
    MCP Resource 콘텐츠

    리소스의 실제 내용을 표현합니다.
    텍스트 또는 바이너리 중 하나만 가집니다.

    Attributes:
        uri: 리소스 URI
        text: 텍스트 콘텐츠 (text 리소스)
        blob: 바이너리 콘텐츠 (blob 리소스)
        mime_type: MIME 타입
    """

    uri: str
    text: str | None = None
    blob: bytes | None = None
    mime_type: str = ""
```

---

## Step 1.2: PromptTemplate 엔티티

**파일:** `src/domain/entities/prompt_template.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_prompt_template.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_prompt_template.py

from src.domain.entities.prompt_template import PromptArgument, PromptTemplate

class TestPromptArgument:
    def test_required_argument_creation(self):
        """필수 인자 생성"""
        arg = PromptArgument(name="name", required=True, description="User name")
        assert arg.name == "name"
        assert arg.required is True
        assert arg.description == "User name"

    def test_optional_argument_creation(self):
        """선택 인자 생성"""
        arg = PromptArgument(name="age", required=False)
        assert arg.required is False
        assert arg.description == ""

class TestPromptTemplate:
    def test_template_without_arguments(self):
        """인자 없는 템플릿 생성"""
        template = PromptTemplate(
            name="greeting",
            description="Simple greeting",
        )
        assert template.name == "greeting"
        assert template.arguments == []

    def test_template_with_arguments(self):
        """인자 있는 템플릿 생성"""
        args = [
            PromptArgument(name="name", required=True),
            PromptArgument(name="age", required=False),
        ]
        template = PromptTemplate(
            name="user_profile",
            description="User profile prompt",
            arguments=args,
        )
        assert len(template.arguments) == 2
        assert template.arguments[0].name == "name"
```

### 구현

```python
# src/domain/entities/prompt_template.py

"""PromptTemplate 엔티티

MCP Prompt Template을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PromptArgument:
    """
    Prompt 템플릿 인자

    Attributes:
        name: 인자 이름
        required: 필수 여부
        description: 인자 설명
    """

    name: str
    required: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """
    MCP Prompt 템플릿

    MCP 서버가 제공하는 프롬프트 템플릿을 표현합니다.

    Attributes:
        name: 템플릿 이름
        description: 템플릿 설명
        arguments: 템플릿 인자 목록
    """

    name: str
    description: str = ""
    arguments: list[PromptArgument] = field(default_factory=list)
```

---

## Step 1.3: SamplingRequest 엔티티

**파일:** `src/domain/entities/sampling_request.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_sampling_request.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_sampling_request.py

from datetime import datetime, timezone
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus

class TestSamplingRequest:
    def test_create_pending_request(self):
        """대기 중인 요청 생성"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1024,
        )
        assert request.status == SamplingStatus.PENDING
        assert request.llm_result is None
        assert isinstance(request.created_at, datetime)

    def test_create_with_optional_fields(self):
        """선택 필드 포함 생성"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
            model_preferences={"model": "gpt-4"},
            system_prompt="You are helpful",
            max_tokens=2048,
        )
        assert request.model_preferences == {"model": "gpt-4"}
        assert request.system_prompt == "You are helpful"
        assert request.max_tokens == 2048

    def test_datetime_uses_timezone_aware(self):
        """datetime이 timezone-aware인지 확인"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[],
        )
        assert request.created_at.tzinfo is not None

    def test_rejection_reason_defaults_empty(self):
        """거부 사유가 기본값으로 빈 문자열인지 확인"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
        )
        assert request.rejection_reason == ""
```

### 구현

```python
# src/domain/entities/sampling_request.py

"""SamplingRequest 엔티티

MCP Sampling 요청을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SamplingStatus(str, Enum):
    """Sampling 요청 상태"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


@dataclass
class SamplingRequest:
    """
    MCP Sampling 요청

    MCP 서버가 LLM 호출을 요청할 때 사용됩니다.

    Attributes:
        id: 요청 ID
        endpoint_id: MCP 엔드포인트 ID
        messages: LLM 메시지 목록
        model_preferences: 모델 선호도 (선택)
        system_prompt: 시스템 프롬프트 (선택)
        max_tokens: 최대 토큰 수
        status: 요청 상태
        llm_result: LLM 응답 결과 (승인 후)
        rejection_reason: 거부 사유 (거부 시)
        created_at: 생성 시각 (UTC)
    """

    id: str
    endpoint_id: str
    messages: list[dict[str, Any]]
    model_preferences: dict[str, Any] | None = None
    system_prompt: str | None = None
    max_tokens: int = 1024
    status: SamplingStatus = SamplingStatus.PENDING
    llm_result: dict[str, Any] | None = None
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Step 1.4: ElicitationRequest 엔티티

**파일:** `src/domain/entities/elicitation_request.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_elicitation_request.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_elicitation_request.py

from src.domain.entities.elicitation_request import (
    ElicitationAction,
    ElicitationRequest,
    ElicitationStatus,
)

class TestElicitationRequest:
    def test_create_pending_request(self):
        """대기 중인 요청 생성"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={"type": "object", "properties": {"api_key": {"type": "string"}}},
        )
        assert request.status == ElicitationStatus.PENDING
        assert request.action is None
        assert request.content is None

    def test_accept_action(self):
        """accept 액션 설정"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={},
            action=ElicitationAction.ACCEPT,
            content={"api_key": "sk-xxx"},
        )
        assert request.action == ElicitationAction.ACCEPT
        assert request.content == {"api_key": "sk-xxx"}

    def test_decline_action(self):
        """decline 액션 설정"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={},
            action=ElicitationAction.DECLINE,
        )
        assert request.action == ElicitationAction.DECLINE
```

### 구현

```python
# src/domain/entities/elicitation_request.py

"""ElicitationRequest 엔티티

MCP Elicitation 요청을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ElicitationAction(str, Enum):
    """Elicitation 액션"""

    ACCEPT = "accept"
    DECLINE = "decline"
    CANCEL = "cancel"


class ElicitationStatus(str, Enum):
    """Elicitation 요청 상태"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass
class ElicitationRequest:
    """
    MCP Elicitation 요청

    MCP 서버가 사용자 입력을 요청할 때 사용됩니다.

    Attributes:
        id: 요청 ID
        endpoint_id: MCP 엔드포인트 ID
        message: 사용자에게 보여줄 메시지
        requested_schema: JSON Schema (입력 구조)
        action: 사용자 액션 (accept/decline/cancel)
        content: 사용자 입력 내용 (action=accept일 때)
        status: 요청 상태
        created_at: 생성 시각 (UTC)
    """

    id: str
    endpoint_id: str
    message: str
    requested_schema: dict[str, Any]
    action: ElicitationAction | None = None
    content: dict[str, Any] | None = None
    status: ElicitationStatus = ElicitationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Step 1.5: Enums 확인

**파일:** `src/domain/entities/enums.py`

**Note:** SamplingStatus, ElicitationStatus, ElicitationAction은 각 엔티티 파일에 정의되어 있습니다. 기존 `enums.py`에는 MessageRole, EndpointType, EndpointStatus가 있으며 그대로 유지합니다.

---

## Step 1.6: Exceptions 추가

**파일:** `src/domain/exceptions.py` (기존 파일 확장)

### ErrorCode 추가

```python
# src/domain/constants.py의 ErrorCode 클래스에 추가

class ErrorCode:
    # ... 기존 코드 ...

    # HITL 관련 에러
    HITL_TIMEOUT = "HitlTimeoutError"
    HITL_REQUEST_NOT_FOUND = "HitlRequestNotFoundError"

    # Resource/Prompt 관련 에러
    RESOURCE_NOT_FOUND = "ResourceNotFoundError"
    PROMPT_NOT_FOUND = "PromptNotFoundError"
```

### Exception 클래스 추가

```python
# src/domain/exceptions.py에 추가

# ============================================================
# HITL 관련 예외
# ============================================================


class HitlTimeoutError(DomainException):
    """HITL 요청 타임아웃"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.HITL_TIMEOUT)


class HitlRequestNotFoundError(DomainException):
    """HITL 요청을 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.HITL_REQUEST_NOT_FOUND)


# ============================================================
# Resource/Prompt 관련 예외
# ============================================================


class ResourceNotFoundError(DomainException):
    """리소스를 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.RESOURCE_NOT_FOUND)


class PromptNotFoundError(DomainException):
    """프롬프트를 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.PROMPT_NOT_FOUND)
```

### 테스트 시나리오

```python
# tests/unit/domain/test_exceptions.py (기존 파일 확장)

from src.domain.exceptions import (
    HitlTimeoutError,
    HitlRequestNotFoundError,
    ResourceNotFoundError,
    PromptNotFoundError,
)
from src.domain.constants import ErrorCode

class TestHitlExceptions:
    def test_hitl_timeout_error(self):
        """HITL 타임아웃 에러"""
        error = HitlTimeoutError("Request timed out")
        assert error.message == "Request timed out"
        assert error.code == ErrorCode.HITL_TIMEOUT

    def test_hitl_request_not_found_error(self):
        """HITL 요청 미발견 에러"""
        error = HitlRequestNotFoundError("Request not found")
        assert error.code == ErrorCode.HITL_REQUEST_NOT_FOUND

class TestResourceExceptions:
    def test_resource_not_found_error(self):
        """리소스 미발견 에러"""
        error = ResourceNotFoundError("Resource not found")
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND

    def test_prompt_not_found_error(self):
        """프롬프트 미발견 에러"""
        error = PromptNotFoundError("Prompt not found")
        assert error.code == ErrorCode.PROMPT_NOT_FOUND
```

---

## Step 1.7: __init__.py 엔티티 Export (M3 수정)

**파일:** `src/domain/entities/__init__.py`

### 문제

현재 `__init__.py`는 `StreamChunk`만 export합니다. 새로 추가된 엔티티들(Resource, PromptTemplate, SamplingRequest, ElicitationRequest)이 누락되어 있습니다.

### 수정

```python
"""Domain Entities - 비즈니스 개념 모델"""

from .elicitation_request import ElicitationRequest, ElicitationAction, ElicitationStatus
from .prompt_template import PromptTemplate, PromptArgument
from .resource import Resource, ResourceContent
from .sampling_request import SamplingRequest, SamplingStatus
from .stream_chunk import StreamChunk

__all__ = [
    "ElicitationRequest",
    "ElicitationAction",
    "ElicitationStatus",
    "PromptArgument",
    "PromptTemplate",
    "Resource",
    "ResourceContent",
    "SamplingRequest",
    "SamplingStatus",
    "StreamChunk",
]
```

### 테스트

이 Step은 테스트가 필요 없습니다 (import 구조 변경).

---

## Verification

```bash
# 모든 엔티티 테스트
pytest tests/unit/domain/entities/ -v

# 예외 테스트
pytest tests/unit/domain/test_exceptions.py -v
```

---

## Step 1.8: Documentation Update

**목표:** Phase 1에서 추가된 Domain Entity 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | SDK Track 엔티티 섹션 추가 (Resource, PromptTemplate, SamplingRequest, ElicitationRequest) |
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | HITL 엔티티 패턴 설명 (Signal 기반 상태 관리 asyncio.Event) |
| Modify | tests/docs/STRUCTURE.md | Test Documentation | HITL 엔티티 테스트 전략 추가 (TTL, timeout 테스트) |

**주의사항:**
- 엔티티 다이어그램은 포함하지 않음 (코드 우선 접근)
- HITL Signal 패턴은 Phase 3 Service 문서화 시 상세 설명

---

## Checklist

- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 1.1: Resource 엔티티 (TDD)
- [ ] Step 1.2: PromptTemplate 엔티티 (TDD)
- [ ] Step 1.3: SamplingRequest 엔티티 (TDD, datetime.now(timezone.utc) 사용)
- [ ] Step 1.4: ElicitationRequest 엔티티 (TDD)
- [ ] Step 1.5: Enums 확인 (각 엔티티 파일에 정의됨)
- [ ] Step 1.6: Exceptions 추가 (TDD)
- [ ] Step 1.7: __init__.py 엔티티 Export (M3 수정)
- [ ] Step 1.8: Documentation Update (Architecture + Test Docs)
- [ ] 전체 테스트 통과 확인
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`

---

*Last Updated: 2026-02-07*
*Principle: TDD (Red → Green → Refactor), Domain Purity (순수 Python)*
