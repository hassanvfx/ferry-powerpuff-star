---
description: Update ClineFlow through its permanent, verified remote bootstrap.
---

Treat this as an execution request. Run this command immediately, before checking tags, releases, or installed versions:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes
```

Do not use an existing local updater. Wait for completion, then run `cat .clineflow/VERSION` and report the command outcome and installed version. If execution is blocked, report the exact permission, network, or safety blocker; do not claim ClineFlow is up to date.
