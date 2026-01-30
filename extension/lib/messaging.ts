/**
 * Extension internal message types and type guards
 *
 * Message flow:
 *   UI → Background: START_STREAM_CHAT
 *   Background → Offscreen: STREAM_CHAT
 *   Offscreen → Background → UI: STREAM_CHAT_EVENT / DONE / ERROR
 *   UI → Background → Offscreen: CANCEL_STREAM
 */

import type { StreamEvent } from './types';

/** Message type constants */
export const MessageType = {
  START_STREAM_CHAT: 'START_STREAM_CHAT',
  STREAM_CHAT: 'STREAM_CHAT',
  STREAM_CHAT_EVENT: 'STREAM_CHAT_EVENT',
  STREAM_CHAT_DONE: 'STREAM_CHAT_DONE',
  STREAM_CHAT_ERROR: 'STREAM_CHAT_ERROR',
  CANCEL_STREAM: 'CANCEL_STREAM',
} as const;

/** UI → Background: start a chat stream */
export interface StartStreamChatMessage {
  type: typeof MessageType.START_STREAM_CHAT;
  payload: {
    conversationId: string | null;
    message: string;
  };
}

/** Background → Offscreen: execute SSE stream */
export interface StreamChatMessage {
  type: typeof MessageType.STREAM_CHAT;
  payload: {
    conversationId: string | null;
    message: string;
    requestId: string;
  };
}

/** Offscreen → Background → UI: SSE event */
export interface StreamChatEventMessage {
  type: typeof MessageType.STREAM_CHAT_EVENT;
  requestId: string;
  event: StreamEvent;
}

/** Offscreen → Background → UI: stream completed */
export interface StreamChatDoneMessage {
  type: typeof MessageType.STREAM_CHAT_DONE;
  requestId: string;
}

/** Offscreen → Background → UI: stream error */
export interface StreamChatErrorMessage {
  type: typeof MessageType.STREAM_CHAT_ERROR;
  requestId: string;
  error: string;
}

/** UI → Background → Offscreen: cancel active stream */
export interface CancelStreamMessage {
  type: typeof MessageType.CANCEL_STREAM;
  requestId: string;
}

/** Union of all extension messages */
export type ExtensionMessage =
  | StartStreamChatMessage
  | StreamChatMessage
  | StreamChatEventMessage
  | StreamChatDoneMessage
  | StreamChatErrorMessage
  | CancelStreamMessage;

// Type guard functions

export function isStreamChatEvent(
  msg: ExtensionMessage,
): msg is StreamChatEventMessage {
  return msg.type === MessageType.STREAM_CHAT_EVENT;
}

export function isStreamChatDone(
  msg: ExtensionMessage,
): msg is StreamChatDoneMessage {
  return msg.type === MessageType.STREAM_CHAT_DONE;
}

export function isStreamChatError(
  msg: ExtensionMessage,
): msg is StreamChatErrorMessage {
  return msg.type === MessageType.STREAM_CHAT_ERROR;
}

export function isCancelStream(
  msg: ExtensionMessage,
): msg is CancelStreamMessage {
  return msg.type === MessageType.CANCEL_STREAM;
}

// Factory functions

export function createStartStreamChat(
  conversationId: string | null,
  message: string,
): StartStreamChatMessage {
  return {
    type: MessageType.START_STREAM_CHAT,
    payload: { conversationId, message },
  };
}

export function createStreamChat(
  conversationId: string | null,
  message: string,
  requestId: string,
): StreamChatMessage {
  return {
    type: MessageType.STREAM_CHAT,
    payload: { conversationId, message, requestId },
  };
}

export function createCancelStream(requestId: string): CancelStreamMessage {
  return {
    type: MessageType.CANCEL_STREAM,
    requestId,
  };
}

/** Generate unique request ID for message tracking */
export function generateRequestId(): string {
  return crypto.randomUUID();
}
