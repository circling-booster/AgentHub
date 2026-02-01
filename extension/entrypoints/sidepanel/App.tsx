/**
 * Sidepanel main application
 *
 * Tab-based navigation between Chat, MCP Server, and A2A Agent management.
 */

import { useState } from 'react';
import { ChatInterface } from '../../components/ChatInterface';
import { McpServerManager } from '../../components/McpServerManager';
import { A2aAgentManager } from '../../components/A2aAgentManager';
import { ServerStatus } from '../../components/ServerStatus';

type Tab = 'chat' | 'mcp' | 'a2a';

export function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');

  return (
    <div className="app">
      <header className="app-header">
        <h1>AgentHub</h1>
        <ServerStatus />
      </header>

      <nav className="tab-bar">
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button
          className={`tab ${activeTab === 'mcp' ? 'active' : ''}`}
          onClick={() => setActiveTab('mcp')}
        >
          MCP Servers
        </button>
        <button
          className={`tab ${activeTab === 'a2a' ? 'active' : ''}`}
          onClick={() => setActiveTab('a2a')}
        >
          A2A Agents
        </button>
      </nav>

      <main className="tab-content">
        {activeTab === 'chat' && <ChatInterface />}
        {activeTab === 'mcp' && <McpServerManager />}
        {activeTab === 'a2a' && <A2aAgentManager />}
      </main>
    </div>
  );
}
