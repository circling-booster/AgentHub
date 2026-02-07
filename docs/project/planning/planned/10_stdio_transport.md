# Plan 10: stdio Transport (Draft)

> **상태:** 📋 Draft
> **선행 조건:** Plan 07 Complete (MCP SDK 통합)
> **목표:** stdio 프로토콜 지원 (subprocess 통신), Cross-platform subprocess 관리

---

## Overview

**핵심 문제:**
- 현재: MCP Streamable HTTP Transport만 지원
- 필요: stdio (stdin/stdout JSON-RPC) 지원으로 더 많은 MCP 서버 지원

**구현 범위:**
1. **StdioConfig Domain Model**: stdio 서버 설정 (command, args, env, cwd)
2. **Subprocess Manager**: 프로세스 라이프사이클 관리 (시작, 모니터링, 재시작, 정리)
3. **stdio Transport**: stdin/stdout JSON-RPC 통신
4. **Cross-platform Support**: Windows/macOS/Linux 동등 지원
5. **Security**: 경로 권한 검증 (allowed_paths)

**참고 문서:**
- 아카이브: `_archive/migration/20260204/plans/phase7/backup-20260203/partB.md` (Step 5-8)

---

## Key Features

### 1. StdioConfig Domain Model

**Domain Entity:**
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

**Endpoint Entity 확장:**
```python
@dataclass
class Endpoint:
    # ... 기존 필드 ...
    transport_type: str  # "http" | "stdio"
    stdio_config: StdioConfig | None = None  # stdio 설정 (transport_type="stdio"일 때)
```

### 2. Subprocess Manager

**Adapter (Outbound):**
```python
class SubprocessManager:
    """프로세스 라이프사이클 관리 (Cross-platform)"""

    async def start_process(self, config: StdioConfig) -> Process:
        """프로세스 시작 (Cross-platform)"""

    async def monitor_process(self, process: Process) -> None:
        """프로세스 모니터링 (크래시 감지 → 재시작)"""

    async def stop_process(self, process: Process) -> None:
        """프로세스 정지 (SIGTERM → SIGKILL)"""

    async def restart_process(self, process: Process) -> Process:
        """프로세스 재시작 (크래시 복구)"""
```

**Cross-platform 고려사항:**
- Windows: `CREATE_NEW_PROCESS_GROUP`, `ctypes` 사용
- macOS/Linux: `os.setpgrp()` 사용
- Path 처리: `pathlib.Path` 사용 (슬래시 정규화)
- Command 이스케이프: `shlex.quote()` (Unix), `subprocess.list2cmdline()` (Windows)

### 3. stdio Transport

**Adapter (Outbound):**
```python
class StdioTransport:
    """stdin/stdout JSON-RPC 통신"""

    async def send_request(self, request: dict) -> dict:
        """JSON-RPC 요청 전송 (stdin)"""

    async def receive_response(self) -> dict:
        """JSON-RPC 응답 수신 (stdout)"""

    async def close(self) -> None:
        """연결 종료"""
```

**JSON-RPC Format:**
```json
// Request (stdin)
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

// Response (stdout)
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
```

### 4. Security: Path Permission Service

**Domain Service:**
```python
class PathPermissionService:
    """경로 권한 검증 (순수 Python)"""

    def validate_path(self, path: str, allowed_paths: list[str]) -> bool:
        """경로가 허용된 경로 내에 있는지 검증"""

    def resolve_path(self, path: str, cwd: str) -> str:
        """상대 경로를 절대 경로로 변환"""
```

---

## Phases (Preliminary)

| Phase | 설명 | Status |
|-------|------|--------|
| **1** | Domain Entities (StdioConfig, Endpoint 확장) | ⏸️ |
| **2** | Port Interface (StdioTransportPort) | ⏸️ |
| **3** | Domain Services (PathPermissionService) | ⏸️ |
| **4** | Adapter Implementation (SubprocessManager, StdioTransport) | ⏸️ |
| **5** | Integration (DI Container, RegistryService 확장) | ⏸️ |
| **6** | Cross-platform CI (Windows/macOS/Linux Matrix) | ⏸️ |

**Phase 상세는 Plan 승인 후 작성 예정**

---

## Architecture

```
AgentHub Backend
  ↓ subprocess spawn (npx, uvx, python, etc.)
MCP Server Process (stdin/stdout JSON-RPC)
  ↑↓ stdin: JSON-RPC request (tools/list, resources/read, etc.)
  ↑↓ stdout: JSON-RPC response
```

**채택:** Option A (외부 MCP 서버 실행)
- AgentHub는 MCP 서버를 subprocess로 실행
- MCP 서버는 독립적인 프로세스로 동작
- 크래시 시 자동 재시작

---

## Design Considerations

### Process Lifecycle

**시작 (Start):**
1. `StdioConfig` 검증 (command, args, allowed_paths)
2. subprocess 생성 (`asyncio.create_subprocess_exec`)
3. stdin/stdout pipe 설정
4. 프로세스 ID 저장 (모니터링용)

**모니터링 (Monitor):**
1. 프로세스 상태 주기적 확인 (5초 간격)
2. 크래시 감지 → 재시작 로직 트리거
3. 최대 재시작 횟수 (`max_restart_attempts`) 도달 시 포기

**정지 (Stop):**
1. SIGTERM 전송 (graceful shutdown)
2. 5초 대기
3. 응답 없으면 SIGKILL 전송 (force kill)
4. 좀비 프로세스 방지 (`wait()` 호출)

**재시작 (Restart):**
1. 기존 프로세스 정지
2. 새 프로세스 시작 (동일 config)
3. stdin/stdout pipe 재설정
4. 재시작 카운터 증가

