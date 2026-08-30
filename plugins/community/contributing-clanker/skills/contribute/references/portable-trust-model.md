# Portable trust model

`contributing-clanker` separates authority so a community installer can choose
the smallest capability needed.

## Boundaries

1. `contribute` is stateless and read-only.
2. `contribute-prepare` writes only below two paths explicitly selected by the
   user through `CONTRIBUTE_STATE_DIR` and `CONTRIBUTE_WORKSPACE_DIR`.
3. `contribute-publish` may mutate GitHub only after presenting the exact target,
   command, content, and validation evidence and receiving fresh approval.
4. No skill treats another host's instruction files, agents, or approval identity
   as automatically authoritative.
5. No install or activation hook creates persistent state.

## Network surface

The only declared network destination is GitHub through the authenticated `gh`
CLI. Audit uses read operations. Prepare may read repository metadata and clone
an explicitly named repository into the configured workspace. Publish owns all
GitHub write operations.

## State surface

No default state or workspace path is assumed. A user opting into preparation
must set both variables explicitly:

```bash
export CONTRIBUTE_STATE_DIR=/path/inside/your/profile/contributing-clanker
export CONTRIBUTE_WORKSPACE_DIR=/path/inside/your/profile/contribution-worktrees
```

The setup script validates that both paths are absolute, non-root, distinct, and
not equal to the home directory before creating anything.
