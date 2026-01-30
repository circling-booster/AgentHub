/**
 * A2A Agent management component
 *
 * Provides UI for registering, listing, and removing A2A agents.
 * Shows expandable agent card details for each agent.
 */

import { useState, useEffect } from 'react';
import { useA2aAgents } from '../hooks/useA2aAgents';

export function A2aAgentManager() {
  const { agents, loading, error, loadAgents, addAgent, removeAgent } = useA2aAgents();
  const [url, setUrl] = useState('');
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  const handleAdd = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    await addAgent(trimmed);
    setUrl('');
  };

  const toggleAgentExpand = (agentId: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedAgents(newExpanded);
  };

  return (
    <div className="a2a-agent-manager">
      <div className="add-agent-form">
        <input
          type="text"
          placeholder="A2A Agent URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button onClick={handleAdd}>Add Agent</button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && <div className="loading">Loading...</div>}

      {!loading && agents.length === 0 && (
        <div className="empty-state">No A2A agents registered</div>
      )}

      <div className="agent-list">
        {agents.map((agent) => (
          <div key={agent.id} className="agent-item">
            <div className="agent-header">
              <button
                className="expand-button"
                onClick={() => toggleAgentExpand(agent.id)}
              >
                {expandedAgents.has(agent.id) ? '▼' : '▶'}
              </button>
              <div className="agent-info">
                <span className="agent-name">{agent.name}</span>
                <span className="agent-url">{agent.url}</span>
              </div>
              <button onClick={() => removeAgent(agent.id)}>Remove</button>
            </div>

            {expandedAgents.has(agent.id) && (
              <div className="agent-card">
                {!agent.agent_card && <div className="no-card">No agent card available</div>}
                {agent.agent_card && (
                  <pre className="agent-card-json">
                    {JSON.stringify(agent.agent_card, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