### Cross-platform Compatibility

**Windows:**
- `CREATE_NEW_PROCESS_GROUP` 플래그 사용
- `ctypes.windll.kernel32.GenerateConsoleCtrlEvent()` (CTRL+C 전송)
- `subprocess.list2cmdline()` (명령어 이스케이프)

**macOS/Linux:**
- `os.setpgrp()` (프로세스 그룹 설정)
- `os.kill(pid, signal.SIGTERM)` (graceful shutdown)
- `shlex.quote()` (명령어 이스케이프)

**CI Matrix:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.11", "3.12"]
```

### Security

**경로 검증:**
- `allowed_paths` 리스트에 있는 경로만 허용
- Symlink 공격 방지 (`os.path.realpath()`)
- 상대 경로 금지 (`.`, `..`)

**환경변수:**
- `env` 딕셔너리로 명시적으로 전달된 환경변수만 사용
- 부모 프로세스의 환경변수 상속 금지 (`env={}` 기본값)

---

## Example Usage

### Playground UI (Future)

**MCP Server Registry 탭:**
```
Transport: [ stdio v ]

Command: [npx                          ]
Args:    [@modelcontextprotocol/server-]
         [filesystem                    ]
         [/path/to/allowed              ]

Allowed Paths:
  [x] /Users/user/Documents
  [ ] /Users/user/Projects
  [+] Add Path

[ Test Connection ] [ Save ]
```

### Configuration (YAML)

```yaml
mcp:
  endpoints:
    - name: "filesystem-server"
      transport_type: "stdio"
      stdio_config:
        command: "npx"
        args:
          - "@modelcontextprotocol/server-filesystem"
          - "/Users/user/Documents"
        env: {}
        cwd: ""
        allowed_paths:
          - "/Users/user/Documents"
          - "/Users/user/Projects"
        restart_on_crash: true
        max_restart_attempts: 3
```

---

## Testing Strategy

### Unit Tests

**Domain:**
- `test_stdio_config_creation`
- `test_endpoint_with_stdio_config`
- `test_path_permission_service`

**Adapter:**
- `test_subprocess_manager_start` (Mock subprocess)
- `test_subprocess_manager_stop`
- `test_subprocess_manager_restart`

### Integration Tests

**stdio Transport (MCP Filesystem Server):**
- `test_stdio_transport_tools_list` (로컬 MCP 서버: `@modelcontextprotocol/server-filesystem`)
- `test_stdio_transport_resources_read` (파일 읽기 검증)
- `test_stdio_crash_recovery` (Kill process → 재시작 검증)
- `test_filesystem_allowed_paths` (경로 권한 검증)

**통합 테스트용 MCP 서버:**
- **Filesystem Server**: `@modelcontextprotocol/server-filesystem` (stdio Transport 대표 사례)
  - 설치: `npm install -g @modelcontextprotocol/server-filesystem`
  - 용도: allowed_paths, subprocess 관리, JSON-RPC 통신 검증

**Marker:**
- `@pytest.mark.local_mcp` (로컬 MCP 서버 필요)

### Cross-platform CI

**GitHub Actions:**
```yaml
- name: Test stdio transport (Windows)
  run: pytest tests/integration/test_stdio_transport.py -m local_mcp -v
  if: matrix.os == 'windows-latest'

- name: Test stdio transport (macOS)
  run: pytest tests/integration/test_stdio_transport.py -m local_mcp -v
  if: matrix.os == 'macos-latest'

- name: Test stdio transport (Linux)
  run: pytest tests/integration/test_stdio_transport.py -m local_mcp -v
  if: matrix.os == 'ubuntu-latest'
```

---

## Risks

| 위험 | 심각도 | 대응 |
|------|:------:|------|
| Windows 프로세스 관리 특수성 | 🟡 | `ctypes` + `CREATE_NEW_PROCESS_GROUP` 활용 |
| subprocess 크로스플랫폼 차이 | 🟡 | `pathlib.Path`, `shlex`/`subprocess.list2cmdline` 분기 |
| 좀비 프로세스 발생 | 🟠 | `wait()` 호출 + 5초 타임아웃 |
| 재시작 루프 (크래시 반복) | 🟡 | `max_restart_attempts` 제한 + 지수 백오프 |
| stdin/stdout 버퍼 오버플로우 | 🟢 | asyncio stream 사용 + 청크 읽기 |

---

## Definition of Done

### Functionality
- [ ] stdio MCP 서버 등록 동작 (Windows/macOS/Linux)
- [ ] 도구 호출 동작 (tools/list, resources/read, etc.)
- [ ] 프로세스 크래시 재시작 동작
- [ ] 좀비 프로세스 방지 검증
- [ ] 경로 권한 검증 동작

### Quality
- [ ] Backend coverage >= 80%
- [ ] Cross-platform CI 통과 (3-OS Matrix)
- [ ] TDD Red-Green-Refactor 사이클 준수

### Documentation
- [ ] `docs/developers/guides/standards/mcp/README.md` 업데이트 (stdio 가이드)
- [ ] `docs/operators/deployment/README.md` 업데이트 (stdio 설정)
- [ ] ADR 작성 (stdio vs HTTP, 크로스플랫폼 전략)

---

## Related Plans

- **Plan 07**: Hybrid-Dual Architecture (선행 조건 - MCP SDK)
- **Plan 09**: Dynamic Configuration (독립적, 병렬 가능)
- **Plan 11**: MCP App UI Rendering (독립적, 병렬 가능)

---

*Draft Created: 2026-02-07*
*Reference: _archive/migration/20260204/plans/phase7/backup-20260203/partB.md*
*Next: Plan 승인 후 Phase 상세 계획 작성*
