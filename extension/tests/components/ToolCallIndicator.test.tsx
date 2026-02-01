/**
 * ToolCallIndicator component tests (Step 2: TDD)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ToolCallIndicator } from '../../components/ToolCallIndicator';

describe('ToolCallIndicator', () => {
  it('should render tool call name', () => {
    render(
      <ToolCallIndicator
        name="search_web"
        arguments={{ query: 'hello' }}
      />
    );
    expect(screen.getByText(/search_web/i)).toBeDefined();
  });

  it('should render tool call arguments as JSON', () => {
    render(
      <ToolCallIndicator
        name="get_weather"
        arguments={{ city: 'Seoul', unit: 'celsius' }}
      />
    );
    const argsElement = screen.getByText(/"city".*"Seoul"/);
    expect(argsElement).toBeDefined();
  });

  it('should render tool result when provided', () => {
    render(
      <ToolCallIndicator
        name="calculate"
        arguments={{ expression: '2+2' }}
        result="4"
      />
    );
    expect(screen.getByText(/result/i)).toBeDefined();
    expect(screen.getByText('4')).toBeDefined();
  });

  it('should show executing state when result is not provided', () => {
    render(
      <ToolCallIndicator
        name="slow_operation"
        arguments={{}}
      />
    );
    // Should indicate execution in progress
    const indicator = screen.getByTestId('tool-call-indicator');
    expect(indicator.className).toContain('executing');
  });

  it('should show completed state when result is provided', () => {
    render(
      <ToolCallIndicator
        name="completed_task"
        arguments={{}}
        result="Success"
      />
    );
    const indicator = screen.getByTestId('tool-call-indicator');
    expect(indicator.className).toContain('completed');
  });

  it('should handle empty arguments gracefully', () => {
    render(
      <ToolCallIndicator
        name="ping"
        arguments={{}}
      />
    );
    expect(screen.getByText(/ping/i)).toBeDefined();
  });
});
