import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ServerStatus } from '../../components/ServerStatus';

// Mock useServerHealth hook
vi.mock('../../hooks/useServerHealth', () => ({
  useServerHealth: vi.fn(),
}));

import { useServerHealth } from '../../hooks/useServerHealth';
const mockUseServerHealth = vi.mocked(useServerHealth);

describe('ServerStatus', () => {
  it('should show healthy status with green indicator', () => {
    // Given: Server is healthy
    mockUseServerHealth.mockReturnValue({
      status: 'healthy',
      lastChecked: Date.now(),
      isHealthy: true,
    });

    // When: Render
    render(<ServerStatus />);

    // Then: Shows healthy text and green indicator
    expect(screen.getByText('Connected')).toBeDefined();
    expect(screen.getByTestId('status-indicator')).toBeDefined();
    expect(screen.getByTestId('status-indicator').className).toContain('healthy');
  });

  it('should show unhealthy status with red indicator', () => {
    // Given: Server is unhealthy
    mockUseServerHealth.mockReturnValue({
      status: 'unhealthy',
      lastChecked: Date.now(),
      isHealthy: false,
    });

    // When: Render
    render(<ServerStatus />);

    // Then: Shows disconnected text
    expect(screen.getByText('Disconnected')).toBeDefined();
    expect(screen.getByTestId('status-indicator').className).toContain('unhealthy');
  });

  it('should show unknown status initially', () => {
    // Given: Status unknown
    mockUseServerHealth.mockReturnValue({
      status: 'unknown',
      lastChecked: null,
      isHealthy: false,
    });

    // When: Render
    render(<ServerStatus />);

    // Then: Shows checking text
    expect(screen.getByText('Checking...')).toBeDefined();
    expect(screen.getByTestId('status-indicator').className).toContain('unknown');
  });
});
