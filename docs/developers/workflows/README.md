# Development Workflows

AgentHub 개발 워크플로우 문서입니다.

---

## Git Workflow

### Branch Strategy

```
main (protected)
  │
  ├── feature/phase-6-partA    ← 현재 작업
  ├── feature/phase-6-partB
  ├── fix/token-validation
  └── refactor/storage-layer
```

| 브랜치 | 용도 | 보호 |
|--------|------|------|
| `main` | 프로덕션 릴리즈 | Protected (직접 커밋 금지) |
| `feature/*` | 새 기능 개발 | - |
| `fix/*` | 버그 수정 | - |
| `refactor/*` | 리팩토링 | - |

### Branch Protection Rules

- `main` 브랜치 직접 push 금지
- PR 필수 (CI 통과 후 머지)
- Pre-commit hook으로 로컬 검증

---

## Commit Guidelines

### Conventional Commits

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

| Type | 용도 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `docs` | 문서 변경 |
| `chore` | 빌드, 설정 등 |

**Examples:**

```
feat(phase6): add circuit breaker entity
fix(storage): resolve SQLite WAL deadlock
test(unit): add FakeUsageStorage tests
docs(architecture): update system diagram
```

---

## Automation Hooks

AgentHub는 Claude Code hooks를 통한 자동화를 사용합니다.

### Hook Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Development Flow                          │
└──────────────────────────────────────────────────────────────┘

[코드 수정] ─────────────────────────────────────────────────────►
     │
     ▼ PostToolUse Hook
┌─────────────────────────────────┐
│  ruff check --fix               │  ← 린트 자동 수정
│  ruff format                    │  ← 코드 포맷팅
└─────────────────────────────────┘
     │
     ▼
[Claude 응답 완료] ──────────────────────────────────────────────►
     │
     ▼ Stop Hook
┌─────────────────────────────────┐
│  pytest tests/unit/ -q          │  ← Unit 테스트
└─────────────────────────────────┘
     │
     ▼
[commit/pr/push 명령] ──────────────────────────────────────────►
     │
     ▼ UserPromptSubmit Hook
┌─────────────────────────────────┐
│  pytest --cov=src               │  ← 전체 테스트 + 커버리지
│  --cov-fail-under=80            │  ← 80% 미만 시 실패
└─────────────────────────────────┘
```

### Hook Configuration

Hook 설정 위치: [.claude/settings.local.json](../../../.claude/settings.local.json)

---

## CI/CD Pipeline

### GitHub Actions Workflow

| Job | 실행 조건 | 내용 |
|-----|----------|------|
| `test` | push, PR to main | Python 3.10/3.11/3.12 테스트 |
| `type-check` | push, PR to main | mypy 타입 체크 |

### CI Pipeline Steps

```yaml
# .github/workflows/ci.yml
1. Checkout
2. Setup Python (matrix: 3.10, 3.11, 3.12)
3. Install dependencies
4. Lint with ruff
   - ruff check src/ tests/
   - ruff format --check src/ tests/
5. Run tests with coverage
   - pytest --cov=src --cov-fail-under=80
6. Upload coverage to Codecov
7. Type check (mypy)
```

### PR Merge Requirements

- [ ] CI 통과 (모든 Python 버전)
- [ ] 커버리지 80% 이상
- [ ] ruff 린트/포맷 통과
- [ ] 타입 체크 통과 (warning 허용)

---

## Local Development Flow

### Daily Workflow

```bash
# 1. 브랜치 생성
git checkout -b feature/my-feature

# 2. 개발 (TDD)
#    - 테스트 작성 (Red)
#    - 구현 (Green)
#    - 리팩토링 (Refactor)

# 3. 로컬 검증
pytest -q --tb=line -x           # 빠른 실패 확인
ruff check --fix src/ tests/     # 린트 수정
ruff format src/ tests/          # 포맷팅

# 4. 커밋
git add <files>
git commit -m "feat(scope): description"

# 5. PR 생성
gh pr create --title "feat: description" --body "..."
```

### Running the Server

```bash
# 개발 모드 (auto-reload)
uvicorn src.main:app --host localhost --port 8000 --reload

# 프로덕션 모드
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Extension Development

```bash
cd extension

# 개발 모드 (HMR)
npm run dev

# 빌드
npm run build

# 타입 체크
npm run typecheck
```

---

## Code Quality Tools

| 도구 | 용도 | 명령어 |
|------|------|--------|
| **ruff** | 린트 + 포맷 | `ruff check --fix && ruff format` |
| **mypy** | 타입 체크 | `mypy src/` |
| **pytest** | 테스트 | `pytest --cov=src` |
| **pre-commit** | Git hooks | 자동 실행 |

---

## Related Documentation

- **테스트 전략**: [testing/](../testing/) - TDD, Fake Adapter
- **아키텍처**: [architecture/](../architecture/) - 시스템 구조
- **CI 설정**: [.github/workflows/ci.yml](../../../.github/workflows/ci.yml)

---

*Last Updated: 2026-02-05*
