# ADR-0009: LangGraph는 A2A Agent, Plugin은 개별 도구만

## 상태

승인됨

## 날짜

2026-02-01

## 컨텍스트

Phase 5 Part A 구현 중, LangGraph와 AgentHub의 통합 방식에 대해 재검토가 필요해졌다.

**기존 가정:**
- LangGraph Agent를 AgentHub Plugin System에서 래핑하여 실행
- Phase 6C의 LangChainPlugin이 LangGraph를 포함
- Phase 8의 동적 로딩이 LangGraph Agent를 대상으로 포함

**발견사항 (2026-02-01 웹 검색):**
- LangGraph StateGraph는 독립 A2A 서버로 노출 가능 (`/a2a/{assistant_id}` 자동 제공)
- Google ADK는 `LangGraphAgent`로 LangGraph CompiledGraph를 실험적으로 래핑 지원
- 실제 사례: YouTube Agent(LangGraph) + Summary Agent(ADK)가 A2A 프로토콜로 통신
- LangChain의 Agent Server가 A2A 엔드포인트를 기본 지원

**핵심 구분:**
- LangGraph Agent = **독립 프로세스** (A2A Server로 노출)
- LangChain Tool = **개별 함수** (WikipediaQueryRun 등, 프로세스 내 실행)

## 결정

1. **LangGraph Agent는 A2A 프로토콜로 통합** (Plugin 아님)
   - 사용자가 A2A Agents 탭에서 LangGraph 서버 URL 등록
   - Phase 3에서 구현된 A2A Client 활용 (추가 구현 불필요)

2. **Plugin System은 "프로세스 내 개별 도구 확장"으로 범위 한정**
   - LangChain 개별 Tool (WikipediaQueryRun, RequestsGet 등)
   - REST API Wrapper
   - 사용자 정의 Python 함수 (`AGENTHUB_TOOLS` 컨벤션)

3. **AgentHub 외부 통합 3-Track 아키텍처 확정**
   - MCP: 도구 프로토콜 (서버 ↔ 클라이언트)
   - A2A: 에이전트 프로토콜 (에이전트 ↔ 에이전트, LangGraph/CrewAI/ADK 포함)
   - Plugin: 프로세스 내 도구 확장 (사용자 코드 로딩)

## 대안

### 대안 1: Plugin System에 LangGraph 포함
- 장점: 단일 진입점 (모든 확장이 Plugin)
- 단점: LangGraph Agent를 같은 프로세스에서 실행해야 함 (불필요한 복잡도)
- 단점: A2A 표준을 무시하는 결과

### 대안 2: Plugin System 완전 제거, 모든 것을 A2A로
- 장점: 아키텍처 단순화 (MCP + A2A만)
- 단점: 단순한 Python 함수 하나 추가하려면 A2A 서버를 띄워야 함 (과도)
- 단점: 사용자 진입 장벽 상승

## 근거

1. **프로토콜 목적 일치**: A2A는 에이전트 간 통신을 위해 설계됨. LangGraph Agent는 에이전트이므로 A2A가 적합.
2. **이미 구현됨**: Phase 3에서 A2A Client가 완성되어 있어 추가 비용 없음.
3. **사용자 경험**: LangGraph 서버를 띄우고 URL만 입력하면 됨 (기존 A2A Agents 탭 사용).
4. **Plugin의 적절한 범위**: 프로세스 내 경량 도구 확장에 적합. 외부 에이전트를 내부에 강제 로딩할 이유 없음.

## 결과

### 긍정적 영향
- 아키텍처 명확성 향상 (MCP/A2A/Plugin 역할 분리)
- Phase 6C Plugin System 범위 축소로 구현 복잡도 감소
- LangGraph 통합에 추가 개발 불필요 (Phase 3 A2A Client 활용)

### 부정적 영향 / 트레이드오프
- Phase 8 범위 축소 (LangGraph 동적 로딩 시나리오 제거)
- 사용자가 LangGraph Agent를 사용하려면 별도 프로세스 실행 필요

### 후속 조치
- [ ] Phase 6C 문서 수정: LangChainPlugin = "개별 Tool 래핑"으로 명확화
- [ ] Phase 8 문서 수정: "사용자 정의 도구 동적 로딩"으로 범위 확정
- [ ] Phase 6 master DoD 수정

## 관련 문서

- [Phase 5 Part A](../plans/phase5.0-partA.md) - A2A Verification (진단 결과)
- [Phase 6 Part C](../plans/phase6.0-partC.md) - Plugin System
- [Phase 8](../plans/phase8.0.md) - Dynamic Loading
- [LLM agents - ADK](https://google.github.io/adk-docs/agents/llm-agents/)
- [A2A endpoint - LangChain](https://docs.langchain.com/langsmith/server-a2a)
