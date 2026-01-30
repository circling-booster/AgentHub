import { describe, it, expect } from 'vitest';
import {
  MessageType,
  isStreamChatEvent,
  isStreamChatDone,
  isStreamChatError,
  isCancelStream,
  createStartStreamChat,
  createStreamChat,
  createCancelStream,
} from '../../lib/messaging';
import type { ExtensionMessage } from '../../lib/messaging';

describe('MessageType constants', () => {
  it('should define all required message types', () => {
    expect(MessageType.START_STREAM_CHAT).toBe('START_STREAM_CHAT');
    expect(MessageType.STREAM_CHAT).toBe('STREAM_CHAT');
    expect(MessageType.STREAM_CHAT_EVENT).toBe('STREAM_CHAT_EVENT');
    expect(MessageType.STREAM_CHAT_DONE).toBe('STREAM_CHAT_DONE');
    expect(MessageType.STREAM_CHAT_ERROR).toBe('STREAM_CHAT_ERROR');
    expect(MessageType.CANCEL_STREAM).toBe('CANCEL_STREAM');
  });
});

describe('Type guard functions', () => {
  describe('isStreamChatEvent', () => {
    it('should return true for STREAM_CHAT_EVENT messages', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_EVENT,
        requestId: 'req-1',
        event: { type: 'text', content: 'Hello' },
      };
      expect(isStreamChatEvent(msg)).toBe(true);
    });

    it('should return false for other message types', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_DONE,
        requestId: 'req-1',
      };
      expect(isStreamChatEvent(msg)).toBe(false);
    });
  });

  describe('isStreamChatDone', () => {
    it('should return true for STREAM_CHAT_DONE messages', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_DONE,
        requestId: 'req-1',
      };
      expect(isStreamChatDone(msg)).toBe(true);
    });

    it('should return false for other message types', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_EVENT,
        requestId: 'req-1',
        event: { type: 'text', content: 'Hi' },
      };
      expect(isStreamChatDone(msg)).toBe(false);
    });
  });

  describe('isStreamChatError', () => {
    it('should return true for STREAM_CHAT_ERROR messages', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_ERROR,
        requestId: 'req-1',
        error: 'Something went wrong',
      };
      expect(isStreamChatError(msg)).toBe(true);
    });

    it('should return false for other message types', () => {
      const msg: ExtensionMessage = {
        type: MessageType.STREAM_CHAT_DONE,
        requestId: 'req-1',
      };
      expect(isStreamChatError(msg)).toBe(false);
    });
  });

  describe('isCancelStream', () => {
    it('should return true for CANCEL_STREAM messages', () => {
      const msg: ExtensionMessage = {
        type: MessageType.CANCEL_STREAM,
        requestId: 'req-1',
      };
      expect(isCancelStream(msg)).toBe(true);
    });
  });
});

describe('Message factory functions', () => {
  describe('createStartStreamChat', () => {
    it('should create START_STREAM_CHAT message with conversationId and message', () => {
      const msg = createStartStreamChat('conv-1', 'Hello');
      expect(msg.type).toBe(MessageType.START_STREAM_CHAT);
      expect(msg.payload.conversationId).toBe('conv-1');
      expect(msg.payload.message).toBe('Hello');
    });

    it('should allow null conversationId for new conversations', () => {
      const msg = createStartStreamChat(null, 'Hello');
      expect(msg.payload.conversationId).toBeNull();
    });
  });

  describe('createStreamChat', () => {
    it('should create STREAM_CHAT message with requestId', () => {
      const msg = createStreamChat('conv-1', 'Hello', 'req-1');
      expect(msg.type).toBe(MessageType.STREAM_CHAT);
      expect(msg.payload.conversationId).toBe('conv-1');
      expect(msg.payload.message).toBe('Hello');
      expect(msg.payload.requestId).toBe('req-1');
    });
  });

  describe('createCancelStream', () => {
    it('should create CANCEL_STREAM message with requestId', () => {
      const msg = createCancelStream('req-1');
      expect(msg.type).toBe(MessageType.CANCEL_STREAM);
      expect(msg.requestId).toBe('req-1');
    });
  });
});
