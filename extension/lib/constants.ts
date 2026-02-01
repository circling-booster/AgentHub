/** AgentHub API base URL */
export const API_BASE = 'http://localhost:8000';

/** chrome.storage keys */
export const STORAGE_KEYS = {
  EXTENSION_TOKEN: 'extensionToken',
  SERVER_HEALTH: 'serverHealth',
} as const;

/** Health check interval in minutes (0.5 = 30 seconds) */
export const HEALTH_CHECK_INTERVAL_MINUTES = 0.5;

/** Offscreen document path (WXT compiles entrypoints/offscreen/index.html → offscreen.html) */
export const OFFSCREEN_DOCUMENT_PATH = 'offscreen.html';

/**
 * Error Code Constants
 *
 * Backend (src/domain/constants.py)와 동일한 값을 사용하여 타입 안전성을 보장합니다.
 * Step 0: Part B - Error Code Constants
 */
export enum ErrorCode {
  // LLM 관련 에러
  LLM_RATE_LIMIT = "LlmRateLimitError",
  LLM_AUTHENTICATION = "LlmAuthenticationError",

  // Endpoint 관련 에러
  ENDPOINT_CONNECTION = "EndpointConnectionError",
  ENDPOINT_TIMEOUT = "EndpointTimeoutError",
  ENDPOINT_NOT_FOUND = "EndpointNotFoundError",

  // Tool 관련 에러
  TOOL_NOT_FOUND = "ToolNotFoundError",

  // Conversation 관련 에러
  CONVERSATION_NOT_FOUND = "ConversationNotFoundError",

  // Validation 관련 에러
  INVALID_URL = "InvalidUrlError",

  // 기타
  UNKNOWN = "UnknownError",
}
