/**
 * Server API types (1:1 mapping with server schemas)
 *
 * Source: src/adapters/inbound/http/schemas/
 */

/** SSE stream event types matching server chat.py output */
export interface StreamEventConversationCreated {
  type: 'conversation_created';
  conversation_id: string;
}

export interface StreamEventText {
  type: 'text';
  content: string;
}

export interface StreamEventDone {
  type: 'done';
}

export interface StreamEventToolCall {
  type: 'tool_call';
  tool_name: string;
  tool_arguments: Record<string, unknown>;
}

export interface StreamEventToolResult {
  type: 'tool_result';
  tool_name: string;
  result: string;
}

export interface StreamEventAgentTransfer {
  type: 'agent_transfer';
  agent_name: string;
}

export interface StreamEventError {
  type: 'error';
  content: string;
  error_code?: string;
}

export type StreamEvent =
  | StreamEventConversationCreated
  | StreamEventText
  | StreamEventToolCall
  | StreamEventToolResult
  | StreamEventAgentTransfer
  | StreamEventDone
  | StreamEventError;

/** Conversation (matches server ConversationResponse schema) */
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

/** MCP Server (matches server MCP routes response) */
export interface McpServer {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  registered_at: string;
  tools?: Tool[];
}

/** Tool (matches server Tool schema) */
export interface Tool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

/** Server health status */
export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp?: string;
}

/** Tool call information */
export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
}

/** Chat message for UI state */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
  toolCalls?: ToolCall[];
  agentTransfer?: string;
}

/** A2A Agent (matches server A2aAgentResponse schema) */
export interface A2aAgent {
  id: string;
  name: string;
  url: string;
  type: string; // "a2a"
  enabled: boolean;
  agent_card: Record<string, unknown> | null;
  registered_at: string;
}
