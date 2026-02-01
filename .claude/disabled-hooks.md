# Disabled Hooks Reference

이 파일은 비활성화된 Hooks 설정을 보관합니다. 필요 시 `.claude/settings.json`에 복사하여 사용하세요.

## Stop Hook (현재 비활성화)

```json
"Stop": [
  {
    "matcher": "",
    "hooks": [
      {
        "type": "command",
        "description": "Quick unit test validation",
        "command": "pytest tests/unit/ -q --tb=line -x 2>&1 | head -20"
      }
    ]
  }
]
```

### 활성화 방법

1. 위 JSON 블록을 복사
2. `.claude/settings.json` 열기
3. `"Stop": []`를 위 내용으로 교체
4. 파일 저장

### 비활성화 이유

- Phase 0-2.5 단계에서는 개발 속도 우선
- 컨텍스트 절약 (Stop Hook 실행 출력 제거)
- PostToolUse로 인한 과도한 Hook 실행 방지

### 재활성화 권장 시점

- Phase 3+ (안정화 단계)
- 테스트 실패율이 높아질 때
- CI/CD 파이프라인 준비 시
