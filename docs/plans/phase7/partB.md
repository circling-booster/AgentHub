# Phase 7 Part B: stdio Transport (Steps 5-8)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Complete
> **목표:** stdio 프로토콜 지원 (subprocess 통신), 전체 크로스플랫폼 동등 지원
> **예상 테스트:** ~13 신규
> **실행 순서:** Step 5 → Step 6 → Step 7 → Step 8
> **병렬:** Part A, Part D와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **5** | StdioConfig Domain Model | ⬜ |
| **6** | Subprocess Manager (Cross-platform) | ⬜ |
| **7** | stdio MCP Integration | ⬜ |
| **8** | Cross-platform CI | ⬜ |

---

## 아키텍처: stdio Transport

```
AgentHub Backend
  ↓ subprocess spawn (npx, uvx, python, etc.)
MCP Server Process (stdin/stdout JSON-RPC)
  ↑↓ stdin: JSON-RPC request
  ↑↓ stdout: JSON-RPC response
```

**채택:** Option A (외부 MCP 서버 실행)
**크로스플랫폼:** Windows/macOS/Linux 동등 지원 (ADR-8)

---

## Step 5: StdioConfig Domain Model

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/stdio_config.py` | NEW | StdioConfig 엔티티 (순수 Python) |
| `src/domain/entities/endpoint.py` | MODIFY | transport_type 필드 또는 stdio_config 추가 |
| `tests/unit/domain/entities/test_stdio_config.py` | NEW | StdioConfig 테스트 |

**핵심 설계:**
```python
@dataclass
class StdioConfig:
    """stdio MCP 서버 설정 (순수 Python)"""
    command: str  # "npx", "uvx", "python", etc.
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str = ""
    allowed_paths: list[str] = field(default_factory=list)  # 보안: 허용 경로
    restart_on_crash: bool = True
    max_restart_attempts: int = 3
```

**TDD 규칙:** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.

**TDD 순서(SKILLS 호출):**
1. RED: `test_stdio_config_creation`
2. RED: `test_stdio_config_with_allowed_paths`
3. RED: `test_endpoint_with_stdio_config`
4. GREEN: StdioConfig 구현 

**DoD:**
- [ ] StdioConfig 엔티티 정의
- [ ] Endpoint에 stdio 설정 연결
- [ ] 3+ 테스트

---

## Step 6: Subprocess Manager (Cross-platform)

**목표:** 안전한 subprocess 라이프사이클 관리 (시작, 모니터링, 재시작, 정리)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/stdio/__init__.py` | NEW | stdio 어댑터 패키지 |
| `src/adapters/outbound/stdio/subprocess_manager.py` | NEW | 프로세스 라이프사이클 관리 |
| `src/adapters/outbound/stdio/stdio_transport.py` | NEW | stdin/stdout JSON-RPC 통신 |
| `src/domain/services/path_permission_service.py` | NEW | 경로 권한 검증 (순수 Python) |
| `src/config/settings.py` | MODIFY | StdioSettings 추가 |
| `configs/default.yaml` | MODIFY | stdio 기본 설정 |
| `tests/unit/adapters/test_subprocess_manager.py` | NEW | 프로세스 관리 테스트 |
| `tests/integration/adapters/test_stdio_transport.py` | NEW | stdio 통신 테스트 |

**핵심 관심사:**

### 프로세스 라이프사이클
```python
class SubprocessManager:
    async def start(self, config: StdioConfig) -> str:  # process_id
        """프로세스 시작 + PID 추적"""
    async def stop(self, process_id: str) -> None:
        """프로세스 종료 (SIGTERM → SIGKILL)"""
    async def restart(self, process_id: str) -> None:
        """크래시 재시작 (exponential backoff)"""
    async def cleanup_all(self) -> None:
        """AgentHub 종료 시 모든 자식 프로세스 정리"""
    async def health_check(self, process_id: str) -> bool:
        """프로세스 생존 확인"""
```

### 크로스플랫폼 처리
```python
import platform
import subprocess

if platform.system() == "Windows":
    # Windows: CREATE_NEW_PROCESS_GROUP, taskkill
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
else:
    # Unix: os.setsid(), os.killpg()
    preexec_fn = os.setsid
```

