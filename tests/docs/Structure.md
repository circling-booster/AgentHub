# **🏗️ Directory Structure & Fixtures**

## **Directory Structure**

tests/  
├── conftest.py                    \# 🔷 Root fixtures (session-scoped)  
│   ├── test\_config                \# 전역 설정  
│   ├── a2a\_echo\_agent             \# A2A Echo Agent subprocess (포트 9003\)  
│   ├── a2a\_math\_agent             \# A2A Math Agent subprocess (동적 포트)  
│   └── mcp\_synapse\_server         \# MCP Synapse subprocess (autouse, 로컬만)  
│  
├── unit/                          \# 단위 테스트 (Domain Layer)  
│   ├── conftest.py                \# 🔶 Fake Adapter fixtures  
│   ├── domain/  
│   │   ├── entities/              \# 엔티티 테스트  
│   │   └── services/              \# 서비스 테스트  
│   ├── adapters/                  \# Adapter 단위 테스트  
│   └── fakes/                     \# 🔸 Fake Adapter 구현체 (중앙 관리)  
│       ├── \_\_init\_\_.py            \# Export: FakeConversationStorage, FakeUsageStorage 등  
│       ├── fake\_storage.py  
│       ├── fake\_orchestrator.py  
│       ├── fake\_toolset.py  
│       ├── fake\_conversation\_service.py  
│       ├── fake\_a2a\_client.py  
│       ├── fake\_mcp\_client.py  
│       └── fake\_usage\_storage.py  
│  
├── integration/                   \# 통합 테스트 (Adapter Layer)  
│   ├── conftest.py                \# 🔶 Integration fixtures  
│   │   ├── temp\_data\_dir          \# 임시 데이터 디렉토리  
│   │   ├── authenticated\_client   \# 인증된 TestClient (lifespan 포함)  
│   │   ├── mock\_mcp\_toolset\_in\_ci \# CI 환경 Mock (autouse)  
│   │   └── mock\_mcp\_client        \# dict-based MCP mock  
│   └── adapters/                  \# Adapter 통합 테스트  
│  
├── chaos/                         \# Chaos Engineering Tests  
│   ├── conftest.py                \# Chaos fixtures  
│   │   ├── chaotic\_mcp\_server     \# 포트 9999 (장애 주입)  
│   │   ├── chaos\_retry\_config     \# 단축 타임아웃  
│   │   └── container              \# Direct container access  
│   ├── test\_circuit\_breaker.py    \# Circuit Breaker 테스트  
│   ├── test\_concurrent\_requests.py \# 동시성 테스트  
│   └── test\_mcp\_failures.py       \# MCP 장애 시나리오  
│  
├── e2e/                           \# E2E 테스트 (Full Stack)  
│   ├── conftest.py                \# 🔶 E2E fixtures (Playwright)  
│   ├── test\_extension\_server.py  \# TestClient 기반 E2E  
│   └── test\_playwright\_extension.py  \# Full Browser E2E  
│  
└── fixtures/                      \# 테스트용 fixture 서버  
    └── a2a\_agents/  
        ├── echo\_agent.py          \# Echo A2A agent  
        └── math\_agent.py          \# Math A2A agent (ADK LlmAgent)

## **🔧 Fixture Hierarchy**

**Fixture Resolution 순서:**

테스트 파일 → 같은 폴더 conftest.py → 상위 폴더 conftest.py → 루트 conftest.py

### **Root Level (tests/conftest.py)**

* Session hooks: litellm 로깅 비활성화, marker 등록  
* test\_config, sample\_mcp\_url, sample\_endpoint\_data  
* a2a\_echo\_agent (session, subprocess, 포트 9003\)  
* a2a\_math\_agent (session, subprocess, 동적 포트)  
* mcp\_synapse\_server (session, autouse if not CI)

### **Unit Level (tests/unit/conftest.py)**

* fake\_conversation\_storage  
* fake\_endpoint\_storage  
* fake\_orchestrator  
* fake\_toolset  
* fake\_conversation\_service

### **Integration Level (tests/integration/adapters/conftest.py)**

* mock\_mcp\_toolset\_in\_ci (autouse \- CI에서 MCP mock)  
* authenticated\_client (async \- 핵심 fixture)  
  * temp\_data\_dir 생성  
  * Container 리셋 \+ storage 오버라이드  
  * LLM 모델 → openai/gpt-4o-mini  
  * Token 자동 주입  
  * Storage initialize \+ cleanup  
* mock\_mcp\_client (dict-based MCP mock)

### **Chaos Level (tests/chaos/conftest.py)**

* chaotic\_mcp\_server (async, 포트 9999\)  
* chaos\_retry\_config (단축 타임아웃)  
* container (async, direct container access)