# 아키텍처 리서치 노트

> **작성일**: 2026년 1월 27일
> **목적**: 아키텍처 결정을 위한 참고자료
> **상태**: ✅ 아키텍처 확정됨 (하이브리드 레이어드 + Google ADK)
> **참고**: 최종 결정은 [architecture-scenarios.md](architecture-scenarios.md) 참조

---

## 1. MCP (Model Context Protocol)

### 개요
- 2024년 11월 Anthropic이 발표한 오픈 표준
- AI 시스템과 외부 도구/데이터 소스 간 통합을 표준화
- 2025년 12월, Linux Foundation 산하 [Agentic AI Foundation (AAIF)](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)에 기증
- 월 9,700만+ SDK 다운로드, 10,000+ 활성 서버

### 핵심 구성요소
- **Tools**: LLM이 실행할 수 있는 함수 (모델 제어)
- **Resources**: 컨텍스트 주입을 위한 데이터 소스 (애플리케이션 제어)
- **Prompts**: 사용자 상호작용을 위한 템플릿 (사용자 제어)

### Sampling 기능
- 서버가 클라이언트의 LLM에게 completion 요청 가능
- 멀티스텝 에이전틱 워크플로우 구현에 유용
- 모델 선택 우선순위: costPriority, speedPriority, intelligencePriority
- **주의**: Claude Desktop에서는 아직 미지원, VS Code GitHub Copilot에서 지원

### Python 개발
- 공식 SDK: `pip install "mcp[cli]"` (Python 3.10+)
- FastMCP: `pip install fastmcp` - 데코레이터 기반 API로 70% 이상의 MCP 서버가 사용
- v2 안정 릴리스 2026년 Q1 예정

