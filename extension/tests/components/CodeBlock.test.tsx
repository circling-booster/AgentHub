import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CodeBlock } from '../../components/CodeBlock';

describe('CodeBlock', () => {
  it('should render code with language syntax highlighting', () => {
    render(<CodeBlock language="python" code="print('hello')" />);

    // react-syntax-highlighter breaks code into multiple spans
    // Check that code block container exists
    const codeBlock = screen.getByTestId('code-block');
    expect(codeBlock).toBeDefined();

    // Verify language is applied (class attribute)
    const codeElement = codeBlock.querySelector('code.language-python');
    expect(codeElement).toBeTruthy();
  });

  it('should render code without language (plain text)', () => {
    render(<CodeBlock language="" code="plain text" />);

    const codeElement = screen.getByText('plain text');
    expect(codeElement).toBeDefined();
  });

  it('should handle empty code', () => {
    render(<CodeBlock language="javascript" code="" />);

    // Should render empty code block without errors
    const container = screen.getByTestId('code-block');
    expect(container).toBeDefined();
  });

  it('should display language label when language is provided', () => {
    render(<CodeBlock language="typescript" code="const x = 1;" />);

    expect(screen.getByText('typescript')).toBeDefined();
  });

  it('should not display language label when language is empty', () => {
    render(<CodeBlock language="" code="text" />);

    expect(screen.queryByTestId('language-label')).toBeNull();
  });
});
