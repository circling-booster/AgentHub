# ADR-011: Workflow Agents Spike Results (Phase 5-E Step 13)

**Status:** ✅ Accepted
**Date:** 2026-02-01
**Deciders:** AgentHub Development Team

---

## Context

Phase 5-E requires implementing multi-step A2A delegation using ADK Workflow Agents (SequentialAgent, ParallelAgent). Before proceeding with Step 14 implementation, we needed to verify compatibility between ADK Workflow Agents and RemoteA2aAgent.

## Decision

**Proceed with ADK SequentialAgent/ParallelAgent** for Step 14-16 implementation.

### Spike Test Results

| Component | Status | Notes |
|-----------|:------:|-------|
| **SequentialAgent + RemoteA2aAgent** | ✅ COMPATIBLE | All tests passed |
| **ParallelAgent + RemoteA2aAgent** | ✅ COMPATIBLE | All tests passed |
| **Session State Access** | ✅ AVAILABLE | Manual state management possible |
| **output_key** | ⏸️ TBD | Requires further investigation in Step 14 if needed |

### Test Evidence

- **File:** `tests/integration/adapters/test_workflow_agent_spike.py`
- **Tests:** 4 passed, 0 failed
- **Execution Time:** 17.03s
- **Test Date:** 2026-02-01

#### Test Cases

1. `test_sequential_agent_with_two_remote_agents` ✅
   - SequentialAgent executes Echo → Math agents successfully

2. `test_sequential_agent_executes_in_order` ✅
   - Sequential execution order verified

3. `test_parallel_agent_with_remote_agents` ✅
   - ParallelAgent executes Echo + Math agents concurrently

4. `test_access_shared_session_state` ✅
   - `session.state` is accessible for manual state management

---

## Consequences

### Positive

- ✅ No need for custom SequentialRunner implementation
- ✅ No need for LlmAgent wrapper workaround
- ✅ Can use ADK native Workflow Agents directly
- ✅ State sharing mechanism available (`session.state`)
- ✅ Hybrid workflows possible (LlmAgent + RemoteA2aAgent mix)

### Negative

- ⚠️ RemoteA2aAgent is marked as EXPERIMENTAL by ADK
  - Warning: "ADK Implementation for A2A support is in experimental mode"
  - Risk: Breaking changes possible in future ADK versions
  - Mitigation: Follow ADK release notes, update standards verification protocol

### Neutral

- `output_key` mechanism details can be investigated in Step 14 if needed
- Manual state management via `session.state` is sufficient for Phase 5-E

---

## Implementation Plan for Step 14

Based on spike results:

1. **Use SequentialAgent directly** for sequential workflows
2. **Use ParallelAgent directly** for parallel workflows
3. **State Sharing Strategy:**
   - Try `output_key` first (if supported)
   - Fallback to manual `session.state` access (confirmed working)
4. **No breaking changes** to existing single-delegation (Phase 5-A) functionality

---

## Risks and Mitigation

| Risk | Severity | Mitigation |
|------|:--------:|------------|
| ADK breaks RemoteA2aAgent API | 🟡 Medium | Standards verification before each implementation step |
| `output_key` not supported | 🟢 Low | Manual state management confirmed working |
| Performance degradation with many agents | 🟢 Low | Defer loading already implemented (Phase 4-D) |

---

## References

- [ADK Sequential Agents Docs](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)
- [ADK Parallel Agents Docs](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)
- [ADK State Management](https://google.github.io/adk-docs/sessions/state/)
- Phase 5 Part E Plan: `docs/plans/phase5/partE.md`
- Spike Tests: `tests/integration/adapters/test_workflow_agent_spike.py`

---

## Alternatives Considered

### Option 1: Custom SequentialRunner
- **Rejected:** ADK native SequentialAgent works perfectly
- **Reason:** No need to reinvent the wheel

### Option 2: LlmAgent Wrapper for RemoteA2aAgent
- **Rejected:** RemoteA2aAgent works directly with SequentialAgent
- **Reason:** Unnecessary complexity

### Option 3: Manual Chaining in OrchestratorAdapter
- **Rejected:** ADK Workflow Agents provide better abstraction
- **Reason:** Would lose ADK's built-in features (logging, tracing, error handling)

---

## Next Steps

1. ✅ **Step 13 Complete** - Spike tests passed
2. ⏭️ **Step 14** - Implement WorkflowAgent domain entity + OrchestratorAdapter workflow support
3. ⏭️ **Step 15** - Workflow REST API + Extension UI
4. ⏭️ **Step 16** - ParallelAgent support + E2E tests

---

*ADR Author: Claude Sonnet 4.5*
*Last Updated: 2026-02-01*
