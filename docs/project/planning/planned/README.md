# Planned Plans

예정된 Plan 초안 문서입니다.

---

## 📋 Planned Plans

| Plan | 제목 | 요약 | 예상 기간 | 의존성 |
|------|------|------|----------|--------|
| **09** | Dynamic Configuration & Model Management | API Key 관리 + LLM 모델 동적 선택 (Playground + Extension) | 2-3주 | Plan 07 |
| **10** | stdio Transport | stdio 프로토콜 지원 (subprocess 통신), Cross-platform 지원, Filesystem 서버 통합 | 2주 | Plan 07 |
| **11** | MCP App UI Rendering | MCP App의 실제 UI 렌더링 지원 (Playground + Extension) | 2-3주 | Plan 07 |
| **12** | Vector Search & Semantic Tool Routing | Vector Search를 활용한 Semantic Tool Routing (50+ 도구 시 자동 활성화) | 2주 | Plan 07 |
| **13** | Internationalization (i18n) | Backend + Extension 국제화 (Korean + English) | 1-2주 | Plan 07 |

---

## Plan 09: Dynamic Configuration & Model Management

**목표:** API Key 관리 + LLM 모델 동적 선택 (Playground + Extension)

**핵심 기능:**
- API Key CRUD (추가, 조회, 삭제, 테스트)
- Model Selection (LiteLLM 모델 목록 + 선택)
- Playground Settings 탭
- Fernet 암호화 (API Key 보안)
- SQLite 저장소 (새 테이블: `api_keys`, `model_configs`)

**예상 Phases:** 7개 (Domain → Port → Service → Adapter → Integration → HTTP → Validation)

**문서:** [09_dynamic_configuration.md](09_dynamic_configuration.md)

---

## Plan 10: stdio Transport

**목표:** stdio 프로토콜 지원 (subprocess 통신), Cross-platform subprocess 관리

**핵심 기능:**
- StdioConfig Domain Model (command, args, env, cwd, allowed_paths)
- Subprocess Manager (시작, 모니터링, 재시작, 정리)
- stdio Transport (stdin/stdout JSON-RPC)
- Cross-platform Support (Windows/macOS/Linux)
- Security (경로 권한 검증)
- **통합 테스트용 MCP Filesystem Server** (`@modelcontextprotocol/server-filesystem`)

**예상 Phases:** 6개 (Domain → Port → Service → Adapter → Integration → CI)

**참고 문서:** `_archive/migration/20260204/plans/phase7/backup-20260203/partB.md`

**문서:** [10_stdio_transport.md](10_stdio_transport.md)

---

## Plan 11: MCP App UI Rendering

**목표:** MCP App의 실제 UI 렌더링 지원 (Playground + Extension)

**핵심 기능:**
- McpAppUiSchema Domain Model (JSON Schema)
- McpAppUiService (UI Schema 파싱 및 변환)
- McpAppUiRenderingAdapter (Jinja2/React 렌더링)
- Playground MCP App UI Renderer 탭
- Extension MCP App UI Modal (추후)

**예상 Phases:** 7개 (Domain → Port → Service → Adapter → Integration → HTTP → E2E)

**주의:** MCP App UI Schema는 빠르게 진화하는 표준 → Plan Phase에서 웹 검색 검증 필수

**문서:** [11_mcp_app_ui_rendering.md](11_mcp_app_ui_rendering.md)

---

## Plan 12: Vector Search & Semantic Tool Routing

**목표:** Vector Search를 활용한 Semantic Tool Routing (50+ 도구 시 자동 활성화)

**핵심 기능:**
- Vector Store (ChromaDB 기반 임베딩 저장소)
- Tool Embedding Service (도구 설명 → 벡터 변환)
- Semantic Router (사용자 쿼리 → 관련 도구 검색)
- Auto Activation (도구 수 임계값 기반 자동 활성화)
- Optional Dependency (`pip install agenthub[vector]`)

**예상 Phases:** 7개 (Domain → Port → Service → Adapter → Integration → HTTP → E2E)

**참고 문서:** `_archive/migration/20260204/plans/phase6/backup-20260203/phase6.0-original.md` (Step 15)

**문서:** [12_vector_search.md](12_vector_search.md)

---

## Plan 13: Internationalization (i18n)

**목표:** Backend + Extension 국제화 (Korean + English)

**핵심 기능:**
- Backend i18n (에러 메시지, 로그, API 응답)
- Extension i18n (UI 텍스트, 알림 - react-i18next)
- Language Selection (Playground + Extension Settings)
- Fallback Strategy (번역 누락 시 영어 폴백)
- Lazy Loading (번들 크기 최적화)

**예상 Phases:** 8개 (Domain → Port → Backend Service → Backend 적용 → Extension Setup → Extension 적용 → Language Selection → E2E)

**참고 문서:** `_archive/migration/20260204/plans/phase7/backup-20260203/phase7.0-original.md` (Step 13-14)

**문서:** [13_i18n.md](13_i18n.md)

---

## 우선순위 제안

### Option A: 사용자 경험 우선
1. **Plan 09** (Dynamic Configuration) - 즉시 사용 가능한 기능
2. **Plan 10** (stdio Transport + Filesystem) - 더 많은 MCP 서버 지원
3. **Plan 13** (i18n) - 사용자 경험 향상
4. **Plan 11** (MCP App UI) - 고급 UI 기능
5. **Plan 12** (Vector Search) - 선택적 고급 기능

### Option B: 아키텍처 확장 우선
1. **Plan 10** (stdio Transport + Filesystem) - Transport layer 완성
2. **Plan 09** (Dynamic Configuration) - Configuration layer 완성
3. **Plan 11** (MCP App UI) - UI layer 확장
4. **Plan 12** (Vector Search) - Search layer 확장
5. **Plan 13** (i18n) - UX layer 완성

### Option C: 병렬 개발 (권장)
**Phase 1 (병렬):**
- Plan 09 (Dynamic Configuration)
- Plan 10 (stdio Transport + Filesystem)

**Phase 2 (선택적):**
- Plan 11 (MCP App UI)
- Plan 13 (i18n)

**Phase 3 (추후):**
- Plan 12 (Vector Search) - 선택적 고급 기능

---

## 다음 단계

1. **초안 검토**: 각 Plan 초안을 검토하여 스코프 및 Phase 구조 확인
2. **우선순위 결정**: 사용자/팀과 논의하여 우선순위 결정
3. **Plan 승인**: 선택된 Plan을 `active/`로 이동
4. **Phase 상세 계획**: 각 Phase의 상세 Step 작성
5. **구현 시작**: TDD Red-Green-Refactor 사이클로 구현

---

## Related Documents

- [Active Plans](../active/README.md) - 현재 진행 중인 Plan
- [Completed Plans](../completed/README.md) - 완료된 Plan
- [Planning Structure](../README.md) - Planning 구조 및 원칙

---

*Last Updated: 2026-02-07*
*Total Planned Plans: 5*
