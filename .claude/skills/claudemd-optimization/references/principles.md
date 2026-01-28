# CLAUDE.md 최적화 원칙 상세

## 목차

1. [Less Is More](#less-is-more)
2. [3차원 프레임워크](#3차원-프레임워크)
3. [Progressive Disclosure](#progressive-disclosure)
4. [LLM 주의력 분배](#llm-주의력-분배)
5. [강조 기법](#강조-기법)
6. [린터가 아님](#린터가-아님)

---

## Less Is More

### 연구 기반 데이터

| 지표 | 값 | 의미 |
|------|-----|------|
| Frontier LLM 명령어 한계 | ~150-200개 | 초과 시 준수율 저하 |
| Claude Code 시스템 프롬프트 | ~50개 명령어 | 이미 소비됨 |
| **가용 예산** | **~100-150개** | 모든 줄이 중요 |

### 핵심 인사이트

명령어 수가 증가하면 준수 품질이 **모든 명령어에 걸쳐 균일하게** 저하됨 - 나중 명령어만 영향받는 게 아님. 비대한 CLAUDE.md는 가장 중요한 규칙의 효과도 떨어뜨림.

### 모델 크기별 차이

| 모델 유형 | 저하 패턴 |
|----------|----------|
| Frontier thinking 모델 | 선형 저하 (점진적) |
| 소형 모델 | 지수적 저하 (급격) |

⚠️ 복잡한 계획이나 다단계 작업에는 소형 모델 사용 자제

---

## 3차원 프레임워크

모든 CLAUDE.md는 정확히 세 가지 차원을 커버해야 함:

| 차원 | 내용 | 예시 |
|------|------|------|
| **WHAT** | 기술 스택, 아키텍처, 코드베이스 구조 | "React + Bun monorepo, 5개 플러그인" |
| **WHY** | 프로젝트 목적, 각 컴포넌트 역할 | "Frontend 플러그인이 UI 개발 담당" |
| **HOW** | 빌드 도구, 검증, 테스트, 워크플로우 | "`bun test` 실행, `/implement` 명령 사용" |

---

## Progressive Disclosure

### 원칙

모든 것을 CLAUDE.md에 넣지 말고, 포인터만 유지.

### 구현 방법

```
docs/  (또는 agent_docs/)
├── commands-and-agents.md    # 상세 명령어/에이전트 참조
├── architecture-guide.md     # 심층 아키텍처 문서
├── api-patterns.md           # API 컨벤션과 예시
├── testing-strategy.md       # 테스트 접근법
└── release-process.md        # 릴리스 워크플로우 상세
```

### CLAUDE.md에서의 참조 방식

```markdown
## 상세 문서

| 주제 | 참조 |
|------|------|
| 명령어 | [docs/commands-and-agents.md](docs/commands-and-agents.md) |
| 아키텍처 | [docs/architecture-guide.md](docs/architecture-guide.md) |
```

---

## LLM 주의력 분배

LLM은 컨텍스트의 **주변부**에 편향됨:

```
┌─────────────────────────────────────────────────────┐
│  높은 주의력                                         │
│  ├── 시스템 프롬프트 (Claude Code)                  │
│  └── CLAUDE.md (시작 부분)                          │
├─────────────────────────────────────────────────────┤
│  낮은 주의력                                         │
│  └── 컨텍스트 윈도우 중간                            │
├─────────────────────────────────────────────────────┤
│  높은 주의력                                         │
│  └── 최근 사용자 메시지 (끝)                         │
└─────────────────────────────────────────────────────┘
```

**시사점**: 가장 중요한 규칙은 CLAUDE.md **상단**에 배치. 중간에 묻히면 안 됨.

---

## 강조 기법

### 공식 권장 (Anthropic)

Claude가 반드시 따라야 하는 규칙에는 강조 표현 사용:

| 표현 | 용도 |
|------|------|
| `IMPORTANT:` | 중요한 규칙 강조 |
| `YOU MUST` | 필수 준수 사항 |
| `NEVER` | 절대 하지 말아야 할 것 |
| `ALWAYS` | 항상 해야 할 것 |

### 사용 예시

```markdown
IMPORTANT: 프로덕션 브랜치에 직접 푸시하지 마세요.
YOU MUST run tests before committing.
NEVER commit .env files.
ALWAYS verify API patterns against official documentation.
```

### 주의사항

- 과도한 사용 금지: 모든 규칙에 강조하면 효과 감소
- 진짜 중요한 3-5개 규칙에만 적용
- 강조 없이도 준수되는 규칙은 일반 텍스트로

---

## 린터가 아님

### 하지 말 것

CLAUDE.md에 스타일 규칙 넣지 말 것:
- ❌ "2칸 들여쓰기 사용"
- ❌ "항상 세미콜론 사용"
- ❌ "let보다 const 선호"

### 대신

- Biome/ESLint/Prettier로 포매팅
- Claude는 기존 코드 패턴에서 학습 (인컨텍스트 러닝)
- 잘 구조화된 코드가 컨벤션을 보여줌

### 고급 기법: Stop Hook

Claude 작업 완료 후 포매터 실행하도록 Stop Hook 설정:

```json
// .claude/settings.local.json
{
  "hooks": {
    "PostToolExecution": [{
      "type": "command",
      "command": "biome check --fix --unsafe $FILE"
    }]
  }
}
```

구현과 포매팅 분리 → **둘 다 품질 향상**