### 참고 자료
- [MCP 공식 명세](https://modelcontextprotocol.io/specification/2025-11-25)
- [Anthropic MCP 코스](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [FastMCP 문서](https://gofastmcp.com/getting-started/welcome)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## 2. A2A (Agent-to-Agent Protocol)

### 개요
- 2025년 4월 Google이 발표, 150+ 조직 지원
- 2025년 7월 v0.3 릴리스: gRPC 지원, 보안 카드 서명, Python SDK 확장
- Linux Foundation A2A 프로젝트로 이관

### 핵심 특징
- HTTP, SSE, JSON-RPC 기반 (기존 IT 스택과 호환)
- OpenAPI 호환 인증/인가 스키마
- 에이전트 간 capability discovery, 장기 실행 태스크 협업 지원

### A2A vs MCP
- MCP: Agent ↔ System (수직 통합) - 도구/데이터 접근
- A2A: Agent ↔ Agent (수평 협업) - 에이전트 간 통신
- **상호 보완적** - 대부분의 엔터프라이즈 시스템에서 함께 사용

### Google ADK (Agent Development Kit)
- 최신 버전 1.23.0 (2026년 1월 22일)
- MCP 도구 사용/소비 지원
- `to_a2a(root_agent)` 함수로 ADK 에이전트를 A2A 서버로 변환

### 참고 자료
- [A2A GitHub](https://github.com/a2aproject/A2A)
- [Google ADK 문서](https://google.github.io/adk-docs/)
- [ADK + A2A 가이드](https://google.github.io/adk-docs/a2a/)
- [ADK + MCP 가이드](https://google.github.io/adk-docs/mcp/)

---

## 3. 하이브리드 아키텍처 (MCP + A2A)

### 권장 패턴
```
┌─────────────────────────────────────────────┐
│          A2A Coordination Layer             │
│  (에이전트 간 협업, 태스크 분해/할당)          │
├─────────────────────────────────────────────┤
│          MCP Tool Access Layer              │
│  (각 에이전트의 도구/리소스 접근)              │
└─────────────────────────────────────────────┘
```

### 핵심 고려사항
- MCP: API 게이트웨이, 컨텍스트 공유 보안, 데이터 권한
- A2A: 에이전트 레지스트리, 메시징 인프라, 표준화된 ID 관리
- N-squared connectivity 문제: 에이전트 수 증가 시 직접 연결 부담

### 2026년 전망 (Gartner)
- 40% 엔터프라이즈 애플리케이션에 태스크 특화 AI 에이전트 포함 예정
- 멀티 에이전트 협업이 표준화될 것으로 전망

### 참고 자료
- [MCP vs A2A 프로토콜 가이드](https://onereach.ai/blog/guide-choosing-mcp-vs-a2a-protocols/)
- [Enterprise AI Stack 2026](https://dextralabs.com/blog/enterprise-ai-stack-2026-mcp-a2a-domain-models/)
- [A2A + MCP Elasticsearch 구현](https://www.elastic.co/search-labs/blog/a2a-protocol-mcp-llm-agent-workflow-elasticsearch)

---

## 4. Fractal Holarchy 개념

### 소프트웨어 적용
- 애플리케이션은 동일한 API를 가진 컴포넌트 트리
- 각 컴포넌트는 다른 컴포넌트를 포함(사용) 가능
- 최상위 컴포넌트도 다른 컴포넌트와 동일한 구조
- **핵심**: 하나의 컴포넌트 작동 방식을 알면 전체를 이해

### 프레임워크 예시
- React/Angular: 컴포넌트 트리 구조
- Elm Architecture: init, update, view 함수의 프랙탈 패턴

### Holarchy 특성
- 모든 노드가 holon (개별 + 집단 지향 행동 동시 구현)
- 본질적으로 peer-to-peer 구조
- 자기 조직화 (self-organisation) 개념

### 참고 자료
- [Fractal Architecture](http://antontelesh.github.io/architecture/2016/03/16/fractal-architecture.html)
- [Fractal Design Patterns](https://blog.bethcodes.com/fractal-design-patterns)
- [Holarchy Wiki](https://organicdesign.nz/Holarchy)

---

## 5. 브라우저 확장 및 MCP 클라이언트

### 주요 Chrome 확장

| 확장 | 설명 |
|------|------|
| [Chrome MCP Server](https://github.com/hangwin/mcp-chrome) | 일상 브라우저 제어, 로그인 상태 활용 |
| [Browser MCP](https://browsermcp.io/) | 로컬 자동화, 봇 감지 우회 |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | DevTools 전체 기능 AI 접근 |

### 보안 고려사항
- Indirect prompt injection 취약점 주의
- 페이지 컨텐츠가 LLM 컨텍스트에 주입될 때 악성 명령 실행 가능성

---

## 6. 음원 분리 MCP 서버 (Demucs)

### Stem MCP Server
- Demucs 모델 기반 AI 음원 분리
- 보컬 추출, 루프 생성, 음악 분석 지원
- MIT 라이선스 (상업적 사용 가능)

### 설치
```bash
pip install mcp>=1.0.0 librosa soundfile numpy scipy torch torchaudio demucs pydub
```

### Demucs 모델 종류
- `mdx_extra_q`: CPU 전용, 가장 빠름
- `mdx`: GPU 권장
- `htdemucs`: v4, GPU 필수
- `htdemucs_ft`: HD, 최고 품질, GPU 필수

**참고:** facebookresearch/demucs 원본 저장소는 더 이상 유지보수되지 않음. [adefossez/demucs](https://github.com/adefossez/demucs) 포크 사용 권장

---

## 7. Agentic AI Foundation (AAIF)

### 개요
- 2025년 12월 Linux Foundation 산하 설립
- Anthropic, Block, OpenAI 공동 창립

### 핵심 프로젝트
- **MCP**: AI 모델과 도구/데이터 연결 표준
- **goose**: 오픈소스 로컬 우선 AI 에이전트 프레임워크
- **AGENTS.md**: AI 코딩 에이전트를 위한 프로젝트별 가이드 표준

### 플래티넘 멤버
AWS, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft, OpenAI

### 거버넌스
- Governing Board: 전략적 투자, 예산, 멤버 모집, 프로젝트 승인
- 개별 프로젝트: 기술적 방향성 자율 유지

### 참고 자료
- [AAIF 발표](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)
- [OpenAI 참여 발표](https://openai.com/index/agentic-ai-foundation/)
- [MCP joins AAIF](http://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/)
