import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'AgentHub',
    description: 'MCP + A2A 통합 AI Agent 인터페이스',
    permissions: [
      'activeTab',
      'storage',
      'sidePanel',
      'offscreen',
      'alarms',
    ],
    host_permissions: [
      'http://localhost:8000/*',
      'http://127.0.0.1:8000/*',
    ],
  },
});
