#!/usr/bin/env python3
"""resolve-creds-ref.py — resolve a connection-descriptor `creds-ref` to a secret.

A `creds-ref` is a POINTER to a secret, never the secret itself (blueprint §2 /
the panel's creds-ref MAJOR). Accepted schemes:

  env:NAME            environment variable NAME
  sops:PATH#KEY       KEY from a SOPS-encrypted file at PATH — decrypted to stdout
                      only, NEVER to disk (per the SOPS posture)
  pass:PATH           `pass show PATH`

Resolution is **fail-closed**:
  * an unknown scheme exits non-zero (this is the validator rule — a `creds-ref`
    that is not a known `scheme:` prefix is rejected, never silently treated as a
    literal);
  * an empty/unresolved secret for a NON-loopback endpoint exits non-zero — we
    never connect a remote endpoint with an empty (unauthenticated) password;
  * for a loopback endpoint (127.0.0.1 / localhost / ::1) an empty result IS
    allowed — bd's local dolt server is unauthenticated by default.

The resolved secret is printed to stdout for capture into an env var:
  export DOLT_PASSWORD="$(resolve-creds-ref.py --creds-ref env:DOLT_PASSWORD --endpoint 127.0.0.1:3308)"
NEVER echo or log the captured value.

Exit: 0 ok (secret on stdout; may be empty for loopback) · 2 bad usage /
      unknown scheme · 4 resolution failed (fail-closed).
"""
import argparse
import os
import subprocess
import sys

KNOWN_SCHEMES = ("env", "sops", "pass")
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", ""}


def eprint(*a):
    print(*a, file=sys.stderr)


def is_loopback(endpoint):
    host = (endpoint or "").strip()
    if host.startswith("["):                      # [::1]:3306
        host = host[1:].split("]", 1)[0]
    elif host.count(":") == 1:                     # host:port
        host = host.rsplit(":", 1)[0]
    return host.lower() in _LOOPBACK_HOSTS


def parse_scheme(ref):
    if ":" not in ref:
        return None, None
    scheme, rest = ref.split(":", 1)
    return scheme.lower(), rest


def resolve_env(rest):
    return os.environ.get(rest, "")


def resolve_pass(rest):
    try:
        out = subprocess.run(["pass", "show", rest], capture_output=True,
                             text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ""
    if out.returncode != 0:
        return ""
    return out.stdout.splitlines()[0] if out.stdout else ""


def resolve_sops(rest):
    if "#" not in rest:
        eprint("error: sops ref must be 'sops:PATH#KEY'")
        return None  # signals usage error
    path, key = rest.rsplit("#", 1)
    # dotenv files: decrypt as dotenv, then read KEY=VALUE. Structured (yaml/json):
    # use --extract for a single value. Both stream to stdout only (never to disk).
    is_dotenv = path.endswith((".env", ".env.sops")) or ".env" in os.path.basename(path)
    try:
        if is_dotenv:
            out = subprocess.run(["sops", "-d", "--input-type", "dotenv",
                                  "--output-type", "dotenv", path],
                                 capture_output=True, text=True, timeout=30)
            if out.returncode != 0:
                return ""
            for line in out.stdout.splitlines():
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
            return ""
        out = subprocess.run(["sops", "-d", "--extract", f'["{key}"]', path],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def resolve(ref):
    """Return (secret, ok). ok=False on unknown scheme / usage error."""
    scheme, rest = parse_scheme(ref)
    if scheme not in KNOWN_SCHEMES:
        eprint(f"error: unknown creds-ref scheme '{scheme}'. "
               f"Accepted: {', '.join(s + ':' for s in KNOWN_SCHEMES)}")
        return None, False
    if scheme == "env":
        return resolve_env(rest), True
    if scheme == "pass":
        return resolve_pass(rest), True
    secret = resolve_sops(rest)
    if secret is None:        # sops usage error
        return None, False
    return secret, True


def main():
    ap = argparse.ArgumentParser(description="resolve a descriptor creds-ref (fail-closed)")
    ap.add_argument("--creds-ref", required=True, help="env:NAME | sops:PATH#KEY | pass:PATH")
    ap.add_argument("--endpoint", default=os.environ.get("DOLT_ENDPOINT", "127.0.0.1:3308"),
                    help="host:port — loopback permits an empty secret")
    args = ap.parse_args()

    secret, ok = resolve(args.creds_ref)
    if not ok:
        return 2
    if not secret:
        if is_loopback(args.endpoint):
            return 0  # empty is fine for a loopback (unauthenticated) server
        eprint(f"error: creds-ref '{args.creds_ref}' resolved empty for non-loopback "
               f"endpoint '{args.endpoint}' — refusing to connect unauthenticated (fail-closed).")
        return 4
    sys.stdout.write(secret)
    return 0


if __name__ == "__main__":
    sys.exit(main())
