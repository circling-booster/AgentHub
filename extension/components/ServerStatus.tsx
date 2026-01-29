/**
 * Server connection status indicator
 *
 * Displays health check status from useServerHealth hook.
 */

import { useServerHealth } from '../hooks/useServerHealth';

const STATUS_LABELS: Record<string, string> = {
  healthy: 'Connected',
  unhealthy: 'Disconnected',
  unknown: 'Checking...',
};

export function ServerStatus() {
  const { status } = useServerHealth();
  const label = STATUS_LABELS[status] || 'Checking...';

  return (
    <div className="server-status">
      <span
        data-testid="status-indicator"
        className={`status-indicator ${status}`}
      />
      <span className="status-label">{label}</span>
    </div>
  );
}
