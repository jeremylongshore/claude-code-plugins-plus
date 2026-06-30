"""sql_classifier.py — verb-class statement classifier (the mutation chokepoint).

This is the heart of blueprint §3 / D4 blocker B1. Every SQL statement that the
plugin runs through `dolt-mcp-client.py` is classified into one of three verb
classes and gated *before* it reaches the dolt-mcp server:

  read              SELECT / SHOW / DESCRIBE / EXPLAIN / dolt read table-funcs …
                    -> executes freely.
  safe-write        INSERT / UPDATE / DELETE / CREATE TABLE / CALL DOLT_COMMIT …
                    -> executes ONLY on an agent-owned branch (never `main`) and
                       ONLY with --allow-mutation; refused on pre-GA flavors.
  history-affecting CALL DOLT_PUSH / DOLT_MERGE / DOLT_RESET('--hard') /
                    branch-delete / DROP DATABASE / unknown CALL …
                    -> ALWAYS refused (recommend-only; a human runs it).

Why a *statement* classifier and not a tool allowlist: `query`/`exec` is a single
MCP tool that carries every SQL verb, so excluding "history-affecting tools" from
an agent grant does nothing — the dangerous verbs ride inside the one allowed
tool. The gate therefore has to read the statement, not the tool name.

Design bias is fail-safe: anything we cannot positively prove is a read is
treated as at least safe-write, and any unrecognized `CALL …` (especially an
unrecognized `CALL DOLT_*`) is treated as history-affecting. A multi-statement
batch is classified at the severity of its most dangerous statement. Comments are
stripped before classification so `/* */`-hidden or `--`-trailing verbs cannot
slip a mutation past a read-looking prefix.

Pure stdlib; importable (no side effects on import) so it can be unit-tested
directly.
"""
import re

READ = "read"
SAFE_WRITE = "safe-write"
HISTORY_AFFECTING = "history-affecting"

# Severity ordering for batch (max-wins) classification.
_SEVERITY = {READ: 0, SAFE_WRITE: 1, HISTORY_AFFECTING: 2}

# Leading keywords that are unambiguously read-only.
_READ_LEADERS = {
    "SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "USE", "VALUES", "TABLE",
    "HELP", "PREPARE", "EXECUTE", "DEALLOCATE",
}
# `SET` is session config (read-class for our purposes); `SET PASSWORD`/`SET GLOBAL`
# are handled as exceptions below.
_READ_SET_EXCEPTIONS = ("PASSWORD", "GLOBAL")

# Leading keywords that mutate the working set / commit on a branch. Recoverable
# through Dolt history as long as no history-affecting op runs, so: safe-write.
_SAFE_WRITE_LEADERS = {
    "INSERT", "UPDATE", "DELETE", "REPLACE", "MERGE", "TRUNCATE",
    "CREATE", "ALTER", "RENAME", "ANALYZE", "LOAD", "IMPORT",
}

# Leading keywords that are destructive/admin and never safe from an agent.
_HISTORY_LEADERS = {
    "GRANT", "REVOKE", "FLUSH", "SHUTDOWN", "KILL", "RESET", "PURGE",
    "LOCK", "UNLOCK", "INSTALL", "UNINSTALL", "BACKUP", "RESTORE",
}

# CALL DOLT_* procedure verb-classes. Anything not listed -> history-affecting.
_DOLT_PROC_CLASS = {
    "DOLT_COMMIT": SAFE_WRITE,
    "DOLT_ADD": SAFE_WRITE,
    "DOLT_CHECKOUT": SAFE_WRITE,   # incl. -b create; switches working set, non-destructive
    "DOLT_BRANCH": SAFE_WRITE,     # create/list; delete is special-cased below
    "DOLT_TAG": SAFE_WRITE,        # create; delete is special-cased below
    "DOLT_FETCH": SAFE_WRITE,      # network read + remote-tracking refs; no local rewrite
    "DOLT_REMOTE": SAFE_WRITE,     # add/list; remove is non-destructive to data
    "DOLT_VERIFY_CONSTRAINTS": SAFE_WRITE,
    # --- history-affecting (always recommend-only) ---
    "DOLT_PUSH": HISTORY_AFFECTING,
    "DOLT_PULL": HISTORY_AFFECTING,
    "DOLT_MERGE": HISTORY_AFFECTING,
    "DOLT_REVERT": HISTORY_AFFECTING,
    "DOLT_CHERRY_PICK": HISTORY_AFFECTING,
    "DOLT_REBASE": HISTORY_AFFECTING,
    "DOLT_CLEAN": HISTORY_AFFECTING,   # discards uncommitted working changes
    "DOLT_GC": HISTORY_AFFECTING,
    "DOLT_PURGE_DROPPED_DATABASES": HISTORY_AFFECTING,
    # DOLT_RESET handled specially (soft vs hard) below.
}

_LEADING_TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_CALL_PROC = re.compile(r"^CALL\s+([A-Za-z_][A-Za-z_0-9]*)", re.IGNORECASE)
# A complete quoted `-d` / `-D` / `--delete` flag arg inside a CALL DOLT_BRANCH /
# DOLT_TAG list — matched as a whole quoted token so a branch literally named
# e.g. '-delete-me' does not trip it.
_DELETE_FLAG = re.compile(r"""['"]\s*--?(?:delete|d)\s*['"]""", re.IGNORECASE)
_WRITE_VERB_ANYWHERE = re.compile(r"\b(INSERT|UPDATE|DELETE|REPLACE|MERGE)\b", re.IGNORECASE)


