# AgentHub 구현 가이드

> 핵심 구현 패턴, 권장 사항, 코드 예시

**최종 수정일:** 2026-01-28

---

## 목차

1. [핵심 구현 패턴](#1-핵심-구현-패턴)
2. [DynamicToolset 구현](#2-dynamictoolset-구현)
3. [비동기 초기화 패턴](#3-비동기-초기화-패턴-async-factory)
4. [SQLite 동시성 처리](#4-sqlite-동시성-처리)
5. [SSE 스트리밍](#5-sse-스트리밍)
6. [에러 처리](#6-에러-처리-3-tier)
7. [설정 관리](#7-설정-관리-pydantic-settings)
8. [의존성 주입](#8-의존성-주입)
9. [보안 패턴](#9-보안-패턴)

---

## 1. 핵심 구현 패턴

### ADK Import 구조 (1.23.0+)

```python
# 올바른 import (ADK 1.23.0+ 기준)
from google.adk.agents import LlmAgent
from google.adk.tools import BaseToolset, BaseTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams, SseServerParams
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

### 주요 제약사항

| 제약 | 설명 | 대응 |
|------|------|------|
| **Google 내장 도구** | SearchTool, CodeExecutionTool은 Gemini 전용 | MCP 서버로 대체 |
| **MCPToolset 비동기** | get_tools()가 async | Async Factory 패턴 사용 |
| **Service Worker 타임아웃** | 30초 유휴 시 종료 | Offscreen Document 사용 |

---

## 2. DynamicToolset 구현

### 기본 구현

```python
# src/adapters/outbound/adk/dynamic_toolset.py
"""ADK BaseToolset 기반 동적 도구 관리"""
import asyncio
import time
from typing import Any

from google.adk.tools import BaseToolset, BaseTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams, SseServerParams

from domain.entities.endpoint import Endpoint, EndpointType
from domain.entities.tool import Tool
from domain.exceptions import ToolNotFoundError


# 도구 개수 제한 (Context Explosion 방지)
MAX_ACTIVE_TOOLS = 30
TOOL_TOKEN_WARNING_THRESHOLD = 10000  # 약 10k 토큰


class ToolLimitExceededError(Exception):
    """활성 도구 수가 제한을 초과함"""
    pass


class DynamicToolset(BaseToolset):
    """
    ADK 공식 패턴을 따르는 동적 툴셋

    특징:
    - BaseToolset 상속으로 ADK Agent와 자연스럽게 통합
    - get_tools() 호출 시마다 현재 등록된 모든 도구 반환
    - MCP 서버 추가/제거 시 Agent 재생성 불필요
    - TTL 기반 캐싱으로 성능 최적화
    - 레거시 SSE 서버 폴백 지원
    - 도구 개수 제한으로 Context Explosion 방지
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        super().__init__()
        self._mcp_toolsets: dict[str, MCPToolset] = {}
        self._endpoints: dict[str, Endpoint] = {}

        # 캐싱 관련
        self._cache_ttl = cache_ttl_seconds
        self._tool_cache: dict[str, list[BaseTool]] = {}
        self._cache_timestamps: dict[str, float] = {}
        self._cache_lock = asyncio.Lock()

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """
        현재 등록된 모든 MCP 서버의 도구 반환 (캐싱 적용)

        ADK Agent가 각 turn마다 이 메서드를 호출합니다.
        TTL 기반 캐싱으로 불필요한 MCP 서버 조회를 방지합니다.
        """
        all_tools: list[BaseTool] = []
        current_time = time.time()

        async with self._cache_lock:
            for endpoint_id, toolset in self._mcp_toolsets.items():
                # 캐시 유효성 확인
                if self._is_cache_valid(endpoint_id, current_time):
                    all_tools.extend(self._tool_cache[endpoint_id])
                    continue

                # 캐시 미스: MCP 서버에서 도구 조회
                try:
                    tools = await toolset.get_tools(readonly_context)
                    self._tool_cache[endpoint_id] = tools
                    self._cache_timestamps[endpoint_id] = current_time
                    all_tools.extend(tools)
                except Exception:
                    # 실패 시 기존 캐시 사용 (있으면)
                    if endpoint_id in self._tool_cache:
                        all_tools.extend(self._tool_cache[endpoint_id])
                    continue

        return all_tools

    def _is_cache_valid(self, endpoint_id: str, current_time: float) -> bool:
        """캐시 유효성 확인"""
        if endpoint_id not in self._cache_timestamps:
            return False
        return (current_time - self._cache_timestamps[endpoint_id]) < self._cache_ttl

    def invalidate_cache(self, endpoint_id: str | None = None) -> None:
        """캐시 무효화"""
        if endpoint_id:
            self._tool_cache.pop(endpoint_id, None)
            self._cache_timestamps.pop(endpoint_id, None)
        else:
            self._tool_cache.clear()
            self._cache_timestamps.clear()

    async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]:
        """
        MCP 서버 추가 (Streamable HTTP 우선, SSE 폴백)

        Context Explosion 방지:
        - 활성 도구 수가 MAX_ACTIVE_TOOLS 초과 시 에러
        - 도구 정의 토큰 수 경고 로깅
        """
        if endpoint.type != EndpointType.MCP:
            raise ValueError("Endpoint type must be MCP")

        toolset = await self._create_mcp_toolset(endpoint.url)

        # 연결 테스트 및 도구 목록 조회
        adk_tools = await toolset.get_tools()

        # Context Explosion 방지: 도구 개수 제한
        current_tool_count = sum(len(tools) for tools in self._tool_cache.values())
        total_tools = current_tool_count + len(adk_tools)

        if total_tools > MAX_ACTIVE_TOOLS:
            await toolset.close()
            raise ToolLimitExceededError(
                f"Active tools ({total_tools}) exceed limit ({MAX_ACTIVE_TOOLS}). "
                f"Consider removing unused MCP servers before adding new ones."
            )

        # 토큰 추정 경고 (대략적 계산: 도구당 평균 300토큰 가정)
        estimated_tokens = total_tools * 300
        if estimated_tokens > TOOL_TOKEN_WARNING_THRESHOLD:
            import logging
            logging.warning(
                f"Tool definitions may use ~{estimated_tokens} tokens. "
                f"Consider reducing active tools to avoid context overflow."
            )

        self._mcp_toolsets[endpoint.id] = toolset
        self._endpoints[endpoint.id] = endpoint

        # 캐시 갱신
        self._tool_cache[endpoint.id] = adk_tools
        self._cache_timestamps[endpoint.id] = time.time()

        # 도메인 Tool 엔티티로 변환
        return [
            Tool(
                name=t.name,
                description=t.description or "",
                input_schema=getattr(t, 'input_schema', {}) or {},
                endpoint_id=endpoint.id,
            )
            for t in adk_tools
        ]

    async def _create_mcp_toolset(self, url: str) -> MCPToolset:
        """
        MCP Toolset 생성 (Streamable HTTP 우선, SSE 폴백)

        2025년 3월 이후 Streamable HTTP가 권장 프로토콜이지만,
        레거시 SSE 서버 호환을 위해 폴백 로직 포함
        """
        # 1. Streamable HTTP 시도 (권장)
        try:
            toolset = MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=url,
                    timeout=120,
                ),
            )
            # 연결 테스트
            await toolset.get_tools()
            return toolset
        except Exception:
            pass

        # 2. 레거시 SSE 폴백
        try:
            toolset = MCPToolset(
                connection_params=SseServerParams(
                    url=url,
                    timeout=120,
                ),
            )
            await toolset.get_tools()
            return toolset
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MCP server: {url}") from e

    async def remove_mcp_server(self, endpoint_id: str) -> bool:
        """MCP 서버 제거"""
        if endpoint_id not in self._mcp_toolsets:
            return False

        toolset = self._mcp_toolsets.pop(endpoint_id)
        self._endpoints.pop(endpoint_id, None)
        self.invalidate_cache(endpoint_id)

        await toolset.close()
        return True

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        도구 직접 실행

        비동기 블로킹 방지:
        - 동기식 I/O나 CPU 집약적 도구가 메인 이벤트 루프를 차단하지 않도록
        - asyncio.to_thread로 별도 스레드에서 실행
        """
        for toolset in self._mcp_toolsets.values():
            adk_tools = await toolset.get_tools()
            for tool in adk_tools:
                if tool.name == tool_name:
                    # 블로킹 방지: 스레드 풀에서 실행
                    # 도구가 동기식 라이브러리를 사용하더라도 메인 루프 차단 방지
                    return await asyncio.to_thread(
                        lambda: asyncio.run(tool.run_async(arguments, None))
                    )

        raise ToolNotFoundError(f"Tool not found: {tool_name}")

    async def health_check(self, endpoint_id: str) -> bool:
        """특정 MCP 서버 상태 확인"""
        if endpoint_id not in self._mcp_toolsets:
            return False

        try:
            toolset = self._mcp_toolsets[endpoint_id]
            await toolset.get_tools()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """모든 MCP 연결 정리"""
        for toolset in self._mcp_toolsets.values():
            try:
                await toolset.close()
            except Exception:
                pass
        self._mcp_toolsets.clear()
        self._endpoints.clear()
        self._tool_cache.clear()
        self._cache_timestamps.clear()
```

---

## 3. 비동기 초기화 패턴 (Async Factory)

### 문제

ADK의 `MCPToolset.get_tools()`는 비동기 메서드입니다. DI 컨테이너의 동기 초기화 시점에서 비동기 호출이 불가능하여 경쟁 조건(Race Condition)이 발생할 수 있습니다.

### 해결: Async Factory Pattern

```python
# src/adapters/outbound/adk/orchestrator_adapter.py
"""ADK LlmAgent 기반 오케스트레이터"""
from typing import AsyncIterator

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from domain.ports.outbound.orchestrator_port import OrchestratorPort
from adapters.outbound.adk.dynamic_toolset import DynamicToolset


class AdkOrchestratorAdapter(OrchestratorPort):
    """
    ADK LlmAgent를 사용한 오케스트레이터

    Async Factory Pattern:
    - 생성자에서는 비동기 초기화를 수행하지 않음
    - initialize() 메서드로 명시적 비동기 초기화
    - FastAPI startup 이벤트에서 호출
    """

    def __init__(
        self,
        model: str,
        dynamic_toolset: DynamicToolset,
        instruction: str = "You are a helpful assistant with access to various tools.",
    ):
        self._model_name = model
        self._dynamic_toolset = dynamic_toolset
        self._instruction = instruction
        self._agent: LlmAgent | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        명시적 비동기 초기화

        FastAPI lifespan에서 호출:

        ```python
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            orchestrator = container.orchestrator_adapter()
            await orchestrator.initialize()
            yield
            await orchestrator.close()
        ```
        """
        if self._initialized:
            return

        # 도구 로딩 완료 대기 (비동기)
        await self._dynamic_toolset.get_tools()

        # Agent 생성
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub-agent",
            instruction=self._instruction,
            tools=[self._dynamic_toolset],
        )

        self._initialized = True

    async def process_message(
        self,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[str]:
        """
        메시지 처리 및 스트리밍 응답

        Tool Call Loop는 ADK Agent 내부에서 자동 처리됩니다.
        """
        # 초기화 확인 (Lazy initialization 폴백)
        if not self._initialized:
            await self.initialize()

        agent = self._agent
        if agent is None:
            raise RuntimeError("Orchestrator not initialized")

        async for event in agent.run_async(message):
            if hasattr(event, 'text') and event.text:
                yield event.text

    async def close(self) -> None:
        """리소스 정리"""
        await self._dynamic_toolset.close()
        self._agent = None
        self._initialized = False
```

### FastAPI Startup 통합

```python
# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.container import Container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    container = Container()

    # Startup: 비동기 초기화
    orchestrator = container.orchestrator_adapter()
    await orchestrator.initialize()

    # Health Monitor 시작
    health_monitor = container.health_monitor()
    await health_monitor.start()

    yield

    # Shutdown: 리소스 정리
    await orchestrator.close()
    await health_monitor.stop()


app = FastAPI(
    title="AgentHub API",
    lifespan=lifespan,
)
```

---

## 4. SQLite 동시성 처리

### 문제

SQLite는 파일 기반 DB로, 여러 비동기 작업이 동시에 쓰기를 시도하면 `database is locked` 에러가 발생합니다.

### 해결: WAL 모드 + 싱글톤 연결 + 쓰기 Lock

```python
# src/adapters/outbound/storage/sqlite_storage.py
"""SQLite 기반 대화 저장소 (WAL 모드 + 동시성 처리)"""
import asyncio
from datetime import datetime

import aiosqlite

from domain.entities.conversation import Conversation, Message, MessageRole
from domain.ports.outbound.storage_port import ConversationStoragePort


class SqliteConversationStorage(ConversationStoragePort):
    """
    SQLite 기반 저장소

    동시성 처리:
    - WAL 모드: 읽기와 쓰기가 서로 차단하지 않음
    - 싱글톤 연결: 연결 오버헤드 최소화
    - 쓰기 Lock: 쓰기 작업 직렬화
    - busy_timeout: Lock 대기 시간 설정
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """데이터베이스 초기화 (테이블 생성 + WAL 모드)"""
        if self._initialized:
            return

        conn = await self._get_connection()

        # WAL 모드 활성화 (동시 읽기/쓰기 지원)
        await conn.execute("PRAGMA journal_mode=WAL")

        # busy_timeout 설정 (5초 대기)
        await conn.execute("PRAGMA busy_timeout=5000")

        # 테이블 생성
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS tool_calls (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                server_url TEXT,
                input JSON,
                output JSON,
                duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            );
        """)

        await conn.commit()
        self._initialized = True

    async def _get_connection(self) -> aiosqlite.Connection:
        """싱글톤 연결 반환"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def save_conversation(self, conversation: Conversation) -> None:
        """대화 세션 저장"""
        async with self._write_lock:
            conn = await self._get_connection()
            await conn.execute(
                """INSERT INTO conversations (id, title, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   title = excluded.title,
                   updated_at = excluded.updated_at""",
                (
                    conversation.id,
                    conversation.title,
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                ),
            )
            await conn.commit()

    async def save_message(self, message: Message) -> None:
        """메시지 저장"""
        async with self._write_lock:
            conn = await self._get_connection()
            await conn.execute(
                """INSERT INTO messages (id, conversation_id, role, content, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    message.id,
                    message.conversation_id,
                    message.role.value,
                    message.content,
                    message.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_messages(self, conversation_id: str) -> list[Message]:
        """대화 메시지 조회 (읽기는 Lock 불필요)"""
        conn = await self._get_connection()
        async with conn.execute(
            """SELECT id, conversation_id, role, content, created_at
               FROM messages
               WHERE conversation_id = ?
               ORDER BY created_at""",
            (conversation_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Message(
                    id=row['id'],
                    conversation_id=row['conversation_id'],
                    role=MessageRole(row['role']),
                    content=row['content'],
                    created_at=datetime.fromisoformat(row['created_at']),
                )
                for row in rows
            ]

    async def close(self) -> None:
        """연결 종료"""
        if self._connection:
            await self._connection.close()
            self._connection = None
```

---

## 5. SSE 스트리밍

### 백엔드 (FastAPI)

```python
# src/adapters/inbound/http/routes/chat.py
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide

from domain.services.orchestrator import OrchestratorService
from adapters.inbound.http.schemas.chat import ChatRequest
from config.container import Container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/stream")
@inject
async def chat_stream(
    request: Request,  # FastAPI Request 객체 (연결 상태 확인용)
    body: ChatRequest,
    orchestrator: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
):
    """
    SSE 스트리밍 채팅 (POST)

    이벤트 형식:
    - data: {"type": "text", "content": "..."}\n\n
    - data: {"type": "tool_call", "name": "...", "arguments": {...}}\n\n
    - data: {"type": "done"}\n\n
    - data: {"type": "error", "message": "..."}\n\n

    Zombie Task 방지:
    - 클라이언트 연결 해제 시 즉시 스트림 종료
    - asyncio.CancelledError 명시적 처리
    """
    async def generate():
        try:
            async for chunk in orchestrator.chat(
                body.conversation_id,
                body.message,
            ):
                # 클라이언트 연결 상태 확인 (Zombie Task 방지)
                if await request.is_disconnected():
                    logger.info(f"Client disconnected, stopping stream for conversation {body.conversation_id}")
                    break

                event_data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {event_data}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except asyncio.CancelledError:
            # 연결 해제 시 정리 로직
            logger.info(f"Stream cancelled for conversation {body.conversation_id}")
            # 필요 시 진행 중인 작업 취소
            # await orchestrator.cancel_current_operation()
            raise  # CancelledError는 다시 발생시켜야 함

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"

        finally:
            # 리소스 정리 보장
            logger.debug(f"Stream cleanup for conversation {body.conversation_id}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

---

## 6. 에러 처리 (3-Tier)

### 구조

```
Domain Exception → Application Layer → HTTP Response
   (순수 Python)      (처리/변환)       (API 응답)
```

### 도메인 예외

```python
# src/domain/exceptions.py
"""도메인 예외 (순수 Python, 외부 의존성 없음)"""


class DomainException(Exception):
    """도메인 예외 기본 클래스"""
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


# Endpoint 관련
class EndpointNotFoundError(DomainException):
    """엔드포인트를 찾을 수 없음"""
    pass


class EndpointConnectionError(DomainException):
    """엔드포인트 연결 실패"""
    pass


class EndpointTimeoutError(DomainException):
    """엔드포인트 응답 시간 초과"""
    pass


# Tool 관련
class ToolNotFoundError(DomainException):
    """도구를 찾을 수 없음"""
    pass


class ToolExecutionError(DomainException):
    """도구 실행 실패"""
    pass


# LLM 관련
class LlmRateLimitError(DomainException):
    """LLM API Rate Limit 초과"""
    pass


class LlmAuthenticationError(DomainException):
    """LLM API 인증 실패"""
    pass


# Conversation 관련
class ConversationNotFoundError(DomainException):
    """대화를 찾을 수 없음"""
    pass


# Validation 관련
class InvalidUrlError(DomainException):
    """유효하지 않은 URL"""
    pass
```

### HTTP 예외 핸들러

```python
# src/adapters/inbound/http/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from domain.exceptions import (
    DomainException,
    EndpointNotFoundError,
    EndpointConnectionError,
    EndpointTimeoutError,
    ToolNotFoundError,
    LlmRateLimitError,
    LlmAuthenticationError,
    ConversationNotFoundError,
)


class ErrorResponse(BaseModel):
    error: str
    code: str
    message: str


# 도메인 예외 → HTTP 상태 코드 매핑
EXCEPTION_STATUS_MAP: dict[type[DomainException], int] = {
    EndpointNotFoundError: status.HTTP_404_NOT_FOUND,
    ToolNotFoundError: status.HTTP_404_NOT_FOUND,
    ConversationNotFoundError: status.HTTP_404_NOT_FOUND,
    LlmAuthenticationError: status.HTTP_401_UNAUTHORIZED,
    LlmRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    EndpointConnectionError: status.HTTP_502_BAD_GATEWAY,
    EndpointTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
}


async def domain_exception_handler(request: Request, exc: DomainException):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=type(exc).__name__,
            code=exc.code,
            message=exc.message,
        ).model_dump(),
    )


def register_exception_handlers(app):
    app.add_exception_handler(DomainException, domain_exception_handler)
```

---

## 7. 설정 관리 (pydantic-settings)

```python
# src/config/settings.py
from typing import Tuple, Type
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class ServerSettings(BaseModel):
    host: str = "localhost"
    port: int = 8000


class LLMSettings(BaseModel):
    default_model: str = "anthropic/claude-sonnet-4-20250514"
    timeout: int = 120


class StorageSettings(BaseModel):
    data_dir: str = "./data"
    database: str = "agenthub.db"


class HealthCheckSettings(BaseModel):
    interval_seconds: int = 30
    timeout_seconds: int = 5


class Settings(BaseSettings):
    """
    설정 우선순위: 환경변수 > .env > YAML > 기본값
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        yaml_file="configs/default.yaml",
        extra="ignore",
    )

    server: ServerSettings = ServerSettings()
    llm: LLMSettings = LLMSettings()
    storage: StorageSettings = StorageSettings()
    health_check: HealthCheckSettings = HealthCheckSettings()

    # API 키 (환경변수에서만 로드)
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """YAML 설정 소스 활성화 (필수)"""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
```

---

## 8. 의존성 주입

```python
# src/config/container.py
from dependency_injector import containers, providers

from config.settings import Settings
from adapters.outbound.adk.dynamic_toolset import DynamicToolset
from adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from adapters.outbound.storage.sqlite_storage import SqliteConversationStorage
from adapters.outbound.storage.json_storage import JsonEndpointStorage
from domain.services.orchestrator import OrchestratorService
from domain.services.conversation import ConversationService


class Container(containers.DeclarativeContainer):
    """의존성 주입 컨테이너"""

    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Storage
    endpoint_storage = providers.Singleton(
        JsonEndpointStorage,
        data_dir=config.storage.data_dir,
    )

    conversation_storage = providers.Singleton(
        SqliteConversationStorage,
        db_path=config.storage.database,
    )

    # ADK Components
    dynamic_toolset = providers.Singleton(
        DynamicToolset,
        cache_ttl_seconds=300,
    )

    orchestrator_adapter = providers.Singleton(
        AdkOrchestratorAdapter,
        model=config.llm.default_model,
        dynamic_toolset=dynamic_toolset,
    )

    # Domain Services
    conversation_service = providers.Factory(
        ConversationService,
        orchestrator=orchestrator_adapter,
        storage=conversation_storage,
    )

    orchestrator_service = providers.Factory(
        OrchestratorService,
        conversation_service=conversation_service,
    )
```

---

## 9. 보안 패턴

### 문제: Localhost API 취약점

`localhost:8000` 포트가 열려 있으면, 악성 웹사이트의 JavaScript가 `fetch('http://localhost:8000/api/tools/call')` 호출로 로컬 MCP 도구를 실행할 수 있습니다 (Drive-by RCE Attack).

### 해결: Token Handshake + Strict CORS

#### 1. 서버 측 보안 미들웨어

```python
# src/adapters/inbound/http/security.py
"""Localhost API 보안 (Drive-by RCE 방지)"""
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 서버 시작 시 생성되는 일회성 토큰
EXTENSION_TOKEN: str = secrets.token_urlsafe(32)


class ExtensionAuthMiddleware(BaseHTTPMiddleware):
    """
    Chrome Extension 인증 미들웨어

    모든 /api/* 요청에 X-Extension-Token 헤더 검증
    """

    EXCLUDED_PATHS = {"/health", "/auth/token", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 제외 경로는 검증 생략
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # API 경로는 토큰 검증 필수
        if path.startswith("/api/"):
            token = request.headers.get("X-Extension-Token")
            if token != EXTENSION_TOKEN:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Unauthorized", "message": "Invalid extension token"}
                )

        return await call_next(request)


def get_extension_token() -> str:
    """Extension 초기화 시 토큰 반환 (1회만 호출 가능하도록 제한 권장)"""
    return EXTENSION_TOKEN
```

#### 2. 토큰 교환 엔드포인트

```python
# src/adapters/inbound/http/routes/auth.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from adapters.inbound.http.security import get_extension_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# 토큰 발급 여부 추적
_token_issued = False


class TokenRequest(BaseModel):
    extension_id: str


class TokenResponse(BaseModel):
    token: str


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: Request, body: TokenRequest):
    """
    Extension 초기화 시 토큰 교환

    보안 고려사항:
    - Origin 헤더 검증
    - 토큰 발급 횟수 제한 (서버 재시작 시 리셋)
    """
    global _token_issued

    # Origin 검증
    origin = request.headers.get("Origin", "")
    if not origin.startswith("chrome-extension://"):
        raise HTTPException(status_code=403, detail="Invalid origin")

    # 토큰 재발급 방지 (선택적)
    if _token_issued:
        raise HTTPException(status_code=403, detail="Token already issued")

    _token_issued = True
    return TokenResponse(token=get_extension_token())
```

#### 3. CORS 설정

```python
# src/adapters/inbound/http/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .security import ExtensionAuthMiddleware

app = FastAPI(title="AgentHub API")

# Middleware 순서 (중요 - Starlette LIFO):
# add_middleware()는 내부적으로 insert(0, ...)을 사용하므로
# 나중에 추가된 미들웨어가 outermost(먼저 실행)됩니다.
#
# 원하는 실행 순서: CORS → Auth → Router
# Auth 먼저 추가 (innermost), CORS 나중 추가 (outermost)
app.add_middleware(ExtensionAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["chrome-extension://*"] 는 작동하지 않음!
    # allow_origin_regex 사용 필수
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
)
```

#### 4. Extension 클라이언트

```typescript
// extension/lib/api.ts
const API_BASE = 'http://localhost:8000';

let extensionToken: string | null = null;

/**
 * 서버 시작 후 토큰 교환 (background.ts에서 1회 호출)
 */
export async function initializeAuth(): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extension_id: chrome.runtime.id }),
  });

  if (!response.ok) {
    throw new Error('Failed to authenticate with server');
  }

  const { token } = await response.json();
  extensionToken = token;

  // Session Storage에 저장 (브라우저 종료 시 삭제)
  await chrome.storage.session.set({ extensionToken: token });
}

/**
 * 인증된 API 요청
 */
export async function authenticatedFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  if (!extensionToken) {
    const stored = await chrome.storage.session.get('extensionToken');
    extensionToken = stored.extensionToken;
  }

  if (!extensionToken) {
    throw new Error('Not authenticated');
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'X-Extension-Token': extensionToken,
      'Content-Type': 'application/json',
    },
  });
}
```

### 보안 체크리스트

| 항목 | 설명 | 필수 |
|------|------|:---:|
| **Token Handshake** | 서버 시작 시 난수 토큰 생성, Extension만 교환 | ✅ |
| **CORS Origin 제한** | `chrome-extension://` 도메인만 허용 | ✅ |
| **X-Extension-Token 헤더** | 모든 API 요청에 토큰 포함 | ✅ |
| **Token 재발급 방지** | 서버당 1회만 발급 (선택적) | ⚠️ |
| **Session Storage** | Token을 Local Storage가 아닌 Session Storage에 저장 | ✅ |

---

## 참고 자료

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [MCP Transports Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [pydantic-settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [dependency-injector Documentation](https://python-dependency-injector.ets-labs.org/)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)
- [Chrome Extension Security](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)

---

*문서 생성일: 2026-01-28*
