# Phase 7: Polish + stdio Transport + MCP Standards

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Complete
> **목표:** Extension UX 완성, stdio 트랜스포트, MCP 필수 기능(Roots/Progress/Tasks/Registry), i18n
> **분할:** Part A-D (개별 파일)
> **예상 테스트:** ~50 신규 (backend + extension)

---

## Phase 구조

| Part | 파일 | Steps | 초점 |
|:----:|------|:-----:|------|
| A | [phase7.0-partA.md](phase7.0-partA.md) | 1-4 | Extension UX Polish |
| B | [phase7.0-partB.md](phase7.0-partB.md) | 5-8 | stdio Transport (Cross-platform) |
| C | [phase7.0-partC.md](phase7.0-partC.md) | 9-12 | MCP Required Features |
| D | [phase7.0-partD.md](phase7.0-partD.md) | 13-14 | i18n (Backend + Extension) |

---

## Step 번호 매핑

| Step | Title | Part |
|:----:|-------|:----:|
| 1 | Markdown Preview Enhancement | A |
| 2 | Export/Import Configuration | A |
| 3 | Conversation Management UI | A |
| 4 | Cost/Budget Dashboard UI | A |
| 5 | StdioConfig Domain Model | B |
| 6 | Subprocess Manager (Cross-platform) | B |
| 7 | stdio MCP Integration | B |
| 8 | Cross-platform CI | B |
| 9 | Roots (Filesystem Scoping) | C |
| 10 | Progress Notifications | C |
| 11 | Tasks (Long-Running Operations) | C |
| 12 | MCP Registry Integration | C |
| 13 | Backend i18n | D |
| 14 | Extension i18n | D |

---

## 전체 실행 순서 및 의존성

```
Part A (UX Polish) ─── 독립 (언제든 시작 가능)
Part B (stdio) ─── 독립 (언제든 시작 가능)
Part C (MCP Standards) ─── Phase 6 Part B 이후 (McpClientPort 필요)
Part D (i18n) ─── 독립 (언제든 시작 가능)
```

**병렬화 옵션:** Part A + B + D 모두 병렬 실행 가능. Part C만 Phase 6B 의존.

---

## Phase 7 Definition of Done

### 기능

- [ ] Markdown 테이블/이미지/코드 블록 정상 렌더링
- [ ] 설정 Export/Import JSON 동작
- [ ] 대화 목록/히스토리 관리 UI 동작
- [ ] Cost Dashboard 차트 표시
- [ ] stdio MCP 서버 등록 + 도구 호출 동작 (Windows/macOS/Linux)
- [ ] Subprocess 크래시 재시작 + 좀비 방지 검증
- [ ] 3-OS CI 매트릭스 통과
- [ ] MCP Roots: 서버에 filesystem roots 전달
- [ ] MCP Progress: 진행률 UI 표시
- [ ] MCP Tasks: 취소/재개 UI 동작
- [ ] MCP Registry: 서버 검색 UI 동작
- [ ] Korean + English i18n 완료

### 품질

- [ ] Backend coverage >= 90%
- [ ] Extension tests updated
- [ ] Cross-platform CI green (3-OS)
- [ ] TDD Red-Green-Refactor 사이클 준수

### 문서

- [ ] `docs/STATUS.md` 업데이트
- [ ] `docs/roadmap.md` Phase 7 상태 반영
- [ ] `extension/README.md` 새 기능 반영

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| stdio subprocess 크로스플랫폼 차이 | 🟡 | `pathlib.Path`, `shlex`/`subprocess.list2cmdline` 분기 |
| Windows 프로세스 관리 특수성 | 🟡 | `ctypes` + `CREATE_NEW_PROCESS_GROUP` 활용 |
| MCP Registry API 변경 | 🟡 | 웹 검색으로 최신 스펙 확인 |
| react-i18next 번들 크기 | 🟢 | lazy loading으로 경량화 |

---

*Phase 7 계획 작성일: 2026-01-31*
