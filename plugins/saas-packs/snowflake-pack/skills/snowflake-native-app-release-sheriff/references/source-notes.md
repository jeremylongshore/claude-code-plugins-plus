# Primary Snowflake sources

Re-check these pages at execution time. Release-channel behavior, manifest
capabilities, security rules, and release notes are time-sensitive.

## Setup and upgrade semantics

- [Develop a new version of an app](https://docs.snowflake.com/en/developer-guide/native-apps/update-app-develop)
  states that a failed setup script is rerun from the beginning, so changes must
  be idempotent. It warns against `CREATE OR REPLACE APPLICATION ROLE` because
  replacement can remove account-role grants.
- [Create the setup script](https://docs.snowflake.com/en/developer-guide/native-apps/creating-setup-script)
  documents supported SQL, qualified object creation, idempotent forms, and the
  privilege-loss window created by replacing granted objects.
- [Upgrade an app using release channels](https://docs.snowflake.com/en/developer-guide/native-apps/release-channels-upgrade)
  documents queued upgrades, immediately-prior-version compatibility, running
  old code, failed-upgrade constraints, and delayed completion across consumers.

## Manifest, privileges, and App Specs

- [Manifest reference](https://docs.snowflake.com/en/developer-guide/native-apps/manifest-reference)
  defines manifest versions, artifact paths, requested privileges, references,
  roles, and lifecycle callbacks.
- [Configure privileges required by an app](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-auto-privs)
  documents manifest v2 automated privileges, patch restrictions, privilege
  removal timing, and the v2-to-v1 revocation consequence.
- [Use app specifications to request controlled access](https://docs.snowflake.com/en/developer-guide/native-apps/requesting-app-specs)
  documents controlled-access approval, definition sequence numbers, and
  approval/decline callbacks.

## Scans and channels

- [Run the automated security scan](https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan)
  defines `NOT_REVIEWED`, `IN_PROGRESS`, `APPROVED`, and `REJECTED`, and states
  that ALPHA or DEFAULT initiates scanning while QA alone does not.
- [Publish using release channels](https://docs.snowflake.com/en/developer-guide/native-apps/release-channels)
  documents registration, channel membership, read-only monitoring surfaces, the
  two-version-per-channel limit, scan initiation, and asynchronous removal.
- [About release channels, versions, and patches](https://docs.snowflake.com/en/developer-guide/native-apps/release-channels-versions)
  distinguishes channel scope and version versus patch compatibility.
- [SHOW VERSIONS IN APPLICATION PACKAGE](https://docs.snowflake.com/en/sql-reference/sql/show-versions)
  is the provider-side read-only source for version state and `review_status`.
- [Snowflake 9.12 release notes](https://docs.snowflake.com/en/release-notes/2025/9_12)
  record release channels becoming generally available. Review newer Native App
  release notes for the target account window before approving a release.

The analyzer requires source-review topics rather than trusting a bundled date as
current. Every topic must point to `https://docs.snowflake.com/` and be reviewed
within the evidence window.
