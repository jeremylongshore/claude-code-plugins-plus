# Portable install integrity contracts

`portable-install-receipt-v1.schema.json` is the machine-readable contract for a
portable Agent Skill installed by `ccpi`. Version 1 is fail-closed: unknown schema
versions or fields require a newer reader and cannot inherit a verified status.
Its stable identifier is `urn:tonsofskills:schema:portable-install-receipt:v1`;
the package does not claim an unserved public schema URL.

## Canonical source selection

The source tree is the complete Git tree below `source.path`, read from the immutable
commit recorded by `source.commit`. `source.tree` records that path's Git tree object
ID. Implementations enumerate with `git ls-tree` and read exact blob bytes with
`git cat-file`, not mutable worktree or index bytes. A local acquisition is accepted
only when its checked-out HEAD equals the full commit ID and the source subtree has no
staged, modified, deleted, untracked, or ignored state.
The configured origin is normalized to a credential-free HTTPS identity and must
equal the receipt repository. An installer must acquire from that repository at that
commit; merely possessing an object in an unrelated local repository is insufficient.

Only a canonical first-party plugin skill path is eligible:
`plugins/<category>/<plugin>/skills/<skill>`. Root `skills/`, `skills/.curated/`,
arbitrary directories, and trees beneath a `.source.json` marker fail closed. The
root mirror remains an external discovery projection; it cannot become canonical by
appearing in a receipt.
The installed-tree verifier hashes every entry except the reserved receipt file
`.ccpi-portable-install.json`; an unexpected extra file is therefore local drift.

Only regular files are portable in v1. Symlinks (including in-tree links), gitlinks,
devices, sockets, and other special entries are refused before copy or hashing. This
keeps identity and installation behavior consistent on Windows, macOS, and Linux and
prevents a link from escaping either the source or destination root.
The contract caps a source at 10,000 files and 64 MiB of aggregate bytes.

Paths are relative POSIX paths made from conservative portable ASCII. Absolute,
drive, and UNC roots; backslashes; empty, `.` or `..` segments; controls and bidi
formatting; `.git`; Windows device names; trailing dots/spaces; and the reserved
receipt filename are forbidden. Duplicate, case-folded, and file/directory-prefix
collisions are refused. `SKILL.md` must exist at the tree root.

## Tree digest framing

Each file has `sha256:<lowercase hex>` over its exact bytes; text is not decoded and
binary files are not transformed. Entries are sorted by their normalized path's raw
UTF-8 bytes. The aggregate SHA-256 input is:

1. UTF-8 `portable-skill-tree/v1`, NUL, `sha256-tree-v1`, and NUL;
2. the entry count as an unsigned 64-bit big-endian integer;
3. for every entry: length-prefixed path UTF-8 bytes, length-prefixed normalized Git
   mode (`100644` or `100755`), exact byte size as unsigned 64-bit big-endian, the 32
   raw digest bytes, and byte `0xff` as an entry terminator.

Mtime, owner, group, checkout root, destination path, and host metadata never enter
the digest. A path, byte, or executable-mode change does. Installers must apply the
recorded regular-file mode explicitly; symlinks, gitlinks, and special files have no
portable v1 representation.

## Receipt trust boundary

The receipt records a credential-free HTTPS repository URL, a full Git SHA-1 or
SHA-256 commit object ID, repository-relative source path, harness and scope,
validator, skill-schema, and harness-registry versions, the complete tree manifest,
and content-addressed evidence references with hashes. A branch or tag may be
discovery metadata elsewhere, but it cannot replace the immutable commit in a valid
receipt.

No absolute source/destination path, home directory, username, credential, raw
evaluation payload, or runtime cache belongs in the receipt. Evidence uses matching
`urn:sha256:` identifiers and digests with indefinite retention. Those hashes are
content addresses, not signatures or independent trust anchors; later verification
policy must resolve them against retained evidence before awarding `verified` status.

The v1 reader accepts at most 1 MiB of valid UTF-8 and requires the exact minified
serialization produced by the contract writer. This makes duplicate JSON keys,
alternate key ordering, unknown fields, and noncanonical encodings fail closed. It
also bounds tree and evidence cardinality, recomputes the aggregate digest, and
rejects count, size, ordering, collision, and digest contradictions. Installed bytes
are then hashed independently and must reproduce that manifest. A locally edited
receipt can never establish upstream identity by self-assertion alone.

JSON Schema validation proves bounded wire shape only. Every consumer must also call
the semantic validator and bind the result to a clean immutable acquisition. Parsing
or schema-validating a receipt never grants a `verified` state by itself.
