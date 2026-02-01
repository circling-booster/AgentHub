/**
 * WorkflowManager Component
 *
 * Manages workflow CRUD operations.
 * Phase 5 Part E Step 15-2.
 */

import { useState, useEffect } from 'react';
import type { Workflow, A2aAgent, WorkflowStep } from '../lib/types';
import { getWorkflows, createWorkflow, deleteWorkflow, listA2aAgents } from '../lib/api';

export function WorkflowManager() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [agents, setAgents] = useState<A2aAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedWorkflowId, setExpandedWorkflowId] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Form state
  const [formName, setFormName] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formType, setFormType] = useState<'sequential' | 'parallel'>('sequential');
  const [formSteps, setFormSteps] = useState<WorkflowStep[]>([]);

  // Load workflows and agents on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [workflowsData, agentsData] = await Promise.all([
        getWorkflows(),
        listA2aAgents(),
      ]);
      setWorkflows(workflowsData);
      setAgents(agentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleExpand = (workflowId: string) => {
    setExpandedWorkflowId(expandedWorkflowId === workflowId ? null : workflowId);
  };

  const handleCreateClick = () => {
    setShowCreateDialog(true);
    setFormName('');
    setFormDescription('');
    setFormType('sequential');
    setFormSteps([]);
  };

  const handleAddStep = () => {
    if (agents.length === 0) return;

    setFormSteps([
      ...formSteps,
      {
        agent_endpoint_id: agents[0].id,
        output_key: `step_${formSteps.length + 1}_result`,
        instruction: '',
      },
    ]);
  };

  const handleUpdateStep = (index: number, field: keyof WorkflowStep, value: string) => {
    const updated = [...formSteps];
    updated[index] = { ...updated[index], [field]: value };
    setFormSteps(updated);
  };

  const handleRemoveStep = (index: number) => {
    setFormSteps(formSteps.filter((_, i) => i !== index));
  };

  const handleCreateSubmit = async () => {
    if (!formName || formSteps.length === 0) return;

    try {
      await createWorkflow({
        name: formName,
        workflow_type: formType,
        description: formDescription,
        steps: formSteps,
      });

      setShowCreateDialog(false);
      await loadData(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow');
    }
  };

  const handleDeleteClick = (workflowId: string) => {
    setDeleteConfirmId(workflowId);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmId) return;

    try {
      await deleteWorkflow(deleteConfirmId);
      setDeleteConfirmId(null);
      await loadData(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete workflow');
    }
  };

  const getAgentName = (agentId: string): string => {
    return agents.find((a) => a.id === agentId)?.name || agentId;
  };

  if (loading) {
    return <div className="p-4">Loading workflows...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="workflow-manager p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Workflows</h2>
        <button
          onClick={handleCreateClick}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          aria-label="Create Workflow"
        >
          Create Workflow
        </button>
      </div>

      {workflows.length === 0 ? (
        <p className="text-gray-500">No workflows created yet.</p>
      ) : (
        <div className="space-y-2">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="border rounded p-3">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold">{workflow.name}</h3>
                  <p className="text-sm text-gray-600">{workflow.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Type: {workflow.workflow_type} | Steps: {workflow.steps.length}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExpand(workflow.id)}
                    className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
                    aria-label="Expand"
                  >
                    {expandedWorkflowId === workflow.id ? '▼' : '▶'}
                  </button>
                  <button
                    onClick={() => handleDeleteClick(workflow.id)}
                    className="px-2 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
                    aria-label="Delete"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {expandedWorkflowId === workflow.id && (
                <div className="mt-3 pl-4 border-l-2 border-gray-300">
                  <h4 className="text-sm font-semibold mb-2">Steps:</h4>
                  {workflow.steps.map((step, idx) => (
                    <div key={idx} className="text-sm mb-1">
                      {idx + 1}. {getAgentName(step.agent_endpoint_id)}
                      <span className="text-gray-500 ml-2">→ {step.output_key}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded shadow-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Create Workflow</h3>

            <label className="block mb-2">
              <span className="text-sm font-medium">Workflow Name</span>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className="w-full border rounded px-2 py-1 mt-1"
                aria-label="Workflow Name"
              />
            </label>

            <label className="block mb-2">
              <span className="text-sm font-medium">Description</span>
              <textarea
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                className="w-full border rounded px-2 py-1 mt-1"
                rows={2}
                aria-label="Description"
              />
            </label>

            <label className="block mb-4">
              <span className="text-sm font-medium">Type</span>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value as 'sequential' | 'parallel')}
                className="w-full border rounded px-2 py-1 mt-1"
                aria-label="Type"
              >
                <option value="sequential">Sequential</option>
                <option value="parallel">Parallel</option>
              </select>
            </label>

            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Steps</span>
                <button
                  onClick={handleAddStep}
                  className="px-2 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                  aria-label="Add Step"
                >
                  Add Step
                </button>
              </div>

              {formSteps.map((step, idx) => (
                <div key={idx} className="border rounded p-2 mb-2">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium">Step {idx + 1}</span>
                    <button
                      onClick={() => handleRemoveStep(idx)}
                      className="text-red-500 text-sm"
                    >
                      Remove
                    </button>
                  </div>

                  <label className="block mb-1">
                    <span className="text-xs">Agent</span>
                    <select
                      value={step.agent_endpoint_id}
                      onChange={(e) => handleUpdateStep(idx, 'agent_endpoint_id', e.target.value)}
                      className="w-full border rounded px-2 py-1 text-sm"
                      aria-label="Agent"
                    >
                      {agents.map((agent) => (
                        <option key={agent.id} value={agent.id}>
                          {agent.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <span className="text-xs">Output Key</span>
                    <input
                      type="text"
                      value={step.output_key}
                      onChange={(e) => handleUpdateStep(idx, 'output_key', e.target.value)}
                      className="w-full border rounded px-2 py-1 text-sm"
                    />
                  </label>
                </div>
              ))}
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowCreateDialog(false)}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateSubmit}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                aria-label="Create"
                disabled={!formName || formSteps.length === 0}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded shadow-lg">
            <p className="mb-4">Are you sure you want to delete this workflow?</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                aria-label="Confirm"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
