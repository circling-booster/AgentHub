# doc-audit-planner Agent Memory

Patterns and principles learned during project documentation audit work.

---

## Documentation Structure (Updated: 2026-02-07)

### Hub-and-Spoke Architecture

AgentHub follows a **Hub-and-Spoke architecture**:

- **Hub**: `docs/MAP.md` - Contains only high-level section overview (no detailed structure)
- **Spokes**: Section READMEs (`developers/`, `operators/`, `project/`) - Manage subsection structure

**Important**: MAP.md lists **high-level sections only**. When adding new files/folders, update the corresponding Section README, and update MAP.md **only when adding new major sections**.

### File Location Decision

| When Adding Files | Update Target |
|------------------|----------------|
| Files within `docs/developers/architecture/` | `docs/developers/architecture/README.md` |
| New section folder within `docs/developers/` | `docs/developers/README.md` + (rarely) `docs/MAP.md` |
| Adding key entry points (frequently accessed) | `docs/llms.txt` |

---

## Linking Policy (From CLAUDE.md)

| Target | Strategy | When to Use |
|--------|----------|-------------|
| **Within same section** | Direct relative links | Referencing documents in same folder |
| **Different section, frequently referenced** | Direct absolute links | Core documents (CLAUDE.md, tests/README.md) |
| **Different section, occasionally referenced** | MAP reference | Reference documents across domains |

---

## Documentation Steps Template

Documentation steps added to Phase must always include validation instructions:
- "After completion, run `python scripts/validate_docs.py` to check for errors"

---

## Key Files for Context

Files that must always be read when performing documentation audit:

1. `docs/MAP.md` - Hub (section overview)
2. `docs/llms.txt` - List of core documents accessible to AI
3. `CLAUDE.md` - Project principles + linking policy
4. Related Section README - Detailed subsection information

---

## Common Mistakes to Avoid

1. ❌ **Don't add detailed structure to MAP.md**
   - MAP.md contains only high-level sections
   - Subsection structure is managed by Section READMEs

2. ❌ **Don't omit validation instructions in Phase documentation**
   - Include validation execution instructions in all documentation steps
   - Template: "After completion, run `python scripts/validate_docs.py`"

---

*Last Updated: 2026-02-07*
*Structure Version: Hub-and-Spoke (2-level)*
