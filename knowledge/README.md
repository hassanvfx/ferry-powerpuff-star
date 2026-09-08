---
type: Guide
title: "ClineFlow 3 knowledge sources"
description: "Explains tenant-scoped source records and local projections."
---

# ClineFlow 3 knowledge sources

`knowledge/updates/` contains immutable, tenant-scoped update records. New task
journals live under `knowledge/journals/<topic>/` and carry their opaque tenant
author and stream UUID in OKF frontmatter.

Run `./.clineflow/bin/knowledge sync` before reading the familiar five ledger
views. The ledgers, log, and journal/topic indexes are local projections and
are intentionally ignored by Git. Browse the journals and update records
directly when a projection is unavailable.

Use `./.clineflow/bin/knowledge identity show` to inspect the local tenant;
only `identity set` changes a pinned tenant identity.
