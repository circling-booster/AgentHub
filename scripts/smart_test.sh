#!/bin/bash
# AgentHub Smart Test Runner
# 변경된 파일 기반 테스트 범위 자동 조정

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 변경된 Python 파일 확인
CHANGED_FILES=$(git diff --name-only --cached | grep -E '\.py$' || true)

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}No Python files changed. Skipping tests.${NC}"
    exit 0
fi

# 변경 파일 개수
FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)

echo -e "${GREEN}Changed files: $FILE_COUNT${NC}"
echo "$CHANGED_FILES" | head -5
[ $FILE_COUNT -gt 5 ] && echo "..."

# src/ 변경 여부 확인
SRC_CHANGED=$(echo "$CHANGED_FILES" | grep -E '^src/' || true)

if [ -n "$SRC_CHANGED" ]; then
    # src/ 변경 시: 전체 테스트 (출력 최소화)
    echo -e "${YELLOW}src/ changed - Running full test suite (minimal output)${NC}"

    pytest tests/ \
        --cov=src \
        --cov-fail-under=80 \
        --cov-report=term-missing:skip-covered \
        -q \
        --tb=line \
        2>&1 | grep -E '^(tests/|PASSED|FAILED|ERROR|====|coverage:|TOTAL)' | head -50

    EXIT_CODE=${PIPESTATUS[0]}

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed with coverage >= 80%${NC}"
    else
        echo -e "${RED}✗ Tests failed or coverage < 80%${NC}"
        exit $EXIT_CODE
    fi
else
    # tests/ 또는 docs/ 변경 시: 관련 테스트만
    echo -e "${YELLOW}Non-src changes - Running related tests only${NC}"

    # 변경된 테스트 파일만 실행
    TEST_FILES=$(echo "$CHANGED_FILES" | grep -E '^tests/.*\.py$' || true)

    if [ -n "$TEST_FILES" ]; then
        pytest $TEST_FILES -q --tb=line 2>&1 | head -30
        EXIT_CODE=${PIPESTATUS[0]}

        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}✓ Related tests passed${NC}"
        else
            echo -e "${RED}✗ Tests failed${NC}"
            exit $EXIT_CODE
        fi
    else
        echo -e "${GREEN}No test files changed - skipping${NC}"
    fi
fi
