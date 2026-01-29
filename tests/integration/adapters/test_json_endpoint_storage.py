"""JsonEndpointStorage Integration Tests

TDD Phase: RED - 테스트 먼저 작성
"""

import asyncio
import json

import pytest

from src.adapters.outbound.storage.json_endpoint_storage import JsonEndpointStorage
from src.domain.entities.endpoint import Endpoint, EndpointStatus, EndpointType


@pytest.fixture
async def storage(tmp_path):
    """임시 디렉토리를 사용하는 JsonEndpointStorage"""
    storage = JsonEndpointStorage(data_dir=str(tmp_path))
    await storage.initialize()
    yield storage
    await storage.close()


@pytest.fixture
def sample_endpoint():
    """테스트용 MCP 엔드포인트"""
    return Endpoint(
        url="http://localhost:9000/mcp",
        type=EndpointType.MCP,
        name="Test MCP Server",
    )


class TestJsonEndpointStorageBasics:
    """기본 CRUD 동작 검증"""

    async def test_initialize_creates_data_dir(self, tmp_path):
        """initialize 시 data_dir 생성"""
        data_dir = tmp_path / "test_data"
        storage = JsonEndpointStorage(data_dir=str(data_dir))

        await storage.initialize()

        assert data_dir.exists()
        await storage.close()

    async def test_initialize_creates_endpoints_file(self, tmp_path):
        """initialize 시 endpoints.json 생성"""
        storage = JsonEndpointStorage(data_dir=str(tmp_path))

        await storage.initialize()

        endpoints_file = tmp_path / "endpoints.json"
        assert endpoints_file.exists()
        await storage.close()

    async def test_save_and_get_endpoint(self, storage, sample_endpoint):
        """엔드포인트 저장 및 조회"""
        # Given: 엔드포인트 저장
        await storage.save_endpoint(sample_endpoint)

        # When: 조회
        retrieved = await storage.get_endpoint(sample_endpoint.id)

        # Then: 동일한 엔드포인트 반환
        assert retrieved is not None
        assert retrieved.id == sample_endpoint.id
        assert retrieved.url == sample_endpoint.url
        assert retrieved.name == sample_endpoint.name
        assert retrieved.type == sample_endpoint.type

    async def test_get_nonexistent_endpoint(self, storage):
        """존재하지 않는 엔드포인트 조회 시 None"""
        # When: 없는 ID로 조회
        result = await storage.get_endpoint("nonexistent-id")

        # Then: None 반환
        assert result is None

    async def test_update_endpoint(self, storage, sample_endpoint):
        """엔드포인트 업데이트"""
        # Given: 엔드포인트 저장
        await storage.save_endpoint(sample_endpoint)

        # When: update_endpoint_status로 상태 변경
        result = await storage.update_endpoint_status(
            sample_endpoint.id, EndpointStatus.CONNECTED.value
        )

        # Then: 성공, 변경된 상태로 조회됨
        assert result is True
        retrieved = await storage.get_endpoint(sample_endpoint.id)
        assert retrieved.status == EndpointStatus.CONNECTED

    async def test_delete_endpoint(self, storage, sample_endpoint):
        """엔드포인트 삭제"""
        # Given: 엔드포인트 저장
        await storage.save_endpoint(sample_endpoint)

        # When: 삭제
        result = await storage.delete_endpoint(sample_endpoint.id)

        # Then: 삭제 성공, 조회 시 None
        assert result is True
        assert await storage.get_endpoint(sample_endpoint.id) is None

    async def test_delete_nonexistent_endpoint(self, storage):
        """존재하지 않는 엔드포인트 삭제 시 False"""
        # When: 없는 ID로 삭제
        result = await storage.delete_endpoint("nonexistent-id")

        # Then: False 반환
        assert result is False


class TestJsonEndpointStorageList:
    """목록 조회 기능 검증"""

    async def test_list_endpoints_empty(self, storage):
        """빈 목록 조회"""
        # When: 엔드포인트 없이 조회
        endpoints = await storage.list_endpoints()

        # Then: 빈 리스트
        assert endpoints == []

    async def test_list_endpoints_multiple(self, storage):
        """여러 엔드포인트 조회"""
        # Given: 3개 엔드포인트 저장
        ep1 = Endpoint(url="http://localhost:9000/mcp", type=EndpointType.MCP)
        ep2 = Endpoint(url="http://localhost:9001/mcp", type=EndpointType.MCP)
        ep3 = Endpoint(url="http://localhost:9002/a2a", type=EndpointType.A2A)

        await storage.save_endpoint(ep1)
        await storage.save_endpoint(ep2)
        await storage.save_endpoint(ep3)

        # When: 전체 조회
        endpoints = await storage.list_endpoints()

        # Then: 3개 반환
        assert len(endpoints) == 3

    async def test_list_endpoints_with_type_filter(self, storage):
        """타입 필터링"""
        # Given: MCP 2개, A2A 1개 저장
        ep1 = Endpoint(url="http://localhost:9000/mcp", type=EndpointType.MCP)
        ep2 = Endpoint(url="http://localhost:9001/mcp", type=EndpointType.MCP)
        ep3 = Endpoint(url="http://localhost:9002/a2a", type=EndpointType.A2A)

        await storage.save_endpoint(ep1)
        await storage.save_endpoint(ep2)
        await storage.save_endpoint(ep3)

        # When: MCP만 조회
        mcp_endpoints = await storage.list_endpoints(type_filter="mcp")

        # Then: 2개만 반환
        assert len(mcp_endpoints) == 2
        assert all(ep.type == EndpointType.MCP for ep in mcp_endpoints)


