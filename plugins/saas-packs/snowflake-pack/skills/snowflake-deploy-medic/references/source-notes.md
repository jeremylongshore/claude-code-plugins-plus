# Research notes and primary sources

This skill addresses deployment pain that repeatedly creates production risk:
Terraform provider 2.x grant adoption and state drift, preview resource
instability, schemachange checksum/repeatable behavior, CLI/driver/BCR drift, and
the false confidence of a plan without a zero-change or tested rollback receipt.

The source hierarchy is:

1. Snowflake documentation, provider registry, and official release notes for
   current behavior and support boundaries.
2. Schemachange's maintained repository/release notes for its own checksum and
   migration behavior; it is community-developed, not a Snowflake support
   promise.
3. Redacted local plan/history/tool output for this exact deployment.

Primary links:

- [Snowflake Terraform provider](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs)
- [Schemachange](https://github.com/Snowflake-Labs/schemachange)
- [Schemachange troubleshooting](https://github.com/Snowflake-Labs/schemachange/blob/master/TROUBLESHOOTING.md)
- [Snowflake CLI release notes](https://docs.snowflake.com/en/release-notes/clients-drivers/snowflake-cli)
- [Snowflake client/driver release notes](https://docs.snowflake.com/en/release-notes/clients-drivers)
- [Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [Terraform import](https://developer.hashicorp.com/terraform/language/import)

Check live pages at execution time. Provider versions, CLI syntax, driver support,
behavior-change rollouts, and checksum fixes are time-sensitive facts.