### 보안: 경로 권한
```python
class PathPermissionService:
    """허용 경로 검증 (순수 Python)"""
    def __init__(self, allowed_paths: list[str]):
        self._allowed = [Path(p).resolve() for p in allowed_paths]

    def is_allowed(self, path: str) -> bool:
        target = Path(path).resolve()
        return any(target.is_relative_to(allowed) for allowed in self._allowed)
```

### 좀비 프로세스 방지
- PID 파일 기반 추적 (`data/stdio_pids.json`)
- AgentHub 시작 시 이전 세션의 좀비 프로세스 정리
- `atexit` + `signal` 핸들러로 비정상 종료 시에도 정리

**TDD 규칙:** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.

**TDD 순서(SKILLS 호출):**
1. RED: `test_process_starts_and_communicates`
2. RED: `test_process_crash_restart`
3. RED: `test_zombie_prevention_on_cleanup`
4. RED: `test_path_permission_whitelist`
5. RED: `test_cross_platform_paths` (parameterized)
6. RED: `test_resource_limits`
7. GREEN: SubprocessManager, PathPermissionService 구현

**DoD:**
- [ ] subprocess 시작/종료/재시작 동작
- [ ] 크래시 시 exponential backoff 재시작
- [ ] 좀비 프로세스 방지
- [ ] 경로 권한 whitelist 동작
- [ ] Windows/macOS/Linux 동작

---

## Step 7: stdio MCP Integration

**목표:** SubprocessManager를 DynamicToolset에 연결

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | stdio MCPToolset 지원 추가 |
| `src/adapters/inbound/http/routes/mcp.py` | MODIFY | stdio 등록 API 추가 |
| `src/adapters/inbound/http/schemas/mcp.py` | MODIFY | StdioRegistration 스키마 |
| `extension/entrypoints/sidepanel/` | MODIFY | stdio 등록 UI (command, args 입력) |
| `tests/integration/adapters/test_stdio_mcp.py` | NEW | stdio MCP 통합 테스트 |

**웹 검색 필수:** ADK `MCPToolset`의 `StdioServerParameters` 지원 확인

**API 변경:**
```python
# schemas/mcp.py
class RegisterMcpServerRequest(BaseModel):
    url: str = ""  # HTTP URL (기존)
    transport: str = "http"  # "http" | "stdio"
    stdio: StdioConfigSchema | None = None  # stdio 설정

class StdioConfigSchema(BaseModel):
    command: str  # e.g., "npx"
    args: list[str] = []  # e.g., ["-y", "@modelcontextprotocol/server-filesystem"]
    env: dict[str, str] = {}
    allowed_paths: list[str] = []
```

**Extension UI:**
```
[ Transport: HTTP | stdio ▼ ]
[ Command: npx                ]
[ Arguments: -y @mcp/server-fs ]
[ Allowed Paths: + Add Path   ]
[       Register Server        ]
```

**TDD 규칙:** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**DoD:**
- [ ] stdio MCP 서버 등록 + 도구 호출 동작
- [ ] Extension에서 stdio 등록 UI 동작
- [ ] HTTP/stdio 혼합 등록 가능

---

## Step 8: Cross-platform CI

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `.github/workflows/ci-multiplatform.yml` | NEW | 3-OS 매트릭스 CI |

**매트릭스:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.10', '3.12']
```


**TDD 규칙:** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.



**DoD:**
- [ ] 3-OS CI 매트릭스 green
- [ ] stdio 관련 테스트 3-OS 모두 통과

---

## Part B Definition of Done

### 기능
- [ ] stdio MCP 서버 등록 + 도구 호출 (Windows/macOS/Linux)
- [ ] subprocess 크래시 재시작 + 좀비 방지
- [ ] 경로 권한 whitelist
- [ ] Extension stdio 등록 UI

### 품질
- [ ] 13+ 테스트 추가
- [ ] 3-OS CI 매트릭스 통과
- [ ] Coverage >= 90% 유지

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| Windows subprocess 관리 차이 | 🟡 | `CREATE_NEW_PROCESS_GROUP`, `taskkill` |
| npx/uvx 미설치 환경 | 🟡 | 사전 검증 + 에러 메시지 안내 |
| stdio 프로세스 메모리 누수 | 🟡 | 주기적 health check + 메모리 모니터링 |
| CI 3-OS 비용 | 🟢 | 핵심 테스트만 3-OS, 나머지 Linux 전용 |

---

*Part B 계획 작성일: 2026-01-31*
