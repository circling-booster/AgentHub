/**
 * MCP Server management component
 *
 * Provides UI for registering, listing, and removing MCP servers.
 * Shows expandable tools list for each server.
 */

import { useState, useEffect } from 'react';
import { useMcpServers } from '../hooks/useMcpServers';

export function McpServerManager() {
  const { servers, loading, error, loadServers, addServer, removeServer, loadTools } = useMcpServers();
  const [url, setUrl] = useState('');
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadServers();
  }, [loadServers]);

  const handleAdd = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    await addServer(trimmed);
    setUrl('');
  };

  const toggleServerExpand = async (serverId: string) => {
    const newExpanded = new Set(expandedServers);
    if (newExpanded.has(serverId)) {
      newExpanded.delete(serverId);
    } else {
      newExpanded.add(serverId);
      // Load tools when expanding (if not already loaded)
      const server = servers.find(s => s.id === serverId);
      if (server && !server.tools) {
        await loadTools(serverId);
      }
    }
    setExpandedServers(newExpanded);
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
            <div className="server-header">
              <button
                className="expand-button"
                onClick={() => toggleServerExpand(server.id)}
              >
                {expandedServers.has(server.id) ? '▼' : '▶'}
              </button>
              <div className="server-info">
                <span className="server-name">{server.name}</span>
                <span className="server-url">{server.url}</span>
              </div>
              <button onClick={() => removeServer(server.id)}>Remove</button>
            </div>

            {expandedServers.has(server.id) && (
              <div className="tools-list">
                {!server.tools && <div className="loading-tools">Loading tools...</div>}
                {server.tools && server.tools.length === 0 && (
                  <div className="no-tools">No tools available</div>
                )}
                {server.tools && server.tools.length > 0 && (
                  <ul>
                    {server.tools.map((tool) => (
                      <li key={tool.name} className="tool-item">
                        <span className="tool-name">{tool.name}</span>
                        <span className="tool-description">{tool.description}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
