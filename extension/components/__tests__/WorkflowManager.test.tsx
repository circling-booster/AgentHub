/**
 * WorkflowManager component tests
 *
 * Tests workflow CRUD UI functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowManager } from '../WorkflowManager';
import type { Workflow, A2aAgent } from '../../lib/types';

// Mock API module
vi.mock('../../lib/api', () => ({
  getWorkflows: vi.fn(),
  createWorkflow: vi.fn(),
  deleteWorkflow: vi.fn(),
  listA2aAgents: vi.fn(),
}));

import * as api from '../../lib/api';

describe('WorkflowManager', () => {
  const mockAgents: A2aAgent[] = [
    {
      id: 'agent-1',
      name: 'Echo Agent',
      url: 'http://localhost:9003',
      type: 'a2a',
      enabled: true,
      agent_card: null,
      registered_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'agent-2',
      name: 'Math Agent',
      url: 'http://localhost:9004',
      type: 'a2a',
      enabled: true,
      agent_card: null,
      registered_at: '2026-01-01T00:00:00Z',
    },
  ];

  const mockWorkflows: Workflow[] = [
    {
      id: 'workflow-1',
      name: 'Echo then Math',
      workflow_type: 'sequential',
      description: 'Echo user message then calculate',
      steps: [
        { agent_endpoint_id: 'agent-1', output_key: 'echo_result', instruction: '' },
        { agent_endpoint_id: 'agent-2', output_key: 'math_result', instruction: '' },
      ],
      created_at: '2026-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (api.listA2aAgents as ReturnType<typeof vi.fn>).mockResolvedValue(mockAgents);
    (api.getWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflows);
  });

  it('should render workflow list on mount', async () => {
    render(<WorkflowManager />);

    // Wait for workflows to load
    await waitFor(() => {
      expect(screen.getByText('Echo then Math')).toBeTruthy();
    });

    expect(api.getWorkflows).toHaveBeenCalledTimes(1);
    expect(api.listA2aAgents).toHaveBeenCalledTimes(1);
  });

  it('should display workflow details when expanded', async () => {
    render(<WorkflowManager />);

    // Wait for workflows to load
    await waitFor(() => {
      expect(screen.getByText('Echo then Math')).toBeTruthy();
    });

    // Expand workflow details
    const expandButton = screen.getByRole('button', { name: /expand/i });
    fireEvent.click(expandButton);

    // Verify steps are displayed
    await waitFor(() => {
      expect(screen.getByText(/Echo Agent/i)).toBeTruthy();
      expect(screen.getByText(/Math Agent/i)).toBeTruthy();
    });
  });

  it('should create new workflow when form is submitted', async () => {
    (api.createWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 'new-workflow',
      name: 'Test Workflow',
      workflow_type: 'sequential',
      description: 'Test description',
      steps: [{ agent_endpoint_id: 'agent-1', output_key: 'result', instruction: '' }],
      created_at: '2026-01-01T00:00:00Z',
    });

    render(<WorkflowManager />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Echo then Math')).toBeTruthy();
    });

    // Open create workflow dialog
    const createButton = screen.getByRole('button', { name: /create workflow/i });
    fireEvent.click(createButton);

    // Fill form
    const nameInput = screen.getByLabelText(/workflow name/i);
    fireEvent.change(nameInput, { target: { value: 'Test Workflow' } });

    const descInput = screen.getByLabelText(/description/i);
    fireEvent.change(descInput, { target: { value: 'Test description' } });

    const typeSelect = screen.getByLabelText(/type/i);
    fireEvent.change(typeSelect, { target: { value: 'sequential' } });

    // Add step
    const addStepButton = screen.getByRole('button', { name: /add step/i });
    fireEvent.click(addStepButton);

    const agentSelect = screen.getByLabelText(/agent/i);
    fireEvent.change(agentSelect, { target: { value: 'agent-1' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: 'Create' });
    fireEvent.click(submitButton);

    // Verify API call
    await waitFor(() => {
      expect(api.createWorkflow).toHaveBeenCalledWith({
        name: 'Test Workflow',
        description: 'Test description',
        workflow_type: 'sequential',
        steps: [
          {
            agent_endpoint_id: 'agent-1',
            output_key: expect.any(String),
            instruction: '',
          },
        ],
      });
    });

    // Verify workflows list is refreshed
    expect(api.getWorkflows).toHaveBeenCalledTimes(2);
  });

  it('should delete workflow when delete button is clicked', async () => {
    (api.deleteWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    render(<WorkflowManager />);

    // Wait for workflows to load
    await waitFor(() => {
      expect(screen.getByText('Echo then Math')).toBeTruthy();
    });

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    // Verify API call
    await waitFor(() => {
      expect(api.deleteWorkflow).toHaveBeenCalledWith('workflow-1');
    });

    // Verify workflows list is refreshed
    expect(api.getWorkflows).toHaveBeenCalledTimes(2);
  });
});
