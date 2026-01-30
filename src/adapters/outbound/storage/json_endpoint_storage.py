"""JsonEndpointStorage - JSON 파일 기반 엔드포인트 저장소

TDD Phase: GREEN - 최소 구현
"""

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

from src.domain.entities.endpoint import EndpointStatus, EndpointType
from src.domain.ports.outbound.storage_port import EndpointStoragePort

if TYPE_CHECKING:
    from src.domain.entities.endpoint import Endpoint


class JsonEndpointStorage(EndpointStoragePort):
    """
    JSON 파일 기반 엔드포인트 저장소

    특징:
    - {data_dir}/endpoints.json에 저장
    - asyncio.to_thread로 동기 파일 I/O 래핑
    - asyncio.Lock으로 쓰기 직렬화
    - datetime → ISO format, enum → .value 직렬화
    """

    def __init__(self, data_dir: str):
        """
        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self._data_dir = Path(data_dir)
        self._json_file = self._data_dir / "endpoints.json"
        self._write_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """데이터 디렉토리 및 JSON 파일 생성"""
        await asyncio.to_thread(self._data_dir.mkdir, parents=True, exist_ok=True)

        if not await asyncio.to_thread(self._json_file.exists):
            await self._write_json({})

    async def close(self) -> None:
        """리소스 정리 (JSON 저장소는 특별한 정리 불필요)"""
        pass

    async def save_endpoint(self, endpoint: "Endpoint") -> None:
        """엔드포인트 저장/갱신"""
        async with self._write_lock:
            data = await self._read_json()
            data[endpoint.id] = self._serialize_endpoint(endpoint)
            await self._write_json(data)

    async def get_endpoint(self, endpoint_id: str) -> "Endpoint | None":
        """엔드포인트 조회"""
        data = await self._read_json()
        endpoint_data = data.get(endpoint_id)

        if endpoint_data is None:
            return None

        return self._deserialize_endpoint(endpoint_data)

    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list["Endpoint"]:
        """엔드포인트 목록 조회"""
        data = await self._read_json()
        endpoints = [self._deserialize_endpoint(ep_data) for ep_data in data.values()]

        if type_filter:
            # type_filter를 EndpointType enum으로 변환
            filter_type = EndpointType(type_filter.lower())
            endpoints = [ep for ep in endpoints if ep.type == filter_type]

        return endpoints

    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """엔드포인트 삭제"""
        async with self._write_lock:
            data = await self._read_json()

            if endpoint_id not in data:
                return False

            del data[endpoint_id]
            await self._write_json(data)
            return True

    async def update_endpoint_status(
        self,
        endpoint_id: str,
        status: str,
    ) -> bool:
        """엔드포인트 상태 갱신"""
        async with self._write_lock:
            data = await self._read_json()

            if endpoint_id not in data:
                return False

            data[endpoint_id]["status"] = status
            await self._write_json(data)
            return True

    async def _read_json(self) -> dict:
        """JSON 파일 읽기 (비동기 래핑)"""

        def _read():
            if not self._json_file.exists():
                return {}
            with open(self._json_file, encoding="utf-8") as f:
                return json.load(f)

        return await asyncio.to_thread(_read)

    async def _write_json(self, data: dict) -> None:
        """JSON 파일 쓰기 (비동기 래핑)"""

        def _write():
            with open(self._json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        await asyncio.to_thread(_write)

    def _serialize_endpoint(self, endpoint: "Endpoint") -> dict:
        """Endpoint → dict 직렬화"""
        return {
            "id": endpoint.id,
            "url": endpoint.url,
            "type": endpoint.type.value,  # enum → str
            "name": endpoint.name,
            "enabled": endpoint.enabled,
            "status": endpoint.status.value,  # enum → str
            "registered_at": endpoint.registered_at.isoformat(),  # datetime → ISO str
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "endpoint_id": tool.endpoint_id,
                }
                for tool in endpoint.tools
            ],
            "agent_card": endpoint.agent_card,  # dict | None → JSON 호환
        }

    def _deserialize_endpoint(self, data: dict) -> "Endpoint":
        """dict → Endpoint 역직렬화"""
        from datetime import datetime

        from src.domain.entities.endpoint import Endpoint
        from src.domain.entities.tool import Tool

        # Tools 역직렬화
        tools = [
            Tool(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data["input_schema"],
                endpoint_id=tool_data["endpoint_id"],
            )
            for tool_data in data.get("tools", [])
        ]

        # Endpoint 생성 (status 포함)
        endpoint = Endpoint(
            id=data["id"],
            url=data["url"],
            type=EndpointType(data["type"]),  # str → enum
            name=data["name"],
            enabled=data["enabled"],
            status=EndpointStatus(data["status"]),  # str → enum
            registered_at=datetime.fromisoformat(data["registered_at"]),  # ISO str → datetime
            tools=tools,
            agent_card=data.get("agent_card"),  # 기존 데이터 하위 호환 (None default)
        )

        return endpoint
