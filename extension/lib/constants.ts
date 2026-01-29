/** AgentHub API base URL */
export const API_BASE = 'http://localhost:8000';

/** chrome.storage keys */
export const STORAGE_KEYS = {
  EXTENSION_TOKEN: 'extensionToken',
  SERVER_HEALTH: 'serverHealth',
} as const;

/** Health check interval in minutes (0.5 = 30 seconds) */
export const HEALTH_CHECK_INTERVAL_MINUTES = 0.5;

/** Offscreen document path */
export const OFFSCREEN_DOCUMENT_PATH = 'offscreen/index.html';
