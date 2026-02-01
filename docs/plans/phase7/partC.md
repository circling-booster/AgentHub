# Phase 7 Part C: MCP Required Features (Steps 9-12)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Part B (McpClientPort)
> **목표:** MCP 필수 기능 (Roots, Progress, Tasks, Registry) 구현
> **예상 테스트:** ~13 신규
> **실행 순서:** Step 9 → Step 10 → Step 11 → Step 12

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **9** | Roots (Filesystem Scoping) | ⬜ |
| **10** | Progress Notifications | ⬜ |
| **11** | Tasks (Long-Running Operations) | ⬜ |
| **12** | MCP Registry Integration | ⬜ |

---

## Step 9: Roots (Filesystem Scoping)

**스펙:** MCP 2025-06-18 공식 스펙

**목표:** MCP Client(AgentHub)가 서버에 filesystem roots를 선언

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/root.py` | NEW | Root 엔티티 (uri, name) |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | MODIFY | 초기화 시 roots 전송 |
| `src/config/settings.py` | MODIFY | RootsSettings (default roots) |
| `configs/default.yaml` | MODIFY | roots 기본 설정 |
| `tests/unit/domain/entities/test_root.py` | NEW | Root 엔티티 테스트 |

**핵심 설계:**
```python
@dataclass
class Root:
    uri: str  # "file:///path/to/workspace"
    name: str = ""

# settings.yaml
roots:
  - uri: "file:///Users/user/workspace"
    name: "workspace"
```

**TDD 규칙(SKILLS 호출):** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.



**DoD:**
- [ ] MCP 서버 연결 시 roots 전달
- [ ] 설정에서 roots 관리 가능

---

## Step 10: Progress Notifications

**스펙:** MCP 2025-03-26 Progress 유틸리티

**목표:** MCP 서버의 장시간 작업 진행률을 Extension에 표시

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/progress.py` | NEW | Progress 엔티티 |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | MODIFY | progress 알림 핸들러 |
| `src/adapters/inbound/http/routes/chat.py` | MODIFY | SSE로 progress 이벤트 스트림 |
| `extension/components/ProgressIndicator.tsx` | NEW | 진행률 바 |
| `tests/unit/domain/entities/test_progress.py` | NEW | Progress 테스트 |

**핵심 설계:**
```python
@dataclass
class Progress:
    token: str
    progress: float  # 0.0 ~ 1.0
    total: float | None = None
    message: str = ""
```

**SSE 이벤트:**
```json
{"type": "progress", "token": "xxx", "progress": 0.5, "message": "Processing..."}
```

**TDD 규칙(SKILLS 호출):** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.



**DoD:**
- [ ] MCP 서버 progress 알림을 SSE로 전달
- [ ] Extension에 진행률 바 표시

---

## Step 11: Tasks (Long-Running Operations)

**스펙:** MCP 2025-11-25 Task 프리미티브

**목표:** 장시간 작업의 취소/재개 지원

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/mcp_task.py` | NEW | McpTask 엔티티 (id, status, progress) |
| `src/adapters/inbound/http/routes/tasks.py` | NEW | Task 관리 API |
| `extension/components/TaskManager.tsx` | NEW | Task 목록 + 취소/재개 UI |
| `tests/unit/domain/entities/test_mcp_task.py` | NEW | McpTask 테스트 |

**API:**
- `GET /api/tasks` - 실행 중인 Tasks 목록
- `POST /api/tasks/{id}/cancel` - Task 취소
- `POST /api/tasks/{id}/resume` - Task 재개

**TDD 규칙(SKILLS 호출):** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**DoD:**
- [ ] 장시간 작업 Task ID로 추적 가능
- [ ] 취소/재개 동작
- [ ] Extension에서 Task 관리 UI

---

## Step 12: MCP Registry Integration

**동향:** GitHub MCP Registry (2025년 말 출시)

**목표:** MCP 서버 레지스트리에서 서버 검색/설치

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/ports/outbound/registry_discovery_port.py` | NEW | RegistryDiscoveryPort |
| `src/adapters/outbound/mcp/registry_adapter.py` | NEW | GitHub MCP Registry 클라이언트 |
| `extension/components/ServerDiscovery.tsx` | NEW | 서버 검색 UI |
| `tests/integration/adapters/test_registry_discovery.py` | NEW | Registry 통합 테스트 |

**핵심 설계:**
```python
class RegistryDiscoveryPort(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[RegistryEntry]: ...
    @abstractmethod
    async def get_server_info(self, server_id: str) -> ServerInfo: ...
    @abstractmethod
    async def get_install_command(self, server_id: str) -> StdioConfig: ...
```

**Extension UI:**
- "Browse Registry" 버튼 → 검색 모달
- 서버 카드: 이름, 설명, 설치 버튼
- 원클릭 설치 (stdio 자동 설정)

**웹 검색 필수:** GitHub MCP Registry API 확인

**TDD 규칙(SKILLS 호출):** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**DoD:**
- [ ] Registry에서 MCP 서버 검색
- [ ] 검색 결과에서 원클릭 등록
- [ ] Extension 검색 UI 동작

---

## Part C Definition of Done

### 기능
- [ ] MCP Roots: 서버에 filesystem roots 전달
- [ ] Progress Notifications: 진행률 UI 표시
- [ ] Tasks: 취소/재개 동작
- [ ] Registry: 서버 검색 + 원클릭 등록

### 품질
- [ ] 13+ 테스트 추가
- [ ] Coverage >= 90% 유지

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| MCP Registry API 변경/미공개 | 🟡 | 웹 검색, 변경 시 어댑터만 수정 |
| Tasks 스펙 안정성 | 🟡 | 2025-11-25 스펙 기준 구현, 변경 추적 |
| Progress 이벤트 빈도 과다 | 🟢 | throttling (초당 최대 N회) |

---

*Part C 계획 작성일: 2026-01-31*
