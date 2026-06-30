"""profile_sql.py — build the version-control audit SQL from a schema PROFILE.

This is the seam that proves the use-case-adapter inversion (the panel's
schema-profile MAJOR / §9): the generic queries (epic-closure drift, dependency
bottlenecks) are emitted from a profile's table/column/encoding/value names, so a
SECOND schema (profiles/example-generic.profile.json) runs the same logic with
zero code change. `beads` stops being hardcoded and becomes profile #1.

A profile is untrusted INPUT — names are quoted as identifiers and the type-value
is quoted as a literal, so a malicious profile cannot inject SQL. (Live schema
introspection still wins over the profile at agent runtime.)

Pure stdlib; importable for tests.
"""
import json
import re

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


def load_profile(path):
    with open(path) as fh:
        return json.load(fh)


def _ident(name):
    """Validate a table/column identifier and return it bare. Rejects anything that
    is not a plain identifier, so a hostile profile cannot smuggle SQL through a
    table/column name."""
    if not isinstance(name, str) or not _IDENT.match(name):
        raise ValueError(f"unsafe identifier in profile: {name!r}")
    return name


def _lit(value):
    """Single-quote a string literal, escaping embedded quotes."""
    if not isinstance(value, str):
        raise ValueError(f"non-string value in profile: {value!r}")
    return "'" + value.replace("'", "''") + "'"


def _enc(profile, key):
    enc = profile["encodings"][key]
    return enc, enc.get("value", key)   # type-column value defaults to the encoding key


def epic_closure_sql(profile):
    """OPEN epics whose entire parent-child child set is already closed."""
    issues = _ident(profile["tables"]["issues"])
    deps = _ident(profile["tables"]["dependencies"])
    col_id = _ident(profile["columns"]["id"])
    col_status = _ident(profile["columns"]["status"])
    col_type = _ident(profile["columns"]["type"])
    col_itype = _ident(profile["columns"]["issue_type"])
    pc, pc_val = _enc(profile, "parent-child")
    child = _ident(pc["child"])
    parent = _ident(pc["parent"])
    closed = _lit(profile["closed-value"])
    epic = _lit(profile["epic-value"])
    pc_lit = _lit(pc_val)
    return (
        f"SELECT e.{col_id} AS epic, COUNT(d.{child}) AS children, "
        f"SUM(CASE WHEN c.{col_status}={closed} THEN 1 ELSE 0 END) AS closed "
        f"FROM {issues} e "
        f"JOIN {deps} d ON d.{parent}=e.{col_id} AND d.{col_type}={pc_lit} "
        f"JOIN {issues} c ON c.{col_id}=d.{child} "
        f"WHERE e.{col_itype}={epic} AND e.{col_status}<>{closed} "
        f"GROUP BY e.{col_id} "
        f"HAVING children>0 AND closed=children "
        f"ORDER BY children DESC"
    )


def bottleneck_sql(profile, top=10):
    """OPEN issues blocking the most other OPEN issues (the `blocks` encoding)."""
    if not isinstance(top, int) or isinstance(top, bool) or top < 1:
        raise ValueError("top must be a positive integer")
    issues = _ident(profile["tables"]["issues"])
    deps = _ident(profile["tables"]["dependencies"])
    col_id = _ident(profile["columns"]["id"])
    col_status = _ident(profile["columns"]["status"])
    col_type = _ident(profile["columns"]["type"])
    bl, bl_val = _enc(profile, "blocks")
    blocked = _ident(bl["blocked"])
    blocker = _ident(bl["blocker"])
    closed = _lit(profile["closed-value"])
    bl_lit = _lit(bl_val)
    return (
        f"SELECT b.{col_id} AS blocker, b.{col_status} AS status, COUNT(*) AS blocking_open "
        f"FROM {deps} d "
        f"JOIN {issues} b ON b.{col_id}=d.{blocker} "
        f"JOIN {issues} blocked ON blocked.{col_id}=d.{blocked} "
        f"WHERE d.{col_type}={bl_lit} AND b.{col_status}<>{closed} "
        f"AND blocked.{col_status}<>{closed} "
        f"GROUP BY b.{col_id}, b.{col_status} "
        f"ORDER BY blocking_open DESC LIMIT {top}"
    )
