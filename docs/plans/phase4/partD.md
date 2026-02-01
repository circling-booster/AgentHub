# Phase 4 Part D: Reliability & Scale (Steps 10-11)

> **상태:** ✅ Complete
> **완료 일자:** 2026-01-31
> **선행 조건:** Part A Complete
> **목표:** A2A Health 모니터링, 대규모 도구 Defer Loading
> **예상 테스트:** ~7 신규 (backend)
> **Phase 4 최종 Part:** 완료 시 전체 문서 업데이트

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **10** | A2A Agent Health Monitoring | ✅ |
| **11** | Defer Loading (Large-Scale Tools) | ✅ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part D Prerequisites

- [ ] Part A 완료 (Step 1: A2A wiring 필요)
- [ ] 기존 테스트 전체 통과

**⚡ 병렬화 옵션:** Part A 완료 후 Part B, C와 병렬 진행 가능

---

## Step 10: A2A Agent Health Monitoring

**문제:** `health_monitor_service.py`의 `check_endpoint_health()`가 MCP만 지원. A2A 타입 분기 없음.

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/health_monitor_service.py` | MODIFY | A2A 타입 엔드포인트 health check 추가. 타입별 분기 (MCP: toolset.health_check, A2A: a2a_client.health_check) |
| `src/domain/ports/outbound/a2a_port.py` | MODIFY | `health_check(endpoint_id)` 메서드 추가 |
| `src/adapters/outbound/a2a/a2a_client_adapter.py` | MODIFY | Agent Card URL GET으로 health check 구현 |
| `tests/unit/fakes/fake_a2a_client.py` | MODIFY | `health_check()` 구현 |
| `tests/unit/domain/services/test_health_monitor.py` | MODIFY | A2A health check 테스트 |

**핵심 설계:**
```python
# health_monitor_service.py 수정
async def check_endpoint_health(self, endpoint_id: str) -> bool:
    endpoint = await self._storage.get_endpoint(endpoint_id)
    if not endpoint:
        return False

    if endpoint.type == EndpointType.MCP:
        return await self._toolset.health_check(endpoint_id)
    elif endpoint.type == EndpointType.A2A:
        if self._a2a_client:
            return await self._a2a_client.health_check(endpoint_id)
        return False

# a2a_client_adapter.py 추가
async def health_check(self, endpoint_id: str) -> bool:
    """Agent Card URL GET으로 health check"""
    agent = self._agents.get(endpoint_id)
    if not agent:
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(agent.card_url, timeout=5)
            return resp.status_code == 200
    except Exception:
        return False
```

**TDD 순서:**
1. RED: `test_health_check_a2a_agent_healthy`
2. RED: `test_health_check_a2a_agent_unhealthy`
3. RED: `test_health_monitor_checks_both_types`
4. GREEN: health_monitor_service, a2a_port, a2a_client_adapter 수정

**DoD:**
- [ ] A2A 에이전트 주기적 health check 동작
- [ ] 비정상 A2A 에이전트 로깅
- [ ] MCP/A2A 모두 health check API 동작
- [ ] 신규 테스트 3개 이상

**의존성:** Part A Step 1 (A2A 연결)

---

## Step 11: Defer Loading (Large-Scale Tools)

**목표:** 도구 50개 초과 시 메타데이터만 로드, 실행 시 풀 스키마 lazy load

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | `MAX_ACTIVE_TOOLS` 100으로 증가. threshold 초과 시 `DeferredToolProxy` 래퍼로 메타데이터만 로드 |
| `src/config/settings.py` | MODIFY | `mcp.defer_loading_threshold` 설정 추가 (기본 30) |
| `configs/default.yaml` | MODIFY | defer_loading_threshold 기본값 |
| `tests/unit/adapters/test_defer_loading.py` | **NEW** | Defer loading 동작 테스트 |

**핵심 설계:**
```python
# dynamic_toolset.py 추가
class DeferredToolProxy:
    """메타데이터만 로드된 도구 프록시. 실행 시 풀 스키마 lazy load."""
    def __init__(self, name: str, description: str, endpoint_id: str, toolset: MCPToolset):
        self.name = name
        self.description = description
        self._endpoint_id = endpoint_id
        self._toolset = toolset
        self._full_tool = None  # lazy

    async def run_async(self, arguments, context):
        if self._full_tool is None:
            tools = await self._toolset.get_tools()
            self._full_tool = next(t for t in tools if t.name == self.name)
        return await self._full_tool.run_async(arguments, context)

