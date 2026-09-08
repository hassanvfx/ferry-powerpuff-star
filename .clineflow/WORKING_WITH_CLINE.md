# Working with ClineFlow

ClineFlow stores new persistent context as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) v0.2 bundle in `knowledge/`. Read `.clineflow/PROCEDURES.md` as the operational workflow.

## Daily workflow

1. Ask the agent to run `./.clineflow/bin/knowledge sync`, then inspect `.clineflow/PROCEDURES.md`, `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five generated ledger views before starting work.
2. For a substantial task, create a tenant-scoped stream with `knowledge journal new` or explicitly resume a known stream.
3. Keep decisions, testing evidence, progress, and next steps in that concept. Publish immutable update records that explicitly review all five ledgers, then rebuild local views with `knowledge sync`.
4. When the user says “Please commit.” or otherwise asks to commit, update `knowledge/log.md`, run `./.clineflow/bin/validate-okf` and `./.clineflow/bin/validate-knowledge-sync`, stage code plus knowledge together, and require `./.clineflow/bin/validate-knowledge-sync --staged` to pass before committing.

For a substantial slice, have the agent record the task contract, execution boundary, handoff topology, existing approaches considered, and planned proof before implementation. A single handoff fits one cohesive, independently verifiable slice; otherwise use linked milestone streams with explicit boundaries, local proof, dependencies, and one integrator responsible for composition and final end-to-end proof. The agent may choose reversible details within the authorized contract, but must ask before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria. Deterministic checks provide evidence for encoded rules; integration checks and remaining judgment stay explicit.

## Legacy journal discovery

Projects may have pre-OKF journals in `docs/journals/`. ClineFlow searches these files for historical context when they exist, but does not modify, migrate, or validate them. All new task documentation belongs in `knowledge/journals/`.

## Update ClineFlow

Tell your agent: “Please update ClineFlow.” The agent reads the current instructions from the authoritative repository and immediately runs `curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes` without asking again. Do not run any existing local updater first; legacy copies can overwrite themselves. It reports the installed version and any preserved legacy artifacts after verification or rollback completes.

## Remove ClineFlow

Tell your agent: “Please remove ClineFlow.” The agent first runs `./.clineflow/bin/uninstall --dry-run`, explains what the remover will delete and preserve, and asks for explicit confirmation. Only after confirmation may it apply the removal; the initial phrase never authorizes bypassing the preview.

## Knowledge Visor

Say “Please show me the ClineFlow dashboard.” to explicitly invoke the optional time-first knowledge visor. An agent handling that request collects facts to temporary storage, reads them, prepares source-linked insights when grounded narrative observations or delivery assumptions are available, then observes and renders the report. A direct CLI invocation remains the no-insights fallback. The first request previews and approval-gates its isolated runtime and pinned visual assets. ClineFlow does not install, update, or run those optional components during normal operation.

## Related projects

Keep related codebases as sibling folders beneath one common parent directory. When cross-project context is needed, ask the agent to inspect “sibling project `<foldername>`” (for example, `../backend-api`). This convention needs no ClineFlow configuration, symlinks, or generated workspace file.
