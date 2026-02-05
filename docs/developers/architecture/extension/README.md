# Extension Architecture

Chrome Extension 아키텍처 설계 문서입니다 (Manifest V3).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Chrome Extension                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌───────────────┐         ┌───────────────────────────┐   │
│   │    Popup      │         │        Sidepanel          │   │
│   │  (Quick UI)   │         │    (Main Chat UI)         │   │
│   └───────┬───────┘         └─────────────┬─────────────┘   │
│           │                               │                  │
│           └───────────┬───────────────────┘                  │
│                       │ chrome.runtime.sendMessage           │
│                       ↓                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Background (Service Worker)             │   │
│   │         - Token Management                           │   │
│   │         - Message Routing                            │   │
│   │         - Lifecycle Events                           │   │
│   └────────────────────────┬────────────────────────────┘   │
│                            │ message                         │
│                            ↓                                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           Offscreen Document (Hidden)                │   │
│   │         - SSE Connection                             │   │
│   │         - HTTP Requests                              │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP REST + SSE
                            ↓
                   ┌─────────────────┐
                   │  AgentHub API   │
                   │  (localhost)    │
                   └─────────────────┘
```

---

## Component Responsibilities

### Background (Service Worker)

| 역할 | 설명 |
|------|------|
| **Token 관리** | Handshake로 받은 토큰 저장/조회 |
| **Message 라우팅** | 컴포넌트 간 메시지 전달 |
| **Lifecycle 이벤트** | 설치, 업데이트, 시작 처리 |
| **Offscreen 관리** | Offscreen Document 생성/유지 |

**특징:**
- Service Worker로 실행 (Manifest V3)
- 비활성 시 종료되므로 상태는 chrome.storage에 저장
- DOM 접근 불가

### Offscreen Document

| 역할 | 설명 |
|------|------|
| **SSE 처리** | EventSource로 스트리밍 수신 |
| **HTTP 요청** | REST API 호출 |
| **DOM 의존 작업** | Service Worker에서 불가능한 작업 수행 |

**필요성:**
- Manifest V3의 Service Worker는 EventSource 미지원
- Background에서 직접 SSE 연결 불가
- Offscreen Document가 SSE 프록시 역할 수행

### Sidepanel

| 역할 | 설명 |
|------|------|
| **메인 UI** | 채팅 인터페이스 (React) |
| **대화 표시** | 메시지 렌더링, 스트리밍 표시 |
| **MCP/A2A 관리** | 서버/에이전트 등록 UI |

**특징:**
- React + CSS 기반 UI
- Background와 메시지로 통신
- 브라우저 사이드바에 표시

### Popup

| 역할 | 설명 |
|------|------|
| **빠른 액세스** | Extension 아이콘 클릭 시 표시 |
| **연결 상태** | 서버 연결 상태 표시 |
| **Sidepanel 열기** | 메인 UI로 이동 |

---

## Communication Flow

### Message Passing

```
Sidepanel/Popup ──chrome.runtime.sendMessage──▶ Background
                                                    │
Background ──chrome.runtime.sendMessage──▶ Offscreen
                                                    │
Offscreen ──HTTP/SSE──▶ AgentHub API
                                                    │
                  ◀──SSE events──
                                                    │
Offscreen ──chrome.runtime.sendMessage──▶ Background
                                                    │
Background ──chrome.runtime.sendMessage──▶ Sidepanel
```

### Message Types

| 타입 | 방향 | 설명 |
|------|------|------|
| `CHAT_REQUEST` | Sidepanel → Background | 채팅 요청 |
| `START_SSE` | Background → Offscreen | SSE 연결 시작 |
| `SSE_EVENT` | Offscreen → Background | SSE 이벤트 수신 |
| `UPDATE_UI` | Background → Sidepanel | UI 업데이트 |

---

## Service Worker Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Inactive  │────▶│   Starting  │────▶│   Active    │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                                       │
       │                                       │ (타임아웃)
       └───────────────────────────────────────┘
```

### 주의사항

| 항목 | 설명 |
|------|------|
| **자동 종료** | 30초 비활성 시 Service Worker 종료 |
| **상태 저장** | chrome.storage 사용 (메모리 변수 X) |
| **재시작** | 이벤트 발생 시 자동 재시작 |
| **초기화** | onStartup, onInstalled 이벤트 처리 |

---

## File Structure

```
extension/
├── entrypoints/
│   ├── background.ts       # Service Worker
│   ├── content.ts          # Content Script (미사용)
│   ├── offscreen/
│   │   ├── index.html      # Offscreen Document HTML
│   │   └── main.ts         # SSE/HTTP 처리 로직
│   └── sidepanel/
│       ├── index.html      # Sidepanel HTML
│       ├── main.tsx        # React 엔트리포인트
│       ├── App.tsx         # 메인 컴포넌트
│       └── App.css         # 스타일
├── lib/
│   ├── api.ts              # REST API 클라이언트
│   ├── sse.ts              # SSE 클라이언트
│   └── types.ts            # TypeScript 타입
└── wxt.config.ts           # WXT 설정
```

---

## Security Model

### Content Security Policy

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### Permissions

| 권한 | 용도 |
|------|------|
| `storage` | Token, 설정 저장 |
| `sidePanel` | 사이드패널 표시 |
| `offscreen` | Offscreen Document 생성 |

### Host Permissions

```json
{
  "host_permissions": ["http://localhost:8000/*"]
}
```

---

*Last Updated: 2026-02-05*