# get_tools() 수정
async def get_tools(self, readonly_context=None) -> list[BaseTool]:
    all_tools = []
    total_count = sum(len(t) for t in self._tool_cache.values())

    if total_count > self._defer_threshold:
        # Defer mode: 메타데이터만 반환
        for endpoint_id, tools in self._tool_cache.items():
            for tool in tools:
                all_tools.append(DeferredToolProxy(
                    name=tool.name,
                    description=tool.description,
                    endpoint_id=endpoint_id,
                    toolset=self._mcp_toolsets[endpoint_id],
                ))
    else:
        # Normal mode: 풀 도구 반환
        # ... 기존 로직 ...
    return all_tools
```

**TDD 순서:**
1. RED: `test_defer_loading_activates_above_threshold`
2. RED: `test_deferred_tool_lazy_loads_on_execution`
3. RED: `test_normal_mode_below_threshold`
4. RED: `test_max_active_tools_increased_to_100`
5. GREEN: DeferredToolProxy 구현, get_tools() 수정

**DoD:**
- [ ] 도구 수 > defer_loading_threshold 시 메타데이터만 로드
- [ ] 도구 실행 시 풀 스키마 lazy load
- [ ] MAX_ACTIVE_TOOLS 100으로 증가
- [ ] 설정으로 threshold 조정 가능
- [ ] 신규 테스트 4개 이상

**의존성:** 독립

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 10 시작 | `/tdd` | TDD Red-Green-Refactor |
| Step 11 시작 | `/tdd` | TDD Red-Green-Refactor |
| Part D 완료 | `phase-orchestrator` Agent | Phase 4 전체 DoD 검증 |
| Part D 완료 | `code-reviewer` Agent | 최종 코드 품질 검토 |

---

## 커밋 정책

```
feat(phase4): Step 10 - A2A agent health monitoring
feat(phase4): Step 11 - Defer loading for large-scale tool support
docs(phase4): Phase 4 complete - documentation updates
```

---

## Part D Definition of Done

### 기능

- [ ] A2A 에이전트 health check (주기적 + API)
- [ ] 대규모 도구 defer loading (메타데이터 only → lazy load)
- [ ] MAX_ACTIVE_TOOLS 100

### 품질

- [ ] 기존 테스트 전체 통과 (regression 0)
- [ ] Backend coverage >= 90%
- [ ] `ruff check` + `ruff format` clean

### 문서 (Phase 4 최종)

- [ ] `docs/STATUS.md` — Phase 4 Complete 반영
- [ ] `docs/roadmap.md` — Phase 4 DoD 체크, Phase 5 Next Actions 업데이트
- [ ] `CLAUDE.md` — Phase 4 성과 반영 (StreamChunk, Observability 등)
- [ ] `src/adapters/README.md` — Defer Loading, Observability 섹션 추가
- [ ] `docs/plans/README.md` — Phase 4 상태 업데이트

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| DeferredToolProxy가 ADK BaseTool 호환 여부 | 🟡 중간 | ADK가 duck typing 사용하는지 확인. 불가 시 BaseTool 상속 |
| A2A health check가 Agent Card GET만으로 불충분 | 🟢 낮음 | 현재로서는 Card URL 응답으로 충분. 향후 JSON-RPC ping 추가 가능 |
| Defer loading 성능 벤치마크 부재 | 🟡 중간 | 50개 이상 도구로 수동 테스트. Phase 5에서 정밀 벤치마크 |

---

## Phase 4 완료 시 전체 업데이트 목록

Part D 완료 = Phase 4 완료. 다음 파일들을 최종 업데이트:

| 파일 | 변경 내용 |
|------|----------|
| `docs/STATUS.md` | Phase 4 Complete, 커버리지, 테스트 수 업데이트 |
| `docs/roadmap.md` | Phase 4 DoD `[x]` 체크, Phase 5 Next Actions |
| `CLAUDE.md` | Quick Reference 업데이트, Phase 4 성과 |
| `docs/plans/README.md` | Phase 4 → ✅ Complete |
| `docs/plans/phase4.0.md` | 상태: ✅ Complete |
| `src/adapters/README.md` | StreamChunk, Observability, Defer Loading 추가 |

---

*Part D 계획 작성일: 2026-01-31*
*초안 Steps 9-10 기반*
*Phase 4 최종 Part — 완료 시 전체 문서 업데이트 책임*
