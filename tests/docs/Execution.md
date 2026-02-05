# **🚀 Running Tests & CI/CD**

## **🚀 Running Tests**

### **기본 명령어**

\# 전체 테스트 (LLM, Chaos, E2E 제외)  
pytest

\# 빠른 실패 감지 (첫 실패 시 중단)  
pytest \-x

\# Verbose 모드  
pytest \-v

\# Quiet 모드 (Token 절약 \- Claude Code 권장)  
pytest \-q \--tb=line \-x

### **타겟 실행**

\# 특정 파일  
pytest tests/unit/domain/services/test\_conversation\_service.py

\# 특정 테스트  
pytest tests/unit/domain/services/test\_conversation\_service.py::test\_send\_message

\# 특정 디렉토리  
pytest tests/unit/

### **고급 명령어**

\# LLM 테스트 포함  
pytest \--run-llm \-v

\# 커버리지 리포트  
pytest \--cov=src \--cov-report=html

\# 병렬 실행 (pytest-xdist)  
pytest \-n auto

\# 테스트 수 확인 (실행 없이)  
pytest \--co \-q

## **🔄 Regression Prevention Strategy**

### **1\. 실패한 테스트 재실행**

\# 마지막으로 실패한 테스트만 실행  
pytest \--lf \-v

\# 실패한 테스트 먼저 실행 후 나머지 실행  
pytest \--ff \-v

### **2\. 커버리지 회귀 감지**

\# 커버리지 80% 미만 시 실패  
pytest \--cov=src \--cov-fail-under=80

* Phase 1 목표: 80%  
* Phase 4+ 목표: 90%

## **🌐 CI/CD Pipeline**

### **GitHub Actions (.github/workflows/ci.yml)**

name: Tests  
on: \[push, pull\_request\]

jobs:  
  test:  
    runs-on: ubuntu-latest  
    steps:  
      \- uses: actions/checkout@v3  
      \- uses: actions/setup-python@v4  
        with:  
          python-version: '3.11'  
      \- name: Install dependencies  
        run: pip install \-e ".\[dev\]"  
      \- name: Run tests with coverage  
        run: |  
          pytest \--cov=src \--cov-fail-under=80 \--cov-report=xml  
      \- name: Upload coverage  
        uses: codecov/codecov-action@v3  
