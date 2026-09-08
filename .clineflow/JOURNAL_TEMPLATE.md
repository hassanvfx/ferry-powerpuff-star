# Legacy Journal Template Notice

New ClineFlow task journals are tenant-scoped OKF concepts in
`knowledge/journals/<topic>/`.

Create them with `./.clineflow/bin/knowledge journal new --topic <topic> --title
<title>`. New journals prompt for the task contract, execution boundary,
handoff topology, existing approaches, planned proof, and separate verification outcomes. Record
additive work with `knowledge record` and rebuild local ledger views with
`knowledge sync`. Existing files in `docs/journals/` remain supported as
read-only context and should not be converted automatically.
