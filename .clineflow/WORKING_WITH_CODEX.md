# Working with ChatGPT Codex

ClineFlow gives ChatGPT Codex persistent project context through the repository's shared `AGENTS.md` instructions and the native OKF bundle in `knowledge/`. Read `.clineflow/PROCEDURES.md` as the operational reference. It does not require a Codex plugin, SDK, or runtime.

## Start or resume a task

1. Run `./.clineflow/bin/knowledge sync`, then read `AGENTS.md`, `.clineflow/PROCEDURES.md`, `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five generated `knowledge/clineflow_*.yml` views.
2. Follow the indexes' relevant journal references, then search `knowledge/` for related concepts. When present, search `docs/journals/` as read-only legacy context too.
3. Summarize the relevant context before changing code. For a substantial change, propose a concise implementation plan first.
4. Inspect topics, then create a tenant-scoped stream or explicitly resume a known stream with `./.clineflow/bin/knowledge journal`.

## Work and deliver

- Keep the active tenant Engineering Journal current with decisions, implementation notes, verification evidence, issues, and next steps. Publish one immutable update record per knowledge change and rebuild projections with `knowledge sync`.
- Before a substantial slice, record its contract, boundary, handoff topology, relevant existing approaches, and planned proof. Use one handoff only for one cohesive, independently verifiable slice; otherwise use linked milestone streams with explicit boundaries, local proof, dependencies, and a named integrator responsible for composition and final end-to-end proof. Choose reversible details within the authorized contract; ask before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria.
- Treat deterministic commands as evidence for the rules they encode, not proof that the contract is complete. Record integration checks and any remaining judgment with their factual outcomes.
- Never edit or delete a published update record; publish a corrective record that references it.
- Before delivery, run `./.clineflow/bin/validate-okf`, `./.clineflow/bin/validate-knowledge-sync`, the relevant project tests, and `git diff --check`.
- When the user says “Please commit.” or otherwise asks to commit, stage code and knowledge together, require `./.clineflow/bin/validate-knowledge-sync --staged` to pass, then commit.

## Useful prompts for Codex

**Start work**

> Read `AGENTS.md` and `knowledge/index.md`, search relevant journals, summarize the current context, and propose the next safe step.

**Resume work**

> Find the active Engineering Journal in `knowledge/journals/`, inspect its next steps and related knowledge, then continue from the documented state.

**Close a task**

> Update the active Engineering Journal, reconcile all five ledgers and `knowledge/log.md`, run the OKF and knowledge-sync validators plus relevant tests, then show me the delivery summary.

**Update ClineFlow**

> Please update ClineFlow.

This prompt authorizes Codex to read the current repository instructions and immediately invoke `curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes`. Do not run any existing local updater first; legacy copies can overwrite themselves. Codex must wait for verification or rollback to finish and report the outcome; it must still stop on safety failures or requests for unrelated system changes.

**Remove ClineFlow**

> Please remove ClineFlow.

Codex first runs `./.clineflow/bin/uninstall --dry-run`, explains what will be removed and preserved, and asks for explicit confirmation. Only after confirmation may it run the remover; `--yes` is valid only when the final removal has been authorized.

**Open the Knowledge Visor**

> Please show me the ClineFlow dashboard.

Only this explicit request, a direct Knowledge Visor request, or a direct `./.clineflow/bin/dashboard` command activates the optional dashboard. When responding to the natural-language request, collect facts into temporary storage, read them, author a source-linked insights JSON when grounded observations or delivery assumptions are available, then run `dashboard observe` and `dashboard render`. The direct CLI command remains the intentional no-insights fallback. First use displays and approval-gates every runtime and visual-asset download. Ordinary ClineFlow work never installs or runs the visor.

## Diagnose the setup

Run `./.clineflow/bin/doctor` after installation or when Codex does not appear to have project context. It checks the shared instructions, required OKF files, Git repository, and structural validation without installing anything.
