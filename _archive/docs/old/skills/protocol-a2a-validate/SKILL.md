---
name: a2a-validate
description: A2A Agent Card의 스키마 유효성을 검증합니다. Agent Card 작성 후 검증 시 사용하세요.
argument-hint: <agent-card-file>
---

# A2A Agent Card 검증

파일: `$ARGUMENTS`

## 검증 항목

### 1. 필수 필드
- [ ] name: 문자열, 비어있지 않음
- [ ] description: 문자열
- [ ] skills: 배열, 최소 1개

### 2. Skills 검증
각 skill에 대해:
- [ ] id: 고유 식별자
- [ ] name: 스킬 이름
- [ ] description: 설명
- [ ] inputSchema: JSON Schema 형식

### 3. Endpoints 검증
- [ ] base URL 형식 유효성
- [ ] HTTPS 권장

### 4. 스키마 검증
```bash
# JSON Schema 검증 (ajv 사용 시)
ajv validate -s a2a-schema.json -d agent-card.json
```

## 출력 형식

```markdown
## Agent Card 검증 결과

### 파일
[파일 경로]

### 결과
✅ 유효 / ❌ 무효

### 이슈
1. [이슈 설명]

### 권장사항
- [개선 제안]
```
