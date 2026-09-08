# Durable Development Methodology

Durable development keeps the decisions, evidence, and next action needed to continue work inside the project rather than inside a temporary conversation. It is a manual for people and coding agents, independent of language, framework, editor, or provider.

## The durable development loop

1. **Recover context.** Run `./.clineflow/bin/knowledge sync`, then read this manual, the five generated `knowledge/clineflow_*.yml` views, and their relevant journal links before proposing or changing work.
2. **Ground intent.** Inspect topics and create or explicitly resume a tenant-scoped Engineering Journal stream. Distinguish confirmed requirements from assumptions, constraints, non-goals, edge cases, and unanswered questions. Choose reversible implementation details within the authorized contract; ask before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria.
3. **Plan handoff topology.** Choose one handoff only for one cohesive, independently verifiable slice. Otherwise define linked milestones with solid ownership boundaries, local proof, dependencies, and one integrator who owns composition and final end-to-end proof.
4. **Define proof.** State observable success criteria and regression checks before implementation. A claim that something “works” is not evidence.
5. **Execute the approved slice.** Implement only what the current contract supports. Capture material decisions, discoveries, failures, and changes in the journal.
6. **Verify and record evidence.** Run the agreed checks. Record factual outcomes, including failures and gaps, and link the evidence from the verification index.
7. **Handoff deliberately.** Update the current-session summary and timeline so a new person or agent can recover the contract, evidence, and next safe step without reading an old chat. In a milestone chain, accept each local proof before composition, then record the integrator's composed result separately from the final handoff.
8. **Commit context with work.** Any change set containing a journal, documentation, or knowledge-base edit must reconcile all five ledgers, the active journal, and `knowledge/log.md` before validation and commit, so the repository carries code and its current explanation together.

## Master indexes

The YAML files under `knowledge/` are the front door to project context. They are concise and referential; Engineering Journals hold the detailed narrative and evidence.

| File | Update it when | It should answer |
| --- | --- | --- |
| `clineflow_specification.yml` | Behavior, constraints, assumptions, non-goals, or open questions change. | What have we agreed to build, preserve, or avoid? |
| `clineflow_verification.yml` | A check is defined, run, passed, failed, or blocked. | What proves completion, and what evidence exists? |
| `clineflow_goals.yml` | Outcomes, priorities, measures, or blockers change. | Why are we doing this work now, and what is success? |
| `clineflow_last_session.yml` | A material change or handoff occurs. | What changed last, what is true now, and what should happen next? |
| `clineflow_timeline.yml` | A project-relevant agent interaction, decision, repository event, or handoff occurs. | How did the project reach its current state? |

Use repository-relative paths in `journal_refs`, `evidence_refs`, `next_step_refs`, and timeline `refs`. Keep index summaries short enough to scan; put explanation, rationale, and detailed test output in the linked journal.

## Operating rules for agents

Before substantial work, an agent must read the indexes and linked journals, summarize the current contract and next safe step, and identify ambiguity. During work it updates the active journal first, then reconciles all five ledgers. At handoff it updates `clineflow_last_session.yml` and appends a timeline event. At commit it updates the journal, all five ledgers, and `knowledge/log.md`, validates the bundle and synchronization, and commits the code and durable context together.

The operational details live in `.clineflow/PROCEDURES.md`. Agents may generate code from intent and constraints, but code remains accountable to the contract and proof. Before a substantial slice, record the intended outcome, boundary, handoff topology, existing approaches considered, and planned proof. A milestone records its owned and excluded boundary, inputs and outputs, local proof, downstream consumer, dependencies, contributor, integrator, and escalation or rollback condition. Preserve factual evidence, failed approaches, and next steps without copying chat transcripts. Use deterministic tools for their encoded checks and record the integration checks and remaining judgment that they cannot settle.

For every qualifying knowledge change, create an immutable tenant update record that names its journal and stream, explicitly marks all five ledger reviews as changed or unchanged, and carries its timeline and log entry. Run `./.clineflow/bin/knowledge sync` to project the current ledger, handoff, log, and navigation views locally. Published records are never edited or deleted; a correction references the prior record. Before committing, run `./.clineflow/bin/validate-knowledge-sync`, stage code, journals, and update records together, and rerun it with `--staged`.

