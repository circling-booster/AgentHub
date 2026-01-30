import { describe, it, expect } from 'vitest';
import { parseMessageContent } from '../../lib/markdown';

describe('parseMessageContent', () => {
  it('should parse single code block', () => {
    const input = 'Here is code:\n```python\nprint("hello")\n```';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ type: 'text', content: 'Here is code:' });
    expect(result[1]).toEqual({
      type: 'code',
      language: 'python',
      code: 'print("hello")',
    });
  });

  it('should parse multiple code blocks', () => {
    const input = 'First:\n```js\nconst x = 1;\n```\nSecond:\n```py\nprint(2)\n```';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(4);
    expect(result[0]).toEqual({ type: 'text', content: 'First:' });
    expect(result[1]).toEqual({ type: 'code', language: 'js', code: 'const x = 1;' });
    expect(result[2]).toEqual({ type: 'text', content: 'Second:' });
    expect(result[3]).toEqual({ type: 'code', language: 'py', code: 'print(2)' });
  });

  it('should parse code block without language', () => {
    const input = '```\nplain code\n```';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ type: 'code', language: '', code: 'plain code' });
  });

  it('should handle text without code blocks', () => {
    const input = 'Just plain text here';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ type: 'text', content: 'Just plain text here' });
  });

  it('should handle empty input', () => {
    const result = parseMessageContent('');

    expect(result).toHaveLength(0);
  });

  it('should trim whitespace around code blocks', () => {
    const input = 'Text\n\n```js\ncode\n```\n\nMore text';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ type: 'text', content: 'Text' });
    expect(result[1]).toEqual({ type: 'code', language: 'js', code: 'code' });
    expect(result[2]).toEqual({ type: 'text', content: 'More text' });
  });

  it('should handle inline backticks (not code blocks)', () => {
    const input = 'Use `variable` here';

    const result = parseMessageContent(input);

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ type: 'text', content: 'Use `variable` here' });
  });
});