class TestJsonEndpointStorageStatus:
    """상태 갱신 기능 검증"""

    async def test_update_endpoint_status(self, storage, sample_endpoint):
        """엔드포인트 상태 갱신"""
        # Given: 엔드포인트 저장
        await storage.save_endpoint(sample_endpoint)

        # When: 상태 갱신
        result = await storage.update_endpoint_status(
            sample_endpoint.id, EndpointStatus.CONNECTED.value
        )

        # Then: 성공, 변경된 상태로 조회됨
        assert result is True
        retrieved = await storage.get_endpoint(sample_endpoint.id)
        assert retrieved.status == EndpointStatus.CONNECTED

    async def test_update_nonexistent_endpoint_status(self, storage):
        """존재하지 않는 엔드포인트 상태 갱신 시 False"""
        # When: 없는 ID로 상태 갱신
        result = await storage.update_endpoint_status(
            "nonexistent-id", EndpointStatus.CONNECTED.value
        )

        # Then: False 반환
        assert result is False


class TestJsonEndpointStorageConcurrency:
    """동시성 처리 검증"""

    async def test_concurrent_writes(self, storage):
        """동시 쓰기 작업 처리"""
        # Given: 10개 엔드포인트 동시 저장
        endpoints = [
            Endpoint(url=f"http://localhost:{9000 + i}/mcp", type=EndpointType.MCP)
            for i in range(10)
        ]

        # When: 동시 저장
        await asyncio.gather(*[storage.save_endpoint(ep) for ep in endpoints])

        # Then: 모두 저장됨
        all_endpoints = await storage.list_endpoints()
        assert len(all_endpoints) == 10

    async def test_concurrent_read_write(self, storage, sample_endpoint):
        """동시 읽기/쓰기 작업"""
        # Given: 엔드포인트 저장
        await storage.save_endpoint(sample_endpoint)

        # When: 동시에 읽기 10회, 쓰기 5회
        read_tasks = [storage.get_endpoint(sample_endpoint.id) for _ in range(10)]
        write_tasks = [
            storage.update_endpoint_status(sample_endpoint.id, EndpointStatus.CONNECTED.value)
            for _ in range(5)
        ]

        results = await asyncio.gather(*read_tasks, *write_tasks)

        # Then: 모든 작업 성공
        assert all(r is not None for r in results[:10])  # 읽기 결과
        assert all(r is True for r in results[10:])  # 쓰기 결과


class TestJsonEndpointStoragePersistence:
    """영속성 검증"""

    async def test_data_persists_across_instances(self, tmp_path, sample_endpoint):
        """인스턴스 간 데이터 영속성"""
        # Given: 첫 번째 인스턴스로 저장
        storage1 = JsonEndpointStorage(data_dir=str(tmp_path))
        await storage1.initialize()
        await storage1.save_endpoint(sample_endpoint)
        await storage1.close()

        # When: 두 번째 인스턴스로 조회
        storage2 = JsonEndpointStorage(data_dir=str(tmp_path))
        await storage2.initialize()
        retrieved = await storage2.get_endpoint(sample_endpoint.id)
        await storage2.close()

        # Then: 동일한 엔드포인트
        assert retrieved is not None
        assert retrieved.id == sample_endpoint.id
        assert retrieved.url == sample_endpoint.url

    async def test_json_file_format(self, tmp_path, sample_endpoint):
        """JSON 파일 형식 검증"""
        # Given: 엔드포인트 저장
        storage = JsonEndpointStorage(data_dir=str(tmp_path))
        await storage.initialize()
        await storage.save_endpoint(sample_endpoint)
        await storage.close()

        # When: JSON 파일 직접 읽기
        json_file = tmp_path / "endpoints.json"
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        # Then: 예상된 구조
        assert isinstance(data, dict)
        assert sample_endpoint.id in data
        endpoint_data = data[sample_endpoint.id]
        assert endpoint_data["url"] == sample_endpoint.url
        assert endpoint_data["type"] == sample_endpoint.type.value
        assert "registered_at" in endpoint_data
