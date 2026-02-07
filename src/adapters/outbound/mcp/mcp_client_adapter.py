"""MCP Client Adapter

MCP Python SDK를 사용하여 MCP 서버와 통신하는 어댑터입니다.
Streamable HTTP Transport를 사용합니다.
"""

import contextlib
import uuid
from contextlib import AsyncExitStack

from mcp import types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from src.domain.entities.prompt_template import PromptArgument, PromptTemplate
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.exceptions import EndpointNotFoundError
from src.domain.ports.outbound.mcp_client_port import (
    ElicitationCallback,
    McpClientPort,
    SamplingCallback,
)


class McpClientAdapter(McpClientPort):
    """MCP SDK 기반 클라이언트 어댑터

    MCP Python SDK를 사용하여 MCP 서버와 통신합니다.
    Streamable HTTP Transport를 사용합니다.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}
        self._exit_stacks: dict[str, AsyncExitStack] = {}
        self._is_cleaning_up: bool = False  # 중복 disconnect_all() 방지

    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None:
        """MCP 서버에 연결

        Args:
            endpoint_id: 엔드포인트 ID
            url: MCP 서버 URL (Streamable HTTP)
            sampling_callback: Domain 샘플링 콜백 (optional)
            elicitation_callback: Domain Elicitation 콜백 (optional)
        """
        # Domain 콜백 → MCP SDK 콜백 변환
        mcp_sampling_cb = None
        if sampling_callback:
            mcp_sampling_cb = self._wrap_sampling_callback(endpoint_id, sampling_callback)

        mcp_elicitation_cb = None
        if elicitation_callback:
            mcp_elicitation_cb = self._wrap_elicitation_callback(endpoint_id, elicitation_callback)

        # MCP SDK 연결 (AsyncExitStack으로 생명주기 관리)
        exit_stack = AsyncExitStack()
        read, write, _ = await exit_stack.enter_async_context(streamable_http_client(url))
        session = await exit_stack.enter_async_context(
            ClientSession(
                read,
                write,
                sampling_callback=mcp_sampling_cb,
                elicitation_callback=mcp_elicitation_cb,
            )
        )
        await session.initialize()

        self._sessions[endpoint_id] = session
        self._exit_stacks[endpoint_id] = exit_stack

    async def disconnect(self, endpoint_id: str) -> None:
        """세션 정리 (AsyncExitStack 해제)

        Args:
            endpoint_id: 엔드포인트 ID
        """
        if endpoint_id in self._exit_stacks:
            try:
                await self._exit_stacks[endpoint_id].aclose()
            except BaseException:
                # MCP SDK anyio/asyncio 충돌, CancelledError, 네트워크 오류 등 무시
                # BaseException으로 catch하여 asyncio.CancelledError도 처리
                # Teardown 중 발생하는 예외는 세션 정리를 방해하지 않음
                pass
            finally:
                del self._exit_stacks[endpoint_id]
                del self._sessions[endpoint_id]

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)

        Note: 중복 호출을 방지하여 anyio plugin의 fixture teardown과 안전하게 동작
        """
        # 이미 정리 중이거나 완료되었으면 즉시 반환 (idempotent)
        if self._is_cleaning_up or not self._sessions:
            return

        self._is_cleaning_up = True
        try:
            for endpoint_id in list(self._sessions.keys()):
                # anyio cancel scope 충돌, CancelledError 등 무시하고 계속 진행
                with contextlib.suppress(BaseException):
                    await self.disconnect(endpoint_id)
        finally:
            self._is_cleaning_up = False

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """리소스 목록 조회"""
        session = self._get_session(endpoint_id)
        result = await session.list_resources()
        return [
            Resource(
                uri=r.uri,
                name=r.name,
                description=r.description or "",
                mime_type=r.mimeType or "",
            )
            for r in result.resources
        ]

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 콘텐츠 읽기"""
        session = self._get_session(endpoint_id)
        result = await session.read_resource(uri)
        # result.contents[0]이 TextResourceContents 또는 BlobResourceContents
        content = result.contents[0]
        if hasattr(content, "text"):
            return ResourceContent(uri=uri, text=content.text, mime_type=content.mimeType or "")
        else:
            return ResourceContent(uri=uri, blob=content.blob, mime_type=content.mimeType or "")

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """프롬프트 목록 조회"""
        session = self._get_session(endpoint_id)
        result = await session.list_prompts()
        return [
            PromptTemplate(
                name=p.name,
                description=p.description or "",
                arguments=[
                    PromptArgument(
                        name=a.name, required=a.required, description=a.description or ""
                    )
                    for a in (p.arguments or [])
                ],
            )
            for p in result.prompts
        ]

    async def get_prompt(self, endpoint_id: str, name: str, arguments: dict | None) -> str:
        """프롬프트 렌더링"""
        session = self._get_session(endpoint_id)
        result = await session.get_prompt(name, arguments or {})
        # 메시지들을 결합하여 반환
        return "\n".join(
            m.content.text if hasattr(m.content, "text") else str(m.content)
            for m in result.messages
        )

    def _get_session(self, endpoint_id: str) -> ClientSession:
        """세션 조회 (없으면 예외)"""
        if endpoint_id not in self._sessions:
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._sessions[endpoint_id]

    def _wrap_sampling_callback(self, endpoint_id: str, domain_callback: SamplingCallback):
        """Domain 콜백을 MCP SDK SamplingFnT로 래핑

        MCP SDK callback signature:
        async def(context: RequestContext[ClientSession],
                  params: CreateMessageRequestParams)
            -> CreateMessageResult | ErrorData
        """

        async def mcp_callback(
            _context, params: types.CreateMessageRequestParams
        ) -> types.CreateMessageResult | types.ErrorData:
            request_id = str(uuid.uuid4())

            # MCP params → Domain 형식 변환
            messages = [
                {
                    "role": m.role,
                    "content": m.content.text if hasattr(m.content, "text") else str(m.content),
                }
                for m in params.messages
            ]

            try:
                result = await domain_callback(
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    messages=messages,
                    model_preferences=params.modelPreferences,
                    system_prompt=params.systemPrompt,
                    max_tokens=params.maxTokens,
                )

                # Domain 결과 → MCP 형식 변환
                return types.CreateMessageResult(
                    role=result.get("role", "assistant"),
                    content=types.TextContent(type="text", text=result.get("content", "")),
                    model=result.get("model", ""),
                )
            except Exception as e:
                return types.ErrorData(code="SAMPLING_ERROR", message=str(e))

        return mcp_callback

    def _wrap_elicitation_callback(self, endpoint_id: str, domain_callback: ElicitationCallback):
        """Domain 콜백을 MCP SDK ElicitationFnT로 래핑

        MCP SDK callback signature:
        async def(context: RequestContext[ClientSession],
                  params: ElicitRequestParams)
            -> ElicitResult | ErrorData
        """

        async def mcp_callback(
            _context, params: types.ElicitRequestParams
        ) -> types.ElicitResult | types.ErrorData:
            request_id = str(uuid.uuid4())

            try:
                result = await domain_callback(
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    message=params.message,
                    requested_schema=params.requestedSchema or {},
                )

                return types.ElicitResult(
                    action=result.get("action", "accept"),
                    content=result.get("content"),
                )
            except Exception as e:
                return types.ErrorData(code="ELICITATION_ERROR", message=str(e))

        return mcp_callback
