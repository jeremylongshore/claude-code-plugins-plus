# Snowflake CLI, drivers, and behavior-change review

Deployment incidents often come from a toolchain mismatch rather than the SQL
itself. Capture the actual Snowflake CLI, Python connector/JDBC/Node driver,
Terraform, schemachange, and runtime versions used by CI. Then check the live
primary release notes for each before approving a change.

## Snowflake CLI

The CLI has its own [release notes](https://docs.snowflake.com/en/release-notes/clients-drivers/snowflake-cli)
and current command/configuration reference. Do not assume that a command or
configuration key from an older `snow` release remains valid. Record the output
of the installed CLI version command without exposing connection details, and
run a non-mutating validation/SQL preview where the current CLI supports it.

## Drivers and authentication

Pin the driver in the application/CI lockfile, not in prose. Check its current
release notes for authentication, OCSP, TLS, Python/runtime, and breaking
changes. Prefer supported key-pair, OAuth, workload identity, or external-browser
flows; never log passwords, private keys, passphrases, or access tokens. A CLI
success does not prove that an application driver can authenticate with the same
account, role, warehouse, or network policy.

## Behavior-change releases (BCRs)

Snowflake behavior-change announcements are account/release-window facts. For a
deployment, record:

1. account release/deployment window and cloud/region;
2. BCR identifier, effective state, and whether it is enabled/disabled;
3. affected SQL/object/driver surface;
4. test evidence in a representative non-production account;
5. rollback or forward-fix owner and stop condition.

Never treat “we checked BCRs” as sufficient without the source URL/date and the
specific features reviewed. A current release note may supersede a copied
recommendation in this skill.

Primary routes: [Snowflake CLI release notes](https://docs.snowflake.com/en/release-notes/clients-drivers/snowflake-cli),
[client/driver release notes](https://docs.snowflake.com/en/release-notes/clients-drivers),
and [Snowflake release notes](https://docs.snowflake.com/en/release-notes).
