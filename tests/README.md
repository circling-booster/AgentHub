# **AgentHub Tests**

TDD \+ 헥사고날 아키텍처 기반 테스트 전략을 위한 가이드 문서입니다.

## **📋 Quick Reference**

| 항목 | 값 |
| :---- | :---- |
| **pytest 설정** | pyproject.toml \[tool.pytest.ini\_options\] |
| **Coverage 설정** | .coveragerc (pyproject.toml보다 우선) |
| **anyio 모드** | auto (@pytest.mark.asyncio 불필요, anyio plugin 사용) |
| **기본 제외 마커** | llm, e2e\_playwright, local\_mcp, local\_a2a, chaos |
| **Import 표준** | from src.domain... (src. 접두사 사용) |
| **Import 검증** | pytest tests/integration/test\_app\_startup.py::TestImportValidation |
| **Fake Adapter 위치** | tests/unit/fakes/ |
| **최소 커버리지** | 80% (CI 강제, 현재: 86.84%) |
| **테스트 수 확인** | pytest \--co \-q |
| **Playground (JS) 테스트** | cd tests/manual/playground && npm test |

## **📚 Documentation Index**

상세한 내용은 아래 문서들을 참조하세요 (tests/docs/ 디렉토리).

| 문서 | 내용 |
| :---- | :---- |
| **[🏗️ Structure](docs/STRUCTURE.md)** | 디렉토리 구조, Fixture 계층 및 범위 |
| [**🧪 Strategy**](docs/STRATEGY.md) | 테스트 피라미드, 격리 전략, 헥사고날 아키텍처, Mock vs Fake |
| [**📝 Writing Guide**](docs/WritingGuide.md) | **필독.** 테스트 작성 레시피, Import 검증, 함정, 네이밍 규칙 |
| [**🔧 Configuration**](docs/CONFIGURATION.md) | 포트 할당, pytest 마커/옵션, 커버리지, Async 설정 |
| [**🚀 Execution & CI**](docs/EXECUTION.md) | 테스트 실행 명령어, CI/CD 파이프라인, 회귀 방지 |
| [**🐛 Troubleshooting**](docs/TROUBLESHOOTING.md) | 자주 발생하는 오류 및 해결 방법 |
| [**📊 Resources**](docs/RESOURCES.md) | MCP 서버 정보, A2A 에이전트, 참고 문헌 |

*Last Updated: 2026-02-02*

*Version: 3.1 (Refactored to /docs)*