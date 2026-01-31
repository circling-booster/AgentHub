/**
 * Tool Call Indicator component (Step 2: SSE Event Streaming)
 *
 * Displays tool execution status with name, arguments, and result.
 */

interface ToolCallIndicatorProps {
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
}

export function ToolCallIndicator({ name, arguments: args, result }: ToolCallIndicatorProps) {
  const status = result ? 'completed' : 'executing';

  return (
    <div
      data-testid="tool-call-indicator"
      className={`tool-call-indicator ${status}`}
      style={{
        padding: '8px 12px',
        margin: '4px 0',
        borderRadius: '6px',
        backgroundColor: result ? '#e8f5e9' : '#fff3e0',
        border: '1px solid',
        borderColor: result ? '#4caf50' : '#ff9800',
        fontSize: '0.85rem',
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
        {result ? '✅' : '⏳'} {name}
      </div>

      {Object.keys(args).length > 0 && (
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            color: '#666',
            backgroundColor: '#f5f5f5',
            padding: '4px 8px',
            borderRadius: '4px',
            marginBottom: result ? '4px' : '0',
          }}
        >
          {JSON.stringify(args, null, 2)}
        </div>
      )}

      {result && (
        <div>
          <strong>Result:</strong>
          <div
            style={{
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              backgroundColor: '#f5f5f5',
              padding: '4px 8px',
              borderRadius: '4px',
              marginTop: '4px',
            }}
          >
            {result}
          </div>
        </div>
      )}
    </div>
  );
}
