/**
 * StreamEvent type tests (Step 2: StreamChunk 이벤트 타입 확장)
 *
 * RED Phase: 새로운 이벤트 타입 검증 (tool_call, tool_result, agent_transfer, error with code)
 */

import { describe, it, expect } from 'vitest';
import type { StreamEvent } from '../../lib/types';

describe('StreamEvent Types (Step 2)', () => {
  it('should support tool_call event type', () => {
    const event: StreamEvent = {
      type: 'tool_call',
      tool_name: 'search',
      tool_arguments: { q: 'test query' },
    };

    expect(event.type).toBe('tool_call');
    expect(event.tool_name).toBe('search');
    expect(event.tool_arguments).toEqual({ q: 'test query' });
  });

  it('should support tool_result event type', () => {
    const event: StreamEvent = {
      type: 'tool_result',
      tool_name: 'search',
      result: 'Search results here',
    };

    expect(event.type).toBe('tool_result');
    expect(event.tool_name).toBe('search');
    expect(event.result).toBe('Search results here');
  });

  it('should support agent_transfer event type', () => {
    const event: StreamEvent = {
      type: 'agent_transfer',
      agent_name: 'specialist_agent',
    };

    expect(event.type).toBe('agent_transfer');
    expect(event.agent_name).toBe('specialist_agent');
  });

  it('should support error event with error_code (Step 3)', () => {
    const event: StreamEvent = {
      type: 'error',
      content: 'Rate limit exceeded',
      error_code: 'LlmRateLimitError',
    };

    expect(event.type).toBe('error');
    expect(event.content).toBe('Rate limit exceeded');
    expect(event.error_code).toBe('LlmRateLimitError');
  });

  it('should support error event without error_code for backward compatibility', () => {
    const event: StreamEvent = {
      type: 'error',
      content: 'Something went wrong',
    };

    expect(event.type).toBe('error');
    expect(event.content).toBe('Something went wrong');
    expect(event.error_code).toBeUndefined();
  });
});
