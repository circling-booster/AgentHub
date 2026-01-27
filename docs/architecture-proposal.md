# AgentHub 아키텍처 제안

> Google ADK 기반 MCP + A2A 통합 Agent System을 위한 프로젝트 구조 제안

---

## 아키텍처 1: 계층형 구조 (Layered Architecture)

전통적인 3-tier 아키텍처 기반, 책임 분리가 명확한 구조입니다.

```
agenthub/
├── src/
│   ├── api/                      # Presentation Layer
│   │   ├── __init__.py
│   │   ├── server.py             # FastAPI 앱 진입점
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py           # 채팅/대화 엔드포인트
│   │   │   ├── mcp.py            # MCP 서버 관리 엔드포인트
│   │   │   ├── a2a.py            # A2A 에이전트 관리 엔드포인트
│   │   │   └── settings.py       # 설정 엔드포인트
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── cors.py
│   │   │   └── error_handler.py
│   │   └── schemas/              # Pydantic 요청/응답 모델
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       └── registry.py
│   │
│   ├── services/                 # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── agent_service.py      # LlmAgent 생성/관리
│   │   ├── mcp_service.py        # MCP 연결 관리
│   │   ├── a2a_service.py        # A2A 프로토콜 핸들링
│   │   └── llm_service.py        # LiteLLM 설정/전환
│   │
│   ├── data/                     # Data Access Layer
│   │   ├── __init__.py
│   │   ├── registry_store.py     # MCP/A2A 등록정보 저장
│   │   ├── session_store.py      # 세션/대화 이력
│   │   └── config_store.py       # 설정값 관리
│   │
│   ├── core/                     # 공통 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py             # 환경설정
│   │   ├── exceptions.py         # 커스텀 예외
│   │   └── logging.py            # 로깅 설정
│   │
│   └── main.py                   # 진입점
│
├── extension/                    # Chrome Extension
│   ├── manifest.json
│   ├── src/
│   │   ├── popup/                # 팝업 UI
│   │   ├── content/              # 콘텐츠 스크립트
│   │   ├── background/           # 서비스 워커
│   │   └── lib/                  # 공통 라이브러리
│   └── assets/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── configs/
│   ├── default.yaml
│   └── development.yaml
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 특징 및 의미

| 항목 | 설명 |
|------|------|
| **패턴** | 전통적인 3-tier (Presentation → Business → Data) |
| **의존성 방향** | 위에서 아래로 단방향 (API → Service → Data) |
| **테스트 용이성** | 각 레이어별 독립적 테스트 가능 |

### 장점

- ✅ **직관적**: 대부분의 개발자에게 익숙한 구조
- ✅ **책임 분리**: 각 레이어가 단일 책임을 가짐
- ✅ **빠른 시작**: 초기 개발 속도가 빠름
- ✅ **온보딩 용이**: 새 팀원이 코드 위치 예측 가능

### 단점

- ❌ **수평 확장 어려움**: 기능 추가 시 여러 레이어 수정 필요
- ❌ **순환 의존성 위험**: 레이어 간 경계가 흐려질 수 있음
- ❌ **Feature 분산**: 하나의 기능이 여러 폴더에 분산됨

### 트레이드오프

```
단순성 ↔ 확장성
```

초기에는 빠르지만, MCP/A2A 서버가 10개 이상 등록되거나 복잡한 워크플로우가 추가되면 서비스 레이어가 비대해질 수 있습니다.

---

## 아키텍처 2: 기능 중심 구조 (Feature-based / Modular)

기능(도메인)별로 모듈을 분리하여 응집도를 높인 구조입니다.

```
agenthub/
├── src/
│   ├── app.py                    # FastAPI 앱 조립
│   ├── main.py                   # 진입점
│   │
│   ├── features/                 # 기능별 모듈
│   │   ├── __init__.py
│   │   │
│   │   ├── chat/                 # 채팅 기능 전체
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # /chat 엔드포인트
│   │   │   ├── service.py        # 대화 처리 로직
│   │   │   ├── schemas.py        # 요청/응답 모델
│   │   │   └── agent.py          # LlmAgent 래퍼
│   │   │
│   │   ├── mcp/                  # MCP 서버 관리 기능
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # /mcp 엔드포인트
│   │   │   ├── service.py        # MCP 연결/관리 로직
│   │   │   ├── schemas.py
│   │   │   ├── toolset.py        # McpToolset 래퍼
│   │   │   └── registry.py       # MCP 서버 등록 저장
│   │   │
│   │   ├── a2a/                  # A2A 에이전트 관리 기능
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   ├── client.py         # A2A 클라이언트
│   │   │   └── registry.py
│   │   │
│   │   ├── llm/                  # LLM 설정/전환 기능
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── providers.py      # LiteLLM 프로바이더 설정
│   │   │
│   │   └── settings/             # 전역 설정 관리
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── service.py
│   │       └── schemas.py
│   │
│   ├── shared/                   # 공유 컴포넌트
│   │   ├── __init__.py
│   │   ├── config.py             # 환경설정
│   │   ├── exceptions.py         # 공통 예외
│   │   ├── middleware.py         # 공통 미들웨어
│   │   ├── database.py           # DB 연결 (SQLite/JSON)
│   │   └── events.py             # 이벤트 버스 (모듈 간 통신)
│   │
│   └── infrastructure/           # 외부 시스템 연동
│       ├── __init__.py
│       ├── adk/                  # Google ADK 통합
│       │   ├── __init__.py
│       │   └── factory.py        # Agent 팩토리
│       └── storage/              # 저장소 추상화
│           ├── __init__.py
│           ├── base.py
│           └── json_store.py
│
├── extension/
│   ├── manifest.json
│   └── src/
│       ├── features/             # Extension도 기능별 분리
│       │   ├── popup/
│       │   ├── sidebar/
│       │   ├── context-menu/
│       │   └── page-capture/
│       └── shared/
│
├── tests/
│   ├── features/                 # 기능별 테스트
│   │   ├── chat/
│   │   ├── mcp/
│   │   └── a2a/
│   └── integration/
│
├── pyproject.toml
└── README.md
```

### 특징 및 의미

| 항목 | 설명 |
|------|------|
| **패턴** | Vertical Slice / Feature Module |
| **응집도** | 높음 - 관련 코드가 한 폴더에 모임 |
| **모듈 독립성** | 각 feature가 자체 라우터, 서비스, 스키마 보유 |

### 장점

- ✅ **높은 응집도**: 하나의 기능 수정 시 한 폴더만 작업
- ✅ **병렬 개발**: 팀원별로 다른 feature 담당 가능
- ✅ **기능 단위 배포**: 특정 기능만 독립적으로 테스트/배포 가능
- ✅ **마이크로서비스 전환 용이**: 필요시 feature를 별도 서비스로 분리 가능

### 단점

- ❌ **코드 중복 가능성**: feature 간 유사한 로직 발생 가능
- ❌ **feature 간 의존성 관리 필요**: 이벤트 버스 등 추가 패턴 필요
- ❌ **초기 설계 비용**: 모듈 경계를 잘 정해야 함

### 트레이드오프

```
응집도 ↔ 일관성
```

각 모듈의 독립성이 높지만, 전체적인 일관성(공통 패턴, 코드 스타일)을 유지하려면 추가 노력이 필요합니다.

---

## 아키텍처 3: 헥사고날 구조 (Hexagonal / Ports and Adapters)

외부 시스템(MCP, A2A, LLM)과의 연동이 많은 이 프로젝트에 적합한 아키텍처입니다.

```
agenthub/
├── src/
│   ├── main.py                   # 진입점
│   │
│   ├── domain/                   # 핵심 비즈니스 로직 (순수 Python)
│   │   ├── __init__.py
│   │   ├── entities/             # 도메인 엔티티
│   │   │   ├── __init__.py
│   │   │   ├── agent.py          # Agent 도메인 모델
│   │   │   ├── tool.py           # Tool (MCP 도구) 모델
│   │   │   ├── endpoint.py       # MCP/A2A 엔드포인트 모델
│   │   │   └── conversation.py   # 대화 세션 모델
│   │   │
│   │   ├── services/             # 도메인 서비스
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # 에이전트 오케스트레이션
│   │   │   ├── registry.py       # 엔드포인트 등록 관리
│   │   │   └── conversation.py   # 대화 처리 로직
│   │   │
│   │   └── ports/                # 포트 (인터페이스 정의)
│   │       ├── __init__.py
│   │       ├── inbound/          # Driving Ports (입력)
│   │       │   ├── __init__.py
│   │       │   ├── chat_port.py          # 채팅 요청 처리
│   │       │   └── management_port.py    # MCP/A2A 관리
│   │       │
│   │       └── outbound/         # Driven Ports (출력)
│   │           ├── __init__.py
│   │           ├── llm_port.py           # LLM 호출 인터페이스
│   │           ├── mcp_port.py           # MCP 연결 인터페이스
│   │           ├── a2a_port.py           # A2A 통신 인터페이스
│   │           └── storage_port.py       # 저장소 인터페이스
│   │
│   ├── adapters/                 # 어댑터 (포트 구현체)
│   │   ├── __init__.py
│   │   │
│   │   ├── inbound/              # Primary Adapters (입력 처리)
│   │   │   ├── __init__.py
│   │   │   ├── http/             # HTTP API 어댑터
│   │   │   │   ├── __init__.py
│   │   │   │   ├── app.py        # FastAPI 앱
│   │   │   │   ├── routes/
│   │   │   │   │   ├── chat.py
│   │   │   │   │   ├── mcp.py
│   │   │   │   │   └── a2a.py
│   │   │   │   └── schemas/
│   │   │   │       └── ...
│   │   │   │
│   │   │   └── a2a_server/       # A2A 서버 어댑터 (to_a2a)
│   │   │       ├── __init__.py
│   │   │       └── server.py
│   │   │
│   │   └── outbound/             # Secondary Adapters (외부 연동)
│   │       ├── __init__.py
│   │       ├── adk/              # Google ADK 어댑터
│   │       │   ├── __init__.py
│   │       │   ├── llm_adapter.py        # LiteLLM 구현
│   │       │   └── mcp_adapter.py        # McpToolset 구현
│   │       │
│   │       ├── a2a_client/       # A2A 클라이언트 어댑터
│   │       │   ├── __init__.py
│   │       │   └── client.py
│   │       │
│   │       └── storage/          # 저장소 어댑터
│   │           ├── __init__.py
│   │           ├── json_storage.py       # JSON 파일 저장
│   │           └── sqlite_storage.py     # SQLite 저장
│   │
│   └── config/                   # 의존성 주입 / 설정
│       ├── __init__.py
│       ├── container.py          # DI 컨테이너
│       └── settings.py           # 환경변수 설정
│
├── extension/
│   └── ...                       # 동일
│
├── tests/
│   ├── domain/                   # 도메인 단위 테스트 (Mocking 없이)
│   ├── adapters/                 # 어댑터 테스트
│   └── integration/              # 통합 테스트
│
├── pyproject.toml
└── README.md
```

### 특징 및 의미

| 항목 | 설명 |
|------|------|
| **패턴** | Hexagonal Architecture / Ports and Adapters |
| **핵심 원칙** | 도메인 로직이 외부 의존성을 모름 |
| **의존성 방향** | 바깥 → 안 (Adapters → Domain) |
| **교체 용이성** | 어댑터만 교체하면 외부 시스템 변경 가능 |

### 장점

- ✅ **높은 테스트 용이성**: 도메인 로직을 Mocking 없이 테스트 가능
- ✅ **외부 시스템 교체 용이**: LiteLLM → 다른 라이브러리 전환이 어댑터만 수정
- ✅ **명확한 경계**: MCP/A2A/LLM 각각이 별도 어댑터로 격리
- ✅ **미래 대비**: 프로토콜 변경, 새 LLM 프로바이더 추가 시 영향 최소화

### 단점

- ❌ **높은 초기 복잡도**: 인터페이스(Port) 정의가 많아짐
- ❌ **오버엔지니어링 위험**: 작은 프로젝트에는 과도할 수 있음
- ❌ **학습 곡선**: 팀원들이 패턴을 이해해야 함
- ❌ **보일러플레이트**: Port/Adapter 매핑 코드 증가

### 트레이드오프

```
유연성 ↔ 복잡도
```

외부 시스템(MCP, A2A, 여러 LLM)과의 연동이 핵심인 AgentHub에는 적합하지만, 초기 개발 속도가 다소 느릴 수 있습니다.

---

## 비교 요약

| 기준 | 계층형 | 기능 중심 | 헥사고날 |
|------|--------|----------|----------|
| **초기 개발 속도** | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| **확장성** | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| **테스트 용이성** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **팀 협업** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **외부 시스템 교체** | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| **학습 곡선** | 낮음 | 보통 | 높음 |
| **적합한 팀 규모** | 1-3명 | 3-7명 | 5+명 |

---

## 권장 사항

### 1. 현재 단계에서의 추천: 기능 중심 구조 (아키텍처 2)

**이유:**

- AgentHub는 MCP/A2A/Chat/Settings 등 명확히 분리되는 기능이 존재
- 1-2인 개발 시작이라면 기능별로 집중하기 좋음
- 추후 헥사고날로 점진적 전환 가능

### 2. 공통 제언

| 항목 | 제언 |
|------|------|
| **DI 컨테이너** | `dependency-injector` 또는 FastAPI의 `Depends`로 의존성 관리 |
| **이벤트 버스** | 모듈 간 통신을 위해 간단한 이벤트 시스템 도입 고려 |
| **설정 관리** | `pydantic-settings`로 환경변수 + YAML 통합 관리 |
| **저장소** | 초기에는 JSON 파일, 추후 SQLite로 마이그레이션 |
| **Extension 통신** | WebSocket 또는 SSE로 실시간 응답 스트리밍 권장 |

### 3. 점진적 전환 경로

```
기능 중심 (Phase 1)
      ↓
도메인 레이어 분리 (Phase 2)
      ↓
Ports/Adapters 도입 (Phase 3 - 필요시)
```

초기에는 `features/` 구조로 빠르게 시작하고, MCP/A2A 어댑터가 복잡해지면 점진적으로 Port/Adapter 패턴을 도입하는 것이 현실적입니다.

### 4. 즉시 결정이 필요한 사항

| 결정 사항 | 선택지 |
|----------|--------|
| **패키지 관리** | `poetry` vs `uv` vs `pip-tools` |
| **데이터 저장** | JSON 파일 vs SQLite vs 둘 다 지원 |
| **Extension 빌드** | Vite + TypeScript vs Webpack vs Plasmo |
| **테스트 프레임워크** | pytest + pytest-asyncio |

---

*문서 생성일: 2026-01-28*
