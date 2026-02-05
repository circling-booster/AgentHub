# Project Management

프로젝트 거버넌스, 계획, 의사결정 기록을 위한 허브입니다.

---

## Sections

| Section | Description | Contents |
|---------|-------------|----------|
| [archive/](archive/) | 완료/폐기된 문서 | Phase 문서, 폐기된 접근법, 분석 보고서 |
| [decisions/](decisions/) | ADR (Architecture Decision Records) | 아키텍처 의사결정 기록 |
| [planning/](planning/) | 로드맵 및 계획 | Phase별 계획, 마일스톤 |

---

## Contributing

### Development Process

1. **Feature Branch** 생성 (`feature/<name>`)
2. 코드 작성 + TDD (테스트 먼저)
3. PR 생성 (GitHub Actions CI 자동 실행)
4. Code Review 후 Merge

### Code Review Checklist

- [ ] 도메인 레이어에 외부 의존성 없음
- [ ] 테스트 커버리지 80% 이상 유지
- [ ] Fake Adapter 패턴 사용 (Mock 지양)
- [ ] 타입 힌트 및 docstring 포함
- [ ] ruff check/format 통과

---

## Project Status

현재 프로젝트 진행 상황:

- **Current Phase:** Phase 6 (Production Observability)
- **Test Coverage:** 89.90%
- **Build Status:** Passing

자세한 상태는 [planning/](planning/)에서 확인하세요.

---

## Quick Links

- [Root README](../../README.md) - 프로젝트 개요
- [Developer Docs](../developers/) - 개발자 가이드
- [Operator Docs](../operators/) - 운영자 가이드

---

*Last Updated: 2026-02-05*
