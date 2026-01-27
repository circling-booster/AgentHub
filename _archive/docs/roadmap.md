# FHLY 개발 로드맵(임시계획)

> **목적**: 아키텍처 확정부터 구현까지의 단계별 가이드
> **현재 단계**: Phase 1 (기반 구축)
> **아키텍처 확정일**: 2026-01-27

---

## Phase 0: 아키텍처 확정 ✅ 완료

### 결과

| 항목 | 결정 |
|------|------|
| 아키텍처 | **하이브리드 레이어드 (시나리오 B+)** |
| 기반 프레임워크 | **Google ADK** |
| MCP 통합 | ADK MCPToolset (Streamable HTTP) |
| A2A 통합 | ADK to_a2a() |

### 완료된 작업
- [x] **타겟 고객 정의**: 개발자(확장성) + 일반사용자(초반 수익화)
- [x] **시나리오 A vs B/B+ 최종 선택**: B+ (하이브리드 레이어드) 확정
- [x] **기반 기술 선택**: Google ADK

### 확인된 프로젝트 조건
- Claude Desktop 호환: 불필요
- MCP Transport: 전부 Streamable HTTP
- 타겟: 개발자 + 일반사용자

### 미완료 (Phase 1에서 계속)
- [ ] **핵심 문제 정의**: "FHLY가 해결하는 단 하나의 문제는?"
- [ ] **엘리베이터 피치**: 10분 안에 설명할 수 있는 프로젝트 요약

---

## Phase 1: 기반 구축 (현재)

### 목표
확정된 아키텍처(Google ADK 기반 하이브리드 레이어드)의 PoC를 구현한다.

### Week 1-2: 환경 설정 및 PoC

#### 작업 항목
- [ ] Google ADK 개발 환경 설정
- [ ] LiteLLM 설정 (Claude 연동)
- [ ] 기존 MCP 서버(음원분리) 1개 연결
- [ ] 간단한 프롬프트 → 도구 실행 파이프라인

#### 기술 스택
```
Python 3.10+
├── google-adk >= 1.0.0
├── litellm (Claude, GPT-4 등)
└── 기존 MCP 서버 (Streamable HTTP)
```

#### 성공 기준
```
사용자 프롬프트: "이 음원에서 보컬 분리해줘"
    → ADK Agent가 요청 수신
    → MCPToolset으로 음원분리 MCP 서버 호출
    → 결과 반환
```

### Week 3: 검증 및 피드백

#### 작업 항목
- [ ] 실제 사용자 3명에게 테스트
- [ ] 피드백 수집 및 정리
- [ ] Phase 2 계획 수립

---

## Phase 2: 확장

### 목표
추가 MCP 서버 연결, 도메인 에이전트 분리, 브라우저 확장 개발

### 핵심 구현 항목

#### 2.1 도메인 에이전트 분리
```python
# 음악 처리 에이전트
music_agent = Agent(name="music-agent", tools=[audio_mcp_tools])

# 문서 처리 에이전트
document_agent = Agent(name="document-agent", tools=[ocr_mcp_tools])

# 유틸리티 라우터
utility_agent = Agent(name="utility-agent", tools=[captcha_mcp_tools, ...])

# 오케스트레이터
orchestrator = Agent(
    name="fhly-orchestrator",
    sub_agents=[music_agent, document_agent, utility_agent]
)
```

#### 2.2 MCP 서버 전체 연결
- [ ] 음원분리 MCP (Phase 1에서 완료)
- [ ] OCR MCP
- [ ] 캡차 인식 MCP

#### 2.3 Chrome Extension 개발
| 방식 | 채택 | 비고 |
|------|------|------|
| Chrome Extension | O | Content Script로 UI 주입 |
| MITM Proxy | 보류 | 보안 이슈로 현재 단계에서 제외 |

### MCP 분류 전략: Lazy Wrapping + 동적 라우터

**초기 접근법:**
- 명확한 도메인(음악, 문서 등)만 전용 에이전트로 래핑
- 나머지는 "유틸리티 라우터 에이전트"가 직접 MCP 호출
- 사용 패턴 축적 후 점진적 카테고리 분리

**대안 (추후 고려):**

| 대안 | 설명 | 적용 시점 |
|------|------|-----------|
| 태그 기반 다중 분류 | MCP에 여러 태그 부여 | 서버 수 50개 이상 시 |
| 계층적 분류 | 대분류 → 중분류 → 소분류 | 명확한 분류 체계 필요 시 |
| 전용 라우터 에이전트 분리 | 유틸리티를 더 세분화 | 특정 유틸리티 사용량 급증 시 |

---

## Phase 3: 비즈니스

### 목표
수익 모델 구체화 및 서비스 런칭

### 작업 항목
1. 개발자용 API/호스트 출시
2. 일반 사용자용 구독 서비스 런칭
3. 문서화 및 온보딩

---

## 의사결정 기록

### 2026-01-27: 아키텍처 확정

| 결정 | 내용 | 이유 |
|------|------|------|
| **아키텍처** | 하이브리드 레이어드 (B+) | 업계 표준, 확장성, A2A+MCP 네이티브 지원 |
| **기반 기술** | Google ADK | MCPToolset, to_a2a() 내장, v1.0.0 안정 버전 |
| **시나리오 A 포기** | MCP 호스트 중심 미채택 | Claude Desktop 불필요, 래퍼 개발 부담 |

#### 시나리오 A 포기로 인한 Trade-offs

| 포기한 것 | 영향도 | 완화 방안 |
|-----------|--------|-----------|
| Claude Desktop 호환 | 낮음 | 자체 UI (Chrome Extension) 개발 |
| 기존 MCP 호스트 코드 활용 | 낮음 | ADK MCPToolset 사용 |
| ADK 프레임워크 의존성 | 중간 | Apache 2.0, LiteLLM으로 LLM 불가지론 |

### 2026-01-27: 초기 계획

| 결정 | 내용 | 이유 |
|------|------|------|
| 철학 제거 | Fractal Holarchy 개념 삭제 | 구현과 무관 |
| 범위 축소 | 통합 호스트에 집중 | 우선순위 명확화 |
| MITM 보류 | 현재 단계 제외 | 복잡성 감소 |
| 분류 전략 | Lazy Wrapping + 동적 라우터 | 초기 단순화 |

---

## 참고

- 아키텍처 결정 기록: [architecture-scenarios.md](architecture-scenarios.md)
- 프로토콜 리서치: [architecture-research.md](architecture-research.md)
- 아카이브된 아이디어: [archived-ideas.md](archived-ideas.md)
