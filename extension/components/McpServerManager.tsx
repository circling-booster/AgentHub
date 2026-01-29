/**
 * MCP Server management component
 *
 * Provides UI for registering, listing, and removing MCP servers.
 */

import { useState, useEffect } from 'react';
import { useMcpServers } from '../hooks/useMcpServers';

export function McpServerManager() {
  const { servers, loading, error, loadServers, addServer, removeServer } = useMcpServers();
  const [url, setUrl] = useState('');

  useEffect(() => {
    loadServers();
  }, [loadServers]);

  const handleAdd = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    await addServer(trimmed);
    setUrl('');
  };

  return (
    <div className="mcp-server-manager">
      <div className="add-server-form">
        <input
          type="text"
          placeholder="MCP Server URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button onClick={handleAdd}>Add Server</button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && <div className="loading">Loading...</div>}

      {!loading && servers.length === 0 && (
        <div className="empty-state">No MCP servers registered</div>
      )}

      <div className="server-list">
        {servers.map((server) => (
          <div key={server.id} className="server-item">
            <div className="server-info">
              <span className="server-name">{server.name}</span>
              <span className="server-url">{server.url}</span>
            </div>
            <button onClick={() => removeServer(server.id)}>Remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}