Agents choose reversible implementation details within the authorized contract. They ask for direction before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria. They may document options, but must not silently promote an assumption into an approved requirement.

## Installing ClineFlow through an agent

To ask a coding agent to install ClineFlow, use this exact prompt:

> Please install ClineFlow by following the instructions provided at [https://github.com/hassanvfx/clineflow](https://github.com/hassanvfx/clineflow)

The repository provides the current OS-aware installation instructions; the agent should follow them instead of relying on stale copied commands.

## Committing through an agent

Use this exact prompt:

> Please commit.

This asks the agent to finish the active Engineering Journal, reconcile all five ledgers and `knowledge/log.md`, run the required validators and project checks, stage code and durable context together, run staged knowledge synchronization, and create a descriptive commit only after the gates pass.

## Updating ClineFlow through an agent

Use this exact prompt:

> Please update ClineFlow.

This is explicit authorization for the agent to read the latest update instructions from the authoritative ClineFlow repository and immediately run `curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes` without asking again. Do not run any existing local updater first; legacy copies can overwrite themselves. The agent waits for migration and verification or rollback to finish, then reports the installed version and preserved legacy artifacts. Safety failures still stop the update, and the authorization does not extend to unrelated system changes or destructive cleanup.

If an old installation does not recognize the prompt, run that exact remote-bootstrap command directly from the project root. It is the compatibility escape hatch and must take precedence over any updater bundled in the old installation.

## Removing ClineFlow through an agent

Use this exact prompt:

> Please remove ClineFlow.

The agent first runs `./.clineflow/bin/uninstall --dry-run`, explains the managed files and rule blocks that would be removed and the knowledge and user content that would remain, and asks for explicit confirmation. Only that confirmation authorizes final removal; the initial prompt never bypasses the preview.

## Opening the Knowledge Visor through an agent

Use this exact prompt:

> Please show me the ClineFlow dashboard.

This explicitly authorizes dashboard generation, but first use still previews and approval-gates the optional pinned runtime and visual assets. Normal development and commit preparation never activate the visor proactively.

## Evidence-first examples

### Product capability

A team wants to add an export option. The specification records supported formats, permission boundaries, excluded formats, and unresolved retention rules. Verification defines example exports, access checks, and regression coverage for existing downloads. The journal explains why the format boundary exists; the indexes link to it.

### Production defect

A service intermittently returns duplicate notifications. The journal records the reproduction, hypothesis, chosen fix, and rollback consideration. Verification names the regression test and production signal that confirm the repair. The timeline links the incident, fix, test result, and deployment handoff.

### Dependency or platform migration

A project must move to a new runtime. Goals describe the migration outcome and compatibility deadline; specification preserves public behavior and states non-goals such as unrelated feature work. Verification lists build, test, deployment, and rollback criteria. The last-session index gives the next migration step and links to the detailed journal.

## Usage and cost ledger

Timeline events may include a `usage` object only when a provider, agent, API, or export explicitly supplies exact values. Record provider, model, input/output/reasoning tokens, cost, currency, source, and capture time. When exact values are unavailable, omit telemetry fields entirely. Existing `usage_capture: unavailable` fields remain valid historical data. Never estimate tokens or prices.

This rule is provider-neutral: Codex, Claude Code, Cline, Cursor, Copilot, Windsurf, and future agents can participate even when they expose different telemetry. Usage data is observational metadata, never proof of completion or a required workflow gate.

## Maintenance standard

Prefer a concise current state over a transcript. Preserve historical detail in journals and timeline events. Keep all claims factual, link evidence, and make the next recommended step specific enough for another person or agent to act safely.

Fresh ClineFlow installation initializes Git when the directory is not already a work tree and Git is available. It does not create a commit, remote, identity, or branch policy; the first commit remains a deliberate project decision.
