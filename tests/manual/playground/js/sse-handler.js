/**
 * TDD Step 5.4: Green Phase
 * SSE Handler 모듈 - 최소 구현
 */

export class SseHandler {
    constructor(url, onMessage, onError, onDone) {
        this.url = url;
        this.onMessage = onMessage;
        this.onError = onError;
        this.onDone = onDone;
        this.eventSource = null;
    }

    connect() {
        this.eventSource = new EventSource(this.url);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.onMessage(data);

                if (data.type === "done") {
                    this.disconnect();
                    this.onDone();
                }
            } catch (error) {
                console.error("Failed to parse SSE event:", error);
            }
        };

        this.eventSource.onerror = (error) => {
            this.onError(error);
            this.disconnect();
        };
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    isConnected() {
        return this.eventSource !== null && this.eventSource.readyState === 1;
    }
}
