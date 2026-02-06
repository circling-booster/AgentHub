/**
 * TDD Step 5.3: Red Phase
 * sse-handler.js 테스트 먼저 작성
 */

import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';

describe("SSE Handler", () => {
    let mockEventSource;

    beforeEach(() => {
        // Mock EventSource
        mockEventSource = {
            onmessage: null,
            onerror: null,
            close: jest.fn(),
            readyState: 0
        };

        global.EventSource = jest.fn(() => mockEventSource);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe("SseHandler", () => {
        test("Red: creates EventSource with correct URL", async () => {
            // Given: SSE Handler (아직 구현 안됨!)
            const { SseHandler } = await import("../js/sse-handler.js");

            const onMessage = jest.fn();
            const onError = jest.fn();
            const onDone = jest.fn();

            // When: connect 호출
            const handler = new SseHandler(
                "http://localhost:8000/api/chat/stream",
                onMessage,
                onError,
                onDone
            );
            handler.connect();

            // Then: EventSource 생성 확인
            expect(global.EventSource).toHaveBeenCalledWith(
                "http://localhost:8000/api/chat/stream"
            );
        });

        test("Red: onMessage callback triggered on event", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onMessage = jest.fn();
            const handler = new SseHandler("http://test", onMessage, jest.fn(), jest.fn());
            handler.connect();

            // When: 메시지 수신
            const event = {
                data: JSON.stringify({ type: "text", content: "Hello" })
            };
            mockEventSource.onmessage(event);

            // Then: 콜백 호출 확인
            expect(onMessage).toHaveBeenCalledWith({
                type: "text",
                content: "Hello"
            });
        });

        test("Red: disconnect closes EventSource", async () => {
            // Given: 연결된 Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const handler = new SseHandler("http://test", jest.fn(), jest.fn(), jest.fn());
            handler.connect();

            // When: disconnect 호출
            handler.disconnect();

            // Then: EventSource.close 호출
            expect(mockEventSource.close).toHaveBeenCalled();
        });

        test("Red: onDone called and disconnects when type is 'done'", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onDone = jest.fn();
            const handler = new SseHandler("http://test", jest.fn(), jest.fn(), onDone);
            handler.connect();

            // When: 'done' 이벤트 수신
            const event = {
                data: JSON.stringify({ type: "done" })
            };
            mockEventSource.onmessage(event);

            // Then: onDone 호출 및 연결 종료
            expect(onDone).toHaveBeenCalled();
            expect(mockEventSource.close).toHaveBeenCalled();
        });

        test("Red: onError callback triggered on error", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onError = jest.fn();
            const handler = new SseHandler("http://test", jest.fn(), onError, jest.fn());
            handler.connect();

            // When: 에러 발생
            const error = new Error("Connection failed");
            mockEventSource.onerror(error);

            // Then: onError 호출 및 연결 종료
            expect(onError).toHaveBeenCalledWith(error);
            expect(mockEventSource.close).toHaveBeenCalled();
        });
    });
});
