<!--
  Sync Impact Report
  Version change: (placeholder) → 1.0.0
  Modified principles: N/A (initial adoption)
  Added sections: Core Principles (3), Technology Stack, Development Workflow, Governance
  Removed sections: None (replaced placeholders)
  Templates: plan-template.md ✅ updated; spec-template.md ✅ no mandatory section changes;
    tasks-template.md ✅ no principle-driven task type changes; commands/*.md N/A (folder not present)
  Follow-up TODOs: None
-->

# Multi-Agent System Constitution

## Core Principles

### I. PEP 8 Code Style

All project code MUST follow PEP 8 style guidelines. This includes naming conventions,
line length (recommended 88–99 with formatter; project MAY set a consistent limit),
indentation (4 spaces), and formatting of imports, whitespace, and comments. Use a
linter/formatter (e.g. Ruff, Black, flake8) in CI and locally so compliance is
automatically enforced.

**Rationale**: Consistency and readability across the codebase; reduces review friction
and aligns with the broader Python ecosystem.

### II. Multi-Agent Setup with Autogen

The system MUST be implemented as a multi-agent setup using the Autogen framework.
Agents MUST be defined, configured, and orchestrated via Autogen patterns (e.g.
conversable agents, group chats, appropriate agent roles). Design choices (agent
count, roles, flow) MUST be justified by the feature specification and documented
in the implementation plan.

**Rationale**: Autogen is the chosen framework for multi-agent behavior; all
agent-related work must stay within its model to ensure maintainability and
upgradeability.

### III. Tools Hosted via MCP

Agent tools MUST be hosted via the Model Context Protocol (MCP). Tools used by
Autogen agents MUST be exposed through MCP servers and consumed via the project’s
MCP client integration. New tooling MUST be added as MCP tools/servers rather than
ad-hoc in-process callables unless the constitution is amended to allow exceptions.

**Rationale**: MCP provides a standard, composable way to expose tools to agents
and keeps tool implementations decoupled from the agent runtime.

## Technology Stack

- **Language**: Python (version to be set in implementation plan; recommend 3.10+).
- **Multi-agent**: Autogen (version and extras as needed for MCP).
- **Tools**: MCP servers and client; tool descriptors and discovery per MCP spec.
- **Linting/formatting**: PEP 8–compliant tooling (e.g. Ruff and/or Black); config
  in repository root and run in CI.

## Development Workflow

- **Constitution Check**: Before Phase 0 research and again after Phase 1 design,
  the implementation plan MUST confirm compliance with all three core principles
  (PEP 8, Autogen, MCP).
- **Code review**: Reviews MUST verify PEP 8 compliance (via tooling) and that new
  agent code uses Autogen and that new tools are exposed via MCP.
- **Complexity**: Any deviation from the principles (e.g. non-MCP tools, non-Autogen
  agent code) MUST be documented and justified in the plan’s Complexity Tracking
  table.

## Governance

This constitution supersedes ad-hoc project practices for the areas it covers.
Amendments require: (1) a documented change proposal, (2) version bump per
semantic versioning (MAJOR for backward-incompatible principle removals or
redefinitions, MINOR for new principles or materially expanded guidance, PATCH
for clarifications and non-semantic refinements), and (3) update of any
dependent templates and specs. All PRs and implementation plans MUST verify
compliance with the current constitution. Use the implementation plan and
specs in `/specs/` for feature-level runtime guidance.

**Version**: 1.0.0 | **Ratified**: 2025-02-21 | **Last Amended**: 2025-02-21