def strip_sql_comments(sql):
    """Remove `/* */`, `--`, and `#` comments so a verb hidden behind a comment
    cannot mask the real leading verb — while preserving string literals, so a
    `--`/`#` *inside* a quoted value (e.g. `DOLT_RESET('--hard')`) is NOT mistaken
    for a comment. Quote-aware with backslash- and doubled-quote escapes."""
    out = []
    i, n, quote = 0, len(sql), None
    while i < n:
        ch = sql[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:        # backslash escape inside a string
                out.append(sql[i + 1]); i += 2; continue
            if ch == quote:
                if i + 1 < n and sql[i + 1] == quote:   # doubled-quote escape ('')
                    out.append(sql[i + 1]); i += 2; continue
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch; out.append(ch); i += 1; continue
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":   # block comment
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
            out.append(" "); continue
        if (ch == "-" and i + 1 < n and sql[i + 1] == "-") or ch == "#":   # line comment
            j = sql.find("\n", i)
            i = n if j == -1 else j
            out.append(" "); continue
        out.append(ch); i += 1
    return "".join(out)


def split_statements(sql):
    """Naive `;` split (ignoring `;` inside quotes). Conservative: when in doubt a
    fragment is classified, and the batch takes the max severity, so an over-split
    never *lowers* the verdict."""
    out, buf, quote = [], [], None
    for ch in sql:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif ch == ";":
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return [s for s in (frag.strip() for frag in out) if s]


def _classify_call(stmt_upper):
    m = _CALL_PROC.match(stmt_upper)
    if not m:
        return HISTORY_AFFECTING  # CALL with no resolvable proc name -> deny
    proc = m.group(1).upper()
    if proc == "DOLT_RESET":
        return HISTORY_AFFECTING if "HARD" in stmt_upper else SAFE_WRITE
    if proc in ("DOLT_BRANCH", "DOLT_TAG") and _DELETE_FLAG.search(stmt_upper):
        return HISTORY_AFFECTING  # branch/tag deletion erases a ref
    if proc.startswith("DOLT_"):
        return _DOLT_PROC_CLASS.get(proc, HISTORY_AFFECTING)
    # Non-dolt stored procedure: unknown effect -> deny from an agent context.
    return HISTORY_AFFECTING


def classify_statement(sql):
    """Classify a single SQL statement into read / safe-write / history-affecting."""
    stmt = strip_sql_comments(sql).strip().lstrip("(").strip()
    if not stmt:
        return READ
    m = _LEADING_TOKEN.match(stmt)
    if not m:
        return SAFE_WRITE  # cannot identify a leading keyword -> not provably read
    lead = m.group(0).upper()
    stmt_upper = stmt.upper()

    if lead == "CALL":
        return _classify_call(stmt_upper)

    if lead == "WITH":
        # A CTE wraps either a read (SELECT) or a write (INSERT/UPDATE/DELETE/...).
        return SAFE_WRITE if _WRITE_VERB_ANYWHERE.search(stmt) else READ

    if lead == "SET":
        return SAFE_WRITE if any(x in stmt_upper for x in _READ_SET_EXCEPTIONS) else READ

    if lead == "DROP":
        # DROP DATABASE/SCHEMA/USER rewrites/erases beyond version control; other
        # DROPs (TABLE/VIEW/INDEX/TRIGGER) are recoverable via Dolt history.
        if re.match(r"DROP\s+(DATABASE|SCHEMA|USER|ROLE)\b", stmt_upper):
            return HISTORY_AFFECTING
        return SAFE_WRITE

    if lead == "CREATE":
        if re.match(r"CREATE\s+(USER|ROLE)\b", stmt_upper):
            return HISTORY_AFFECTING
        return SAFE_WRITE

    if lead in _READ_LEADERS:
        return READ
    if lead in _HISTORY_LEADERS:
        return HISTORY_AFFECTING
    if lead in _SAFE_WRITE_LEADERS:
        return SAFE_WRITE

    # Unknown leading keyword: not provably read -> require the mutation gate.
    return SAFE_WRITE


def classify_sql(sql):
    """Classify a (possibly multi-statement) SQL string at its max severity."""
    statements = split_statements(strip_sql_comments(sql))
    if not statements:
        return READ
    worst = READ
    for stmt in statements:
        cls = classify_statement(stmt)
        if _SEVERITY[cls] > _SEVERITY[worst]:
            worst = cls
    return worst


def gate_decision(sql, allow_mutation, branch, maturity):
    """Decide whether a SQL string may run, and why.

    Returns (allowed: bool, verb_class: str, reason: str).

    Rules (blueprint §3):
      * history-affecting  -> always refused (recommend-only).
      * pre-GA maturity (alpha/experimental) -> only `read` is allowed at all.
      * safe-write         -> allowed only with allow_mutation AND a non-main,
                              non-empty branch (agent/<task>).
      * read               -> always allowed.
    """
    verb = classify_sql(sql)
    maturity = (maturity or "ga").strip().lower()
    pre_ga = maturity in ("alpha", "experimental")

    if verb == HISTORY_AFFECTING:
        return (False, verb,
                "history-affecting statements are recommend-only — a human runs "
                "merge/push/--force/reset --hard/branch-delete/DROP DATABASE, never "
                "an agent. Surface the command for the operator instead of executing it.")

    if verb == SAFE_WRITE:
        if pre_ga:
            return (False, verb,
                    f"maturity '{maturity}' is pre-GA: this flavor is read-only until "
                    "dolt-watch reports it has reached GA. No writes, even on a branch.")
        if not allow_mutation:
            return (False, verb,
                    "safe-write requires --allow-mutation (the agent default is read-only).")
        b = (branch or "").strip()
        if not b or b.lower() == "main":
            return (False, verb,
                    "safe-write must target an agent-owned branch (--branch agent/<task>), "
                    "never `main`.")
        return (True, verb, f"safe-write permitted on branch '{b}'.")

    return (True, verb, "read.")
