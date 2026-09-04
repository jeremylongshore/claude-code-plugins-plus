from __future__ import annotations

import importlib.util
import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "collect_snowflake_evidence.py"
SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SYNC_SCRIPT = HERE.parent / "sync_bundled_collectors.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_bundled_collectors", SYNC_SCRIPT)
assert SYNC_SPEC and SYNC_SPEC.loader
SYNC_MODULE = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(SYNC_MODULE)

ADVERSARIAL_ERROR_VALUES = (
    ("Authorization: Basic dXNlcjpwYXNz", ("dXNlcjpwYXNz",)),
    ("Authorization: Bearer bearer-payload", ("bearer-payload",)),
    (
        'Authorization: Digest username="admin", response="digest-secret"',
        ("Digest", "admin", "digest-secret"),
    ),
    (
        'Digest username="digest-user", realm="prod", nonce="nonce-secret", response="digest-response-secret"',
        ("Digest", "digest-user", "nonce-secret", "digest-response-secret"),
    ),
    (
        "AWS4-HMAC-SHA256 Credential=AKIAREDACTIONTEST/20260901/us-east-1/snowflake/aws4_request, "
        "SignedHeaders=host;x-amz-date, Signature=aws-signature-secret",
        ("AWS4-HMAC-SHA256", "AKIAREDACTIONTEST", "aws-signature-secret"),
    ),
    (
        'OAuth oauth_consumer_key="oauth-key", oauth_nonce="oauth-nonce-secret", '
        'oauth_signature="oauth-signature-secret"',
        ("oauth-key", "oauth-nonce-secret", "oauth-signature-secret"),
    ),
    (
        'Digest username="folded-user",\r\n response="folded-digest-secret"',
        ("folded-user", "folded-digest-secret"),
    ),
    (
        'Digest charset=UTF-8, username="charset-user", response="charset-digest-secret"',
        ("charset-user", "charset-digest-secret"),
    ),
    (
        'Signature keyId="signing-key", algorithm="rsa-sha256", signature="bare-signature-secret"',
        ("signing-key", "bare-signature-secret"),
    ),
    (
        'ProofScheme nonce="proof-nonce-secret", signature="proof-signature-secret"',
        ("proof-nonce-secret", "proof-signature-secret"),
    ),
    (
        'ProofScheme alpha="arbitrary-one", omega="arbitrary-param-secret"',
        ("arbitrary-one", "arbitrary-param-secret"),
    ),
    ("PoP pop-bare-secret", ("pop-bare-secret",)),
    ("Mutual mutual-bare-secret", ("mutual-bare-secret",)),
    ("Authorization: TotallyNew opaque-bare-secret", ("TotallyNew", "opaque-bare-secret")),
    ("DPoP dpop.header.payload.signature", ("dpop.header.payload.signature",)),
    ("request failed using Bearer embedded-bearer-secret", ("embedded-bearer-secret",)),
    ("SCRAM-SHA-256 scram-bare-secret", ("SCRAM-SHA-256", "scram-bare-secret")),
    ("SCRAM-SHA-256 data=c2NyYW0tc2VjcmV0", ("SCRAM-SHA-256", "c2NyYW0tc2VjcmV0")),
    ("SCRAM-SHA-1 data=c2NyYW0tc2VjcmV0", ("SCRAM-SHA-1", "c2NyYW0tc2VjcmV0")),
    ("SCRAM-SHA-1 scram-sha1-token", ("SCRAM-SHA-1", "scram-sha1-token")),
    ("ProofScheme 1nonce=numeric-param-secret", ("ProofScheme", "numeric-param-secret")),
    (
        "VAPID t=vapid-token-secret,k=vapid-public-secret",
        ("VAPID", "vapid-token-secret", "vapid-public-secret"),
    ),
    ("HOBA result=hoba-result-secret", ("HOBA", "hoba-result-secret")),
    ("Bearer abcdefghijklmnopqrs", ("abcdefghijklmnopqrs",)),
    ("Bearer abc====", ("abc====",)),
    ("Proof-Scheme -nonce=hyphenparamsecret", ("Proof-Scheme", "hyphenparamsecret")),
    ("ProofScheme proof=proofsecret", ("ProofScheme", "proofsecret")),
    ('password="correct horse battery staple"', ("correct horse battery staple",)),
    ("password=correct horse battery staple tail-secret", ("correct horse battery staple tail-secret",)),
    ("token='quoted token with spaces'", ("quoted token with spaces",)),
    ("SELECT 1", ("SELECT 1",)),
    ("SELECT CURRENT_ROLE", ("SELECT CURRENT_ROLE",)),
    ("SELECT salary+bonus FROM payroll", ("salary+bonus", "FROM payroll")),
    ("SELECT CASE WHEN salary > 0 THEN bonus END FROM payroll", ("CASE WHEN", "THEN bonus")),
    ("SELECT (salary + bonus) FROM payroll", ("salary + bonus", "FROM payroll")),
    ("SELECT NOT is_deleted FROM payroll", ("NOT is_deleted", "FROM payroll")),
    ("SELECT salary > bonus FROM payroll", ("salary > bonus", "FROM payroll")),
    ("SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("; ; SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("SELECT :bind", ("SELECT :bind",)),
    ("SELECT ?", ("SELECT ?",)),
    ("SELECT (salary)+bonus FROM payroll", ("salary", "bonus", "FROM payroll")),
    ("SELECT (salary) FROM a", ("salary", "FROM a")),
    ("VALUES (1, 'values-secret')", ("VALUES (1", "values-secret")),
    ("VALUES (CURRENT_DATE())", ("VALUES", "CURRENT_DATE")),
    ("VALUES (TO_DATE('2026-01-01'))", ("VALUES", "2026-01-01")),
    ("VALUES (UPPER('private-value'))", ("VALUES", "private-value")),
    ("VALUES ((CURRENT_DATE()))", ("VALUES", "CURRENT_DATE")),
    ("LIST @prod_stage PATTERN='.*list-secret.*'", ("LIST @prod_stage", "list-secret")),
    ("SHOW TABLES", ()),
    ("SHOW COLUMNS IN TABLE payroll", ("SHOW COLUMNS IN TABLE payroll",)),
    ("SHOW FUTURE GRANTS IN SCHEMA prod", ("SHOW FUTURE GRANTS", "IN SCHEMA prod")),
    ("SHOW SECURITY INTEGRATIONS", ("SHOW SECURITY INTEGRATIONS",)),
    ("SHOW API INTEGRATIONS", ("SHOW API INTEGRATIONS",)),
    ("SHOW STORAGE INTEGRATIONS", ("SHOW STORAGE INTEGRATIONS",)),
    ("SHOW NOTIFICATION INTEGRATIONS", ("SHOW NOTIFICATION INTEGRATIONS",)),
    ("DESCRIBE TABLE payroll", ("DESCRIBE TABLE payroll",)),
    ("DESCRIBE SECRET oauth_secret", ("DESCRIBE SECRET", "oauth_secret")),
    ("DESCRIBE PASSWORD POLICY prod_policy", ("DESCRIBE PASSWORD POLICY", "prod_policy")),
    ("DESCRIBE API INTEGRATION prod_api", ("DESCRIBE API INTEGRATION", "prod_api")),
    ("DESC TABLE payroll", ("DESC TABLE payroll",)),
    ("USE ROLE ACCOUNTADMIN", ("USE ROLE ACCOUNTADMIN",)),
    ("TRUNCATE TABLE payroll", ("TRUNCATE TABLE payroll",)),
    ("INSERT INTO payroll VALUES (1)", ("INSERT INTO payroll",)),
    ("COPY FILES INTO @target_stage FROM @source_stage", ("COPY FILES INTO", "source_stage")),
    ("LS @prod_stage PATTERN='.*stage-secret.*'", ("LS @prod_stage", "stage-secret")),
    ("PUT file:///tmp/private.csv @prod_stage", ("file:///tmp/private.csv", "prod_stage")),
    ("PUT 'file:///tmp/private.csv' @prod_stage", ("file:///tmp/private.csv", "prod_stage")),
    ("/* incident */ DELETE FROM payroll WHERE ssn = 'row-secret'", ("DELETE FROM payroll", "row-secret")),
    ("DELETE /* incident-secret */ FROM payroll WHERE id = 7", ("incident-secret", "FROM payroll")),
    ("Statement: DELETE FROM payroll WHERE id = 7", ("DELETE FROM payroll", "WHERE id")),
    ("Failed statement: DELETE FROM payroll WHERE id = 7", ("DELETE FROM payroll", "WHERE id")),
    ("Error: SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("[ERROR] SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("ERROR - SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("Snowflake error: SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("ERROR -- SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("[ERROR] -- SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    ("Snowflake error -- SQL: SELECT salary FROM payroll", ("SELECT salary", "FROM payroll")),
    (
        "CREATE TEMPORARY TABLE temp_secret_table(id INT)",
        ("CREATE TEMPORARY TABLE", "temp_secret_table"),
    ),
    ("CREATE IF NOT EXISTS TABLE payroll(id INT)", ("CREATE IF NOT EXISTS", "payroll")),
    (
        "CREATE SECURITY INTEGRATION oidc TYPE=OAUTH",
        ("CREATE SECURITY INTEGRATION", "TYPE=OAUTH"),
    ),
    ("CREATE OR ALTER TABLE payroll(id INT)", ("CREATE OR ALTER TABLE", "payroll")),
    ("CREATE API INTEGRATION prod_api", ("CREATE API INTEGRATION", "prod_api")),
    ("ALTER TAG pii_tag SET COMMENT = 'tag-secret'", ("ALTER TAG", "tag-secret")),
    ("DROP HYBRID TABLE prod.customer_secret", ("DROP HYBRID TABLE", "customer_secret")),
    ("ALTER SESSION SET QUERY_TAG = 'secret'", ("ALTER SESSION", "QUERY_TAG")),
    ("BEGIN LET x := 1; RETURN x; END;", ("LET x", "RETURN x")),
    ("DECLARE x NUMBER; BEGIN LET x := 1; RETURN x; END;", ("DECLARE x", "RETURN x")),
    ("BEGIN INSERT INTO payroll VALUES (1); END;", ("INSERT INTO payroll", "VALUES (1)")),
    ("BEGIN CREATE TABLE payroll(id INT); END;", ("CREATE TABLE", "payroll")),
    ("BEGIN TRUNCATE TABLE payroll; END;", ("TRUNCATE TABLE", "payroll")),
    ("BEGIN SHOW TABLES; END;", ("BEGIN SHOW TABLES;",)),
    ("BEGIN DESCRIBE TABLE payroll; END;", ("DESCRIBE TABLE", "payroll")),
    ("BEGIN DESC TABLE payroll; END;", ("DESC TABLE", "payroll")),
    ("BEGIN VALUES (CURRENT_DATE()); END;", ("VALUES", "CURRENT_DATE")),
    ("BEGIN LIST @prod_stage; END;", ("LIST @prod_stage",)),
    ("BEGIN LS @prod_stage; END;", ("LS @prod_stage",)),
    ('{"hasPassword": "cli-password-secret"}', ("cli-password-secret",)),
    ('{"has_pat": "cli-pat-secret"}', ("cli-pat-secret",)),
    ('{"hasRsaPublicKey": "cli-rsa-secret"}', ("cli-rsa-secret",)),
    ('{"has-workload-identity": "cli-identity-secret"}', ("cli-identity-secret",)),
)

SELECT_BOUNDARY_SQL = (
    ("SELECT (salary) FROM a;", ("salary", "FROM a;")),
    ("SELECT (salary) FROM a WHERE", ("salary", "FROM a WHERE")),
    ("SELECT (salary) FROM the;", ("salary", "FROM the;")),
    ("Select (salary) from a;", ("salary", "from a")),
    ("Select (salary) from a where", ("salary", "from a where")),
    ("Show columns in table payroll", ("columns", "payroll")),
    ("SHOW TABLES IN ACCOUNT;", ("SHOW TABLES IN ACCOUNT;",)),
    ("show tables in schema secret_schema;", ("secret_schema",)),
    ("SHOW TABLES LIKE 'secret_pattern';", ("secret_pattern",)),
    ("SHOW TABLES STARTS WITH 'secret_prefix' LIMIT 10;", ("secret_prefix",)),
    ("Describe table payroll", ("Describe table payroll",)),
    ("DESCRIBE STORAGE INTEGRATION behavior", ("DESCRIBE STORAGE INTEGRATION behavior",)),
    ("Describe storage integration behavior", ()),
    ("Describe storage integration configuration", ()),
    ("select (salary) from schema.table", ("salary", "schema.table")),
    ("SELECT implicit_secret FROM payroll implicit_alias", ("implicit_secret", "implicit_alias")),
    ("SELECT bare_secret FROM a alias", ("bare_secret", "a alias")),
    (
        "SELECT outer_secret FROM (SELECT inner_secret FROM payroll) nested_alias",
        ("outer_secret", "inner_secret", "nested_alias"),
    ),
    (
        "SELECT table_secret FROM TABLE(RESULT_SCAN('query-secret')) result_alias",
        ("table_secret", "query-secret", "result_alias"),
    ),
    ("SELECT $1 FROM @stage_secret/path", ("@stage_secret/path",)),
    ("SELECT qualified_secret FROM db.schema.payroll p", ("qualified_secret", "db.schema.payroll")),
    (
        "SELECT $1 FROM @stage_secret/path (FILE_FORMAT => 'secret_format') staged",
        ("@stage_secret/path", "secret_format"),
    ),
    ("SELECT $1 FROM @stage_secret/path (PATTERN => 'secret.*')", ("@stage_secret/path", "secret.*")),
    (
        "SELECT lateral_secret FROM source, LATERAL FLATTEN(INPUT => source.payload) flattened",
        ("lateral_secret", "source.payload", "flattened"),
    ),
    (
        "SELECT table_lateral_secret FROM LATERAL TABLE(FLATTEN(INPUT => payload)) flattened",
        ("table_lateral_secret", "flattened"),
    ),
    (
        "SELECT travel_secret FROM payroll AT(TIMESTAMP => '2026-01-01') historical",
        ("travel_secret", "2026-01-01"),
    ),
    ("SELECT offset_secret FROM payroll AT(OFFSET => -60)", ("offset_secret", "OFFSET => -60")),
    (
        "SELECT before_secret FROM payroll BEFORE(STATEMENT => 'secret-query-id') prior",
        ("before_secret", "secret-query-id"),
    ),
    (
        "SELECT changes_secret FROM payroll CHANGES(INFORMATION => DEFAULT) "
        "AT(TIMESTAMP => '2026-01-01') END(TIMESTAMP => '2026-01-02')",
        ("changes_secret", "2026-01-01", "2026-01-02"),
    ),
    (
        "SELECT directory_secret FROM DIRECTORY(@directory_secret_stage)",
        ("directory_secret", "@directory_secret_stage"),
    ),
    ("SELECT union_left FROM payroll UNION SELECT union_right FROM archive", ("union_left", "union_right")),
    (
        "SELECT union_all_left FROM payroll UNION ALL SELECT union_all_right FROM archive",
        ("union_all_left", "union_all_right"),
    ),
    (
        "SELECT union_name_left FROM payroll UNION BY NAME SELECT union_name_right FROM archive",
        ("union_name_left", "union_name_right"),
    ),
    (
        "SELECT union_all_name_left FROM payroll UNION ALL BY NAME SELECT union_all_name_right FROM archive",
        ("union_all_name_left", "union_all_name_right"),
    ),
    (
        "SELECT union_parent_left FROM payroll UNION BY NAME (SELECT union_parent_right FROM archive);",
        ("union_parent_left", "union_parent_right"),
    ),
    (
        "(SELECT left_parent_secret FROM payroll) UNION BY NAME SELECT right_plain_secret FROM archive",
        ("left_parent_secret", "right_plain_secret"),
    ),
    (
        "(SELECT left_full_secret FROM payroll) UNION BY NAME (SELECT right_full_secret FROM archive);",
        ("left_full_secret", "right_full_secret"),
    ),
    (
        "((SELECT wrapped_left_secret FROM payroll) UNION ALL BY NAME (SELECT wrapped_right_secret FROM archive));",
        ("wrapped_left_secret", "wrapped_right_secret"),
    ),
    (
        "(WITH c AS (SELECT cte_inner_secret FROM payroll) "
        "SELECT cte_outer_secret FROM c) UNION SELECT cte_union_secret FROM archive",
        ("cte_inner_secret", "cte_outer_secret", "cte_union_secret"),
    ),
    (
        "(WITH c(value) AS ((SELECT cte_column_secret FROM payroll)) "
        "SELECT value FROM c) UNION (SELECT cte_right_secret FROM archive);",
        ("cte_column_secret", "cte_right_secret"),
    ),
    (
        "SELECT nested_left_secret FROM payroll UNION "
        "(SELECT nested_middle_secret FROM archive INTERSECT SELECT nested_right_secret FROM backup)",
        ("nested_left_secret", "nested_middle_secret", "nested_right_secret"),
    ),
    (
        "SELECT outer_set_secret FROM "
        "(SELECT set_left_secret FROM payroll UNION ALL SELECT set_right_secret FROM archive) combined",
        ("outer_set_secret", "set_left_secret", "set_right_secret"),
    ),
    (
        "SELECT intersect_left FROM payroll INTERSECT SELECT intersect_right FROM archive",
        ("intersect_left", "intersect_right"),
    ),
    ("SELECT except_left FROM payroll EXCEPT SELECT except_right FROM archive", ("except_left", "except_right")),
    ("SELECT minus_left FROM payroll MINUS SELECT minus_right FROM archive", ("minus_left", "minus_right")),
    (
        "SELECT pivot_secret FROM quarterly_sales PIVOT(SUM(private_amount) FOR quarter IN ('Q1', 'Q2')) pivoted",
        ("pivot_secret", "private_amount", "Q1"),
    ),
    (
        "SELECT unpivot_secret FROM quarterly_sales UNPIVOT(private_amount FOR quarter IN (q1, q2)) unpivoted",
        ("unpivot_secret", "private_amount", "q1"),
    ),
    (
        "SELECT unpivot_include_secret FROM quarterly_sales "
        "UNPIVOT INCLUDE NULLS(private_amount FOR quarter IN (q1, q2)) included",
        ("unpivot_include_secret", "private_amount", "q1"),
    ),
    (
        "SELECT unpivot_exclude_secret FROM quarterly_sales "
        "UNPIVOT EXCLUDE NULLS(private_amount FOR quarter IN (q1, q2)) excluded",
        ("unpivot_exclude_secret", "private_amount", "q1"),
    ),
    (
        "SELECT sample_secret FROM payroll TABLESAMPLE BERNOULLI(12.5)",
        ("sample_secret", "12.5"),
    ),
    (
        "SELECT seeded_sample_secret FROM payroll TABLESAMPLE BERNOULLI(10) SEED(4242)",
        ("seeded_sample_secret", "4242"),
    ),
    (
        "SELECT block_sample_secret FROM payroll TABLESAMPLE BLOCK (10) SEED(4242)",
        ("block_sample_secret", "4242"),
    ),
    (
        "SELECT repeatable_block_secret FROM payroll TABLESAMPLE BLOCK(25) REPEATABLE(8181)",
        ("repeatable_block_secret", "8181"),
    ),
    (
        "SELECT semantic_secret FROM "
        "SEMANTIC_VIEW(secret_db.secret_schema.secret_view METRICS revenue, private_margin)",
        ("semantic_secret", "secret_view", "private_margin"),
    ),
    (
        "SELECT semantic_fact_secret FROM SEMANTIC_VIEW(secret_db.secret_schema.secret_view FACTS private_orders)",
        ("semantic_fact_secret", "secret_view", "private_orders"),
    ),
    (
        "SELECT semantic_dimension_secret FROM "
        "SEMANTIC_VIEW(secret_db.secret_schema.secret_view DIMENSIONS private_customer)",
        ("semantic_dimension_secret", "secret_view", "private_customer"),
    ),
    (
        "SELECT semantic_combined_secret FROM SEMANTIC_VIEW(secret_db.secret_schema.secret_view "
        "FACTS private_orders DIMENSIONS private_customer)",
        ("semantic_combined_secret", "private_orders", "private_customer"),
    ),
    ("Select (salary) from a AS alias", ("salary", "AS alias")),
    ("select (salary) from a AS alias", ("salary", "AS alias")),
    ("SELECT (salary) FROM a,b", ("salary", "FROM a,b")),
    ("select (salary) from a join b on a.id=b.id", ("salary", "a.id")),
    ("SHOW STORAGE INTEGRATIONS LIKE 'integration-secret'", ("integration-secret",)),
    ("SHOW EXTERNAL ACCESS INTEGRATIONS", ("SHOW EXTERNAL ACCESS INTEGRATIONS",)),
    ("SHOW EXTERNAL ACCESS INTEGRATIONS LIKE 'external-secret'", ("external-secret",)),
    ("SHOW SEMANTIC VIEWS LIKE 'semantic-view-secret'", ("semantic-view-secret",)),
    ("SHOW EVENT TABLES LIKE 'event-table-secret'", ("event-table-secret",)),
    (
        "SHOW SEMANTIC DIMENSIONS IN secret_db.secret_schema.secret_view FOR METRIC private_metric",
        ("secret_view", "private_metric"),
    ),
    ("SHOW SEMANTIC FACTS IN DATABASE secret_fact_db", ("secret_fact_db",)),
    (
        "SHOW SEMANTIC METRICS IN SCHEMA secret_metric_db.secret_metric_schema",
        ("secret_metric_db", "secret_metric_schema"),
    ),
    ("SHOW TABLES HISTORY", ()),
    ("SHOW TABLES HISTORY LIMIT 10 FROM 'cursor-secret'", ("cursor-secret",)),
    ("SHOW GRANTS TO ROLE secret_role", ("secret_role",)),
    ("SHOW GRANTS ON TABLE secret_table", ("secret_table",)),
    ("SHOW GRANTS OF DATABASE ROLE secret_db_role", ("secret_db_role",)),
    ("SHOW FUTURE GRANTS IN SCHEMA secret_db.secret_schema", ("secret_db.secret_schema",)),
    ("DESCRIBE EXTERNAL TABLE secret_db.secret_schema.secret_table", ("secret_table",)),
    ("DESCRIBE FILE FORMAT secret_db.secret_schema.secret_format", ("secret_format",)),
    ("DESCRIBE DYNAMIC TABLE secret_db.secret_schema.secret_dynamic", ("secret_dynamic",)),
    ("DESCRIBE RESULT 'secret-query-id'", ("secret-query-id",)),
    ("DESCRIBE RESULT LAST_QUERY_ID()", ("LAST_QUERY_ID",)),
    ("DESCRIBE RESULT LAST_QUERY_ID(-2)", ("LAST_QUERY_ID",)),
    (
        "DESCRIBE FUNCTION secret_db.secret_schema.secret_fn(VARCHAR, NUMBER(10,2))",
        ("secret_fn", "NUMBER(10,2)"),
    ),
    ("DESCRIBE TABLE secret_db.secret_schema.secret_table TYPE=COLUMNS", ("secret_table", "TYPE=COLUMNS")),
    ("DESC TABLE secret_db.secret_schema.secret_table TYPE=STAGE", ("secret_table", "TYPE=STAGE")),
    ("DESCRIBE PROCEDURE secret_db.secret_schema.secret_proc(VARCHAR)", ("secret_proc",)),
    ("DESCRIBE MATERIALIZED VIEW secret_db.secret_schema.secret_view", ("secret_view",)),
    ("DESCRIBE ICEBERG TABLE secret_db.secret_schema.secret_iceberg", ("secret_iceberg",)),
    ("DESCRIBE HYBRID TABLE secret_db.secret_schema.secret_hybrid", ("secret_hybrid",)),
    ("DESCRIBE EVENT TABLE secret_db.secret_schema.secret_events", ("secret_events",)),
    ("DESCRIBE SEMANTIC VIEW secret_db.secret_schema.secret_semantic", ("secret_semantic",)),
    ("SHOW TABLES ->> SELECT pipe_show_secret FROM $1", ("pipe_show_secret",)),
    (
        "DESCRIBE TABLE secret_db.secret_schema.secret_table ->> SELECT pipe_desc_secret FROM $1",
        ("pipe_desc_secret", "secret_table"),
    ),
    ("ERROR: " * 17 + "SQL: SELECT wrapper_17_secret FROM payroll", ("wrapper_17_secret",)),
    ("ERROR: " * 1_000 + "SQL: SELECT wrapper_long_secret FROM payroll", ("wrapper_long_secret",)),
    ("(" * 17 + "SELECT query_wrapper_secret FROM payroll" + ")" * 17, ("query_wrapper_secret",)),
    ("(" * 1_100 + "SELECT token_cap_secret FROM payroll" + ")" * 1_100, ("token_cap_secret",)),
    ("Values (1)", ("Values (1)",)),
    ("Values (count + total)", ("count + total",)),
    ("Values ((count))", ("Values ((count))",)),
    ("Values (UPPER('private-value'))", ("private-value",)),
    ("Values (count,total);", ("Values (count,total);",)),
)
VALUES_EXPRESSION_SQL = tuple(
    (
        f"VALUES ({'(' * depth}{expression}{')' * depth})",
        forbidden,
    )
    for expression, forbidden in (
        ("'values-depth-secret'", ("values-depth-secret",)),
        (":private_bind", ("private_bind",)),
        ("UPPER('function-depth-secret')", ("function-depth-secret",)),
        ("TO_DATE('2026-01-01')", ("2026-01-01",)),
    )
    for depth in (0, 1, 2, 4, 8, 16, 64)
)
DIAGNOSTIC_WRAPPED_SQL = tuple(
    (
        f"{prefix}{label}: SELECT diagnostic_secret FROM payroll",
        ("diagnostic_secret", "FROM payroll"),
    )
    for prefix in (
        "ERROR: /* context */ ",
        "[ERROR] /* context */ ",
        "[SNOWFLAKE ERROR]: /* context */ ",
        "ERROR: -- context\n",
    )
    for label in ("SQL", "[QUERY]")
) + (
    (
        "ERROR: /* first */ [QUERY]: /* second */ SQL: SELECT fixed_point_secret FROM payroll",
        ("fixed_point_secret", "FROM payroll"),
    ),
)
ADVERSARIAL_ERROR_VALUES += SELECT_BOUNDARY_SQL + VALUES_EXPRESSION_SQL + DIAGNOSTIC_WRAPPED_SQL
ADVERSARIAL_ERROR_VALUES += (
    ("VALUES (", ("VALUES (",)),
    ("VALUES (" + "(" * 20_000, ("VALUES (",)),
    ("VALUES (" + ",".join("1" for _ in range(3_000)) + ")", ("VALUES (1",)),
)

SAFE_ERROR_VALUES = (
    "Basic authentication",
    "Bearer support",
    "DPoP enabled",
    "Mutual authentication",
    "Select (operator) from the plan...",
    "Values (count,total), not rates...",
    "OAuth flow-reviewed",
    "Signature algorithm=RSA was reviewed",
    "Values (count,total) were stable",
    "Select (operator) accounted for time",
    "Authentication status=healthy",
    "OAuth flow=reviewed",
    "Token count",
    "Request id=3,response=200",
    "Values (count) were stable",
    "Values (count)",
    "Values (count,total)",
    "Operator id=3",
    "Warehouse hash=abc",
    "Metric created=date",
    "realm=prod",
    "Select operator accounted for time.",
    "Show the operator timeline.",
    "Describe the incident clearly.",
    "Begin incident review and end after approval.",
    "Select (operator) from production was dominant.",
    "Show storage integrations were reviewed.",
    "Select (operator) from production remained dominant.",
    "Select (operator) from production remained dominant",
    "Select (operator) from production was dominant",
    "Select (operator) from the plan",
    "Show storage integrations were reviewed",
    "Show tables in account were reviewed",
    "Show tables like patterns were reviewed",
    "Show the operator timeline",
    "Describe the incident clearly",
    "Select union by name behavior remained stable.",
    "Select pivot behavior remained stable.",
    "Select tablesample behavior remained stable.",
    "Select semantic view metrics were reviewed.",
    "Describe event table behavior remained stable.",
    "Describe semantic view configuration remained stable.",
    "Select semantic view facts were reviewed.",
    "Select semantic view dimensions were reviewed.",
    "Select unpivot include nulls behavior remained stable.",
    "Select tablesample block behavior remained stable.",
    "Show semantic views were reviewed.",
    "Show event tables like patterns were reviewed.",
    "Select semantic view facts were reviewed",
    "Select semantic view dimensions were reviewed",
    "Select unpivot include nulls behavior remained stable",
    "Select tablesample block behavior remained stable",
    "Show semantic views were reviewed",
    "Show event tables like patterns were reviewed",
    "Show semantic dimensions in the dashboard for operators.",
    "Show semantic facts in reports were reviewed.",
    "Show semantic metrics in reports were reviewed.",
    "Show semantic dimensions in the dashboard for operators",
    "Show semantic facts in reports were reviewed",
    "Show semantic metrics in reports were reviewed",
)
SAFE_ERROR_VALUES += (
    tuple(
        f"{command} (operator) {from_word} production {predicate}{punctuation}"
        for command, from_word in (("Select", "from"), ("select", "from"), ("SELECT", "FROM"))
        for predicate in ("dominated runtime", "appeared dominant", "stayed stable", "remain stable")
        for punctuation in ("", ".")
    )
    + tuple(
        f"Describe storage integration {continuation}{punctuation}"
        for continuation in ("behavior for operators", "configuration for operators", "configuration remained stable")
        for punctuation in ("", ".")
    )
    + tuple(
        f"{command} storage integrations {tail}{punctuation}"
        for command in ("Show", "show", "SHOW")
        for tail in (
            "in the account",
            "on the dashboard",
            "to operators",
            "like patterns were reviewed",
            "like 'reviewed' to operators",
        )
        for punctuation in ("", ".")
    )
    + tuple(
        f"{command} {subject} {continuation}{punctuation}"
        for command in ("Describe", "describe", "DESCRIBE")
        for subject in ("external table", "file format", "dynamic table", "function", "result", "table")
        for continuation in ("behavior for operators", "configuration remained stable")
        for punctuation in ("", ".")
    )
    + tuple(
        f"{command} external access integrations {continuation}{punctuation}"
        for command in ("Show", "show", "SHOW")
        for continuation in ("were reviewed", "on the dashboard", "to operators")
        for punctuation in ("", ".")
    )
    + tuple(
        f"{command} {subject} {continuation}{punctuation}"
        for command in ("Describe", "describe", "DESCRIBE")
        for subject in ("procedure", "materialized view", "iceberg table", "hybrid table")
        for continuation in ("behavior for operators", "configuration remained stable")
        for punctuation in ("", ".")
    )
    + (
        "Show tables history was reviewed",
        "SHOW TABLES HISTORY was reviewed",
        "Show tables ->> selection was discussed",
        "Describe table behavior ->> selection was discussed",
        "Select union behavior was reviewed",
    )
)


class CollectorTests(unittest.TestCase):
    def test_sanitizers_are_bounded_total_functions_under_adversarial_shapes(self) -> None:
        class ExplodingString:
            def __str__(self) -> str:
                raise ValueError("must not escape")

        self.assertEqual(MODULE.sanitize_text(ExplodingString()), "[REDACTED_CREDENTIAL]")
        self.assertEqual(MODULE.sanitize_text("VALUES (" + "(" * 50_000), "[REDACTED_SQL]")
        self.assertEqual(len(MODULE.sanitize_text("ordinary-note " + "x" * 50_000)), 2000)

        for depth in range(80):
            statement = f"VALUES ({'(' * depth}'depth-secret'{')' * depth})"
            with self.subTest(depth=depth):
                self.assertEqual(MODULE.sanitize_text(statement), "[REDACTED_SQL]")

        cyclic: list[object] = []
        cyclic.append(cyclic)
        sanitized = MODULE.sanitize_output_tree({"nested": cyclic})
        self.assertIsInstance(sanitized, dict)
        self.assertIn("[REDACTED_CREDENTIAL]", json.dumps(sanitized))

        wide = list(range(MODULE.MAX_SANITIZE_TREE_NODES + 5_000))
        sanitized_wide = MODULE.sanitize_output_tree(wide)
        self.assertLessEqual(len(sanitized_wide), MODULE.MAX_SANITIZE_TREE_NODES)
        self.assertEqual(sanitized_wide[-1], "[REDACTED_CREDENTIAL]")
        with self.assertRaises(MODULE.CollectionError):
            MODULE.reject_secret_fields(wide)

    def test_installed_skills_bundle_the_canonical_collector(self) -> None:
        canonical = SCRIPT.read_bytes()
        canonical_sql = {path.name: path.read_bytes() for path in sorted((SCRIPT.parent / "sql").glob("*.sql"))}
        skills_dir = SCRIPT.parents[2] / "skills"
        bundled = sorted(skills_dir.glob("*/scripts/collect_snowflake_evidence.py"))
        self.assertEqual(len(bundled), 9)
        self.assertEqual(len(canonical_sql), 40)
        native_app = skills_dir / "snowflake-native-app-release-sheriff" / "scripts" / SCRIPT.name
        self.assertIn(native_app, bundled)
        self.assertEqual(len(SYNC_MODULE.BUNDLES["snowflake-native-app-release-sheriff"]), 3)
        self.assertIn(
            "snowflake-governance-coverage-auditor",
            {path.parents[1].name for path in bundled},
        )
        self.assertFalse((skills_dir / "snowflake-deploy-medic" / "scripts" / SCRIPT.name).exists())
        for path in bundled:
            with self.subTest(skill=path.parents[1].name):
                self.assertEqual(path.read_bytes(), canonical)
                bundled_sql = {item.name: item.read_bytes() for item in sorted((path.parent / "sql").glob("*.sql"))}
                filenames = SYNC_MODULE.BUNDLES[path.parents[1].name]
                self.assertEqual(bundled_sql, {filename: canonical_sql[filename] for filename in filenames})

    def test_receipt_sql_hash_matches_canonical_template(self) -> None:
        for surface in MODULE.SURFACES:
            with self.subTest(surface=surface):
                path, sql, sources = MODULE.load_surface(surface)
                kwargs = {"source_max_age_seconds": 300} if surface == "query" else {}
                receipt = MODULE.build_receipt(surface, "offline-input", sql, sources, raw=[], **kwargs)
                self.assertEqual(
                    receipt["sql_sha256"],
                    f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
                )

    def test_all_tracked_surfaces_pass_read_only_gate(self) -> None:
        for surface in MODULE.SURFACES:
            with self.subTest(surface=surface):
                path, sql, sources = MODULE.load_surface(surface)
                self.assertTrue(path.is_file())
                self.assertTrue(sources)
                MODULE.validate_read_only_sql(sql)
                for source in sources:
                    self.assertIn(source, sql)

    def test_reviewed_templates_do_not_reintroduce_nonexistent_columns(self) -> None:
        rejected = {
            "auth": {"DEFAULT_SECONDARY_ROLES"},
            "data-quality": {"EXPECTATION_EVALUATION_ERROR"},
            "replication": {
                "REPLICATION_GROUP_TYPE",
                "CREDITS_USED",
                "BYTES_TRANSFERRED",
                "SOURCE_ACCOUNT_NAME",
                "SOURCE_REGION",
                "TARGET_ACCOUNT_NAME",
                "TARGET_REGION",
            },
        }
        for surface, columns in rejected.items():
            _, sql, _ = MODULE.load_surface(surface)
            for column in columns:
                with self.subTest(surface=surface, column=column):
                    self.assertNotRegex(sql, rf"\b{column}\b")

    def test_gate_rejects_mutation_and_session_changes(self) -> None:
        for sql in (
            "ALTER WAREHOUSE X SUSPEND",
            "WITH rows AS (SELECT 1) DELETE FROM t",
            "SELECT 1; GRANT ROLE x TO USER y",
            "/* harmless */ USE ROLE ACCOUNTADMIN",
            "SELECT 1; CALL SYSTEM$WAIT(1)",
        ):
            with self.subTest(sql=sql), self.assertRaises(MODULE.CollectionError):
                MODULE.validate_read_only_sql(sql)
        MODULE.validate_read_only_sql("SELECT 'ALTER TABLE x' AS inert_text")

    def test_normalizer_groups_rows_deterministically(self) -> None:
        raw = [
            {"EVIDENCE": {"_dataset": "queries", "id": "b", "value": 2}},
            {"EVIDENCE": {"_dataset": "queries", "id": "a", "value": 1}},
            {"EVIDENCE": {"_dataset": "warehouses", "id": "w"}},
        ]
        datasets, count = MODULE.normalize_cli_json(raw)
        self.assertEqual(count, 3)
        self.assertEqual(list(datasets), ["queries", "warehouses"])
        self.assertEqual([row["id"] for row in datasets["queries"]], ["a", "b"])

    def test_normalizer_rejects_credentials_and_malformed_rows(self) -> None:
        for raw in (
            [{"EVIDENCE": {"_dataset": "x", "oauth_token": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "accessToken": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "clientSecret": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "privateKey": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "authorizationHeader": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "hasPassword": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "has_pat": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "hasRsaPublicKey": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "has-workload-identity": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "password=hunter2"}}],
            [{"EVIDENCE": {"_dataset": "x", "query_text": "select customer_email"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "https://x.test/file?X-Amz-Signature=abc"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "SELECT 1"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "USE ROLE ACCOUNTADMIN"}}],
            [{"EVIDENCE": {"_dataset": "query_history", "query_tag": "tenant=raw"}}],
            [{"EVIDENCE": []}],
            ["not-an-object"],
        ):
            with self.subTest(raw=raw), self.assertRaises(MODULE.CollectionError):
                MODULE.normalize_cli_json(raw)
        safe_flags = {
            "hasPassword": None,
            "has_pat": False,
            "hasRsaPublicKey": True,
            "has-workload-identity": False,
        }
        datasets, _ = MODULE.normalize_cli_json([{"EVIDENCE": {"_dataset": "users", **safe_flags}}])
        for key, expected in safe_flags.items():
            self.assertIs(datasets["users"][0][key], expected)

    def test_relevant_sql_surfaces_are_deterministically_ordered(self) -> None:
        expected_order = {
            "cost": "ORDER BY SORT_GROUP, SORT_KEY",
            "query": "ORDER BY dataset, sort_key",
            "pipeline": "ORDER BY dataset, sort_key",
        }
        for surface, order_clause in expected_order.items():
            with self.subTest(surface=surface):
                _, sql, _ = MODULE.load_surface(surface)
                self.assertIn(order_clause, sql)

    def test_receipt_exposes_limit_and_possible_truncation(self) -> None:
        path, sql, sources = MODULE.load_surface("query")
        del path
        del sources
        raw = [{"EVIDENCE": {"_dataset": "query_history", "query_id": str(index)}} for index in range(1000)]
        receipt = MODULE.build_receipt("query", "readonly", sql, ["QUERY_HISTORY"], raw=raw, source_max_age_seconds=300)
        self.assertEqual(receipt["row_limit"], 1000)
        self.assertTrue(receipt["truncation_possible"])

    def test_query_receipt_v2_binds_derived_freshness(self) -> None:
        _, sql, sources = MODULE.load_surface("query")
        raw = [
            {
                "EVIDENCE": {
                    "_dataset": "query_history",
                    "query_id": "01abcdef-0123-4567-89ab-cdef01234567",
                    "start_time": "2026-08-30T10:20:00Z",
                    "end_time": "2026-08-30T10:22:33Z",
                }
            },
            {
                "EVIDENCE": {
                    "_dataset": "query_history",
                    "query_id": "01fedcba-9876-4321-89ab-cdef01234567",
                    "start_time": "2026-08-30T10:25:00-01:00",
                    "end_time": None,
                }
            },
        ]
        receipt = MODULE.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at="2026-08-30T11:30:00Z",
            source_max_age_seconds=2700,
        )
        self.assertEqual(receipt["schema_version"], "2")
        self.assertEqual(receipt["freshness"]["dataset_max_time"], "2026-08-30T11:25:00Z")
        self.assertEqual(receipt["freshness"]["source_max_age_seconds"], 2700)
        self.assertIn("anchor query row", receipt["freshness"]["semantics"])
        self.assertTrue(any("not proof of origin" in item for item in receipt["non_claims"]))

    def test_runner_uses_profile_only_and_emits_provenance(self) -> None:
        captured = {}

        def runner(command, **kwargs):
            captured["command"] = command
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    [
                        {
                            "EVIDENCE": {
                                "_dataset": "query_history",
                                "query_id": "01abcdef-0123-4567-89ab-cdef01234567",
                                "end_time": "2026-08-30T10:22:33Z",
                            }
                        }
                    ]
                ),
                stderr="",
            )

        receipt, code = MODULE.execute_surface("query", "readonly-profile", source_max_age_seconds=2700, runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["status"], "collected")
        self.assertEqual(receipt["row_count"], 1)
        self.assertRegex(receipt["sql_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(receipt["receipt_sha256"], r"^sha256:[0-9a-f]{64}$")
        command = captured["command"]
        self.assertEqual(command[:2], ["snow", "sql"])
        self.assertIn("--connection", command)
        self.assertIn("--local-only", command)
        self.assertFalse(any(flag in command for flag in ("--password", "--token", "--private-key-file")))
        self.assertEqual(captured["kwargs"]["timeout"], 120)

    def test_failed_collection_is_sanitized_and_still_receipted(self) -> None:
        for message, forbidden in ADVERSARIAL_ERROR_VALUES:

            def runner(command, **kwargs):
                return subprocess.CompletedProcess(command, 5, stdout="", stderr=message)

            receipt, code = MODULE.execute_surface(
                "cost",
                "readonly",
                window_start="2026-08-01T00:00:00Z",
                window_end="2026-08-02T00:00:00Z",
                runner=runner,
            )
            rendered_errors = json.dumps(receipt["errors"])

            with self.subTest(message=message):
                self.assertEqual(code, 5)
                self.assertEqual(receipt["status"], "error")
                self.assertEqual(receipt["row_count"], 0)
                for fragment in forbidden:
                    self.assertNotIn(fragment, rendered_errors)
                self.assertEqual(
                    receipt["errors"][0]["message"],
                    "Snowflake CLI collection failed; inspect local CLI diagnostics outside the receipt",
                )

    def test_live_cost_receipt_timestamp_is_inside_its_collection_interval(self) -> None:
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")

        receipt, code = MODULE.execute_surface(
            "cost",
            "readonly",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-02T00:00:00Z",
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(receipt["collected_at"], receipt["collection_completed_at"])
        self.assertLessEqual(receipt["collection_started_at"], receipt["collected_at"])
        self.assertNotIn("connection_profile", receipt)
        self.assertRegex(receipt["connection_profile_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_written_error_receipts_remove_every_adversarial_value(self) -> None:
        _, sql, sources = MODULE.load_surface("cost")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "collector-error-receipt.json"
            for message, forbidden in ADVERSARIAL_ERROR_VALUES:
                receipt = MODULE.build_receipt(
                    "cost",
                    "readonly",
                    sql,
                    sources,
                    error={"code": "SNOW_CLI_FAILED", "message": message},
                )
                MODULE.write_receipt(receipt, output)
                rendered = output.read_text(encoding="utf-8")
                rendered_errors = json.dumps(json.loads(rendered)["errors"])

                with self.subTest(message=message):
                    self.assertEqual(json.loads(rendered)["status"], "error")
                    for fragment in forbidden:
                        self.assertNotIn(fragment, rendered_errors)
                    self.assertRegex(rendered_errors, r"\[REDACTED_(?:AUTHORIZATION|CREDENTIAL|SQL)\]")

    def test_written_error_receipts_preserve_safe_evidence(self) -> None:
        _, sql, sources = MODULE.load_surface("cost")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "safe-error-receipt.json"
            for message in SAFE_ERROR_VALUES:
                receipt = MODULE.build_receipt(
                    "cost",
                    "readonly",
                    sql,
                    sources,
                    error={"code": "SNOW_CLI_FAILED", "message": message},
                )
                MODULE.write_receipt(receipt, output)
                rendered = output.read_text(encoding="utf-8")
                with self.subTest(message=message):
                    self.assertIn(message, rendered)
                    self.assertNotIn("[REDACTED_", rendered)

    def test_cli_offline_receipts_reject_artifacts_without_echo_and_preserve_safe_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (message, forbidden) in enumerate(ADVERSARIAL_ERROR_VALUES):
                source = root / f"unsafe-{index}.json"
                output = root / f"unsafe-{index}-receipt.json"
                source.write_text(
                    json.dumps([{"EVIDENCE": {"_dataset": "queries", "note": message}}]),
                    encoding="utf-8",
                )
                completed = subprocess.run(
                    [
                        "python3",
                        str(SCRIPT),
                        "--surface",
                        "query",
                        "--source-max-age-seconds",
                        "900",
                        "--input-json",
                        str(source),
                        "--output",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                combined = completed.stdout + completed.stderr
                with self.subTest(message=message):
                    self.assertEqual(completed.returncode, 2)
                    self.assertFalse(output.exists())
                    for fragment in forbidden:
                        self.assertNotIn(fragment, combined)

            safe_source = root / "safe.json"
            safe_output = root / "safe-receipt.json"
            safe_source.write_text(
                json.dumps(
                    [
                        {
                            "EVIDENCE": {
                                "_dataset": "safe_notes",
                                "sequence": index,
                                "note": message,
                            }
                        }
                        for index, message in enumerate(SAFE_ERROR_VALUES)
                    ]
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "query",
                    "--source-max-age-seconds",
                    "900",
                    "--input-json",
                    str(safe_source),
                    "--output",
                    str(safe_output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            rendered = safe_output.read_text(encoding="utf-8")
            for message in SAFE_ERROR_VALUES:
                self.assertIn(message, rendered)
            self.assertNotIn("[REDACTED_", rendered)

    def test_direct_error_receipt_recursively_sanitizes_arbitrary_values(self) -> None:
        _, sql, sources = MODULE.load_surface("cost")
        receipt = MODULE.build_receipt(
            "cost",
            "readonly",
            sql,
            sources,
            error={
                "code": "SNOW_CLI_FAILED",
                "message": "Authorization: Negotiate negotiate-payload",
                "details": {
                    "accessToken": "camel-access-token-secret",
                    "clientSecret": "camel-client-secret",
                    "privateKey": "camel-private-key",
                    "authorizationHeader": "DPoP camel-authorization-payload",
                    "unsafeBooleanMetadata": {
                        "hasPassword": "password-flag-secret",
                        "has_pat": "pat-flag-secret",
                        "hasRsaPublicKey": "rsa-flag-secret",
                        "has-workload-identity": "identity-flag-secret",
                    },
                    "safeBooleanMetadata": {
                        "hasPassword": True,
                        "has_pat": False,
                        "hasRsaPublicKey": True,
                        "has-workload-identity": False,
                    },
                    "nested": [
                        'password="multi word password"',
                        "SHOW USERS",
                        {"token": "plain-secret-with-no-prefix"},
                    ],
                },
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested-error-receipt.json"
            MODULE.write_receipt(receipt, output)
            rendered = output.read_text(encoding="utf-8")
            written_receipt = json.loads(rendered)

        for forbidden in (
            "Negotiate",
            "negotiate-payload",
            "multi word password",
            "SHOW USERS",
            "plain-secret-with-no-prefix",
            "camel-access-token-secret",
            "camel-client-secret",
            "camel-private-key",
            "camel-authorization-payload",
            "password-flag-secret",
            "pat-flag-secret",
            "rsa-flag-secret",
            "identity-flag-secret",
        ):
            self.assertNotIn(forbidden, rendered)
        self.assertIn("[REDACTED_AUTHORIZATION]", rendered)
        self.assertIn("[REDACTED_CREDENTIAL]", rendered)
        self.assertIn("[REDACTED_SQL]", rendered)
        self.assertEqual(
            written_receipt["errors"][0]["details"]["safeBooleanMetadata"],
            {
                "hasPassword": True,
                "has_pat": False,
                "hasRsaPublicKey": True,
                "has-workload-identity": False,
            },
        )

    def test_cli_offline_normalization_writes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.json"
            output = root / "receipt.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "EVIDENCE": {
                                "_dataset": "query_history",
                                "query_id": "01abcdef-0123-4567-89ab-cdef01234567",
                                "end_time": "2026-08-30T10:22:33Z",
                            }
                        }
                    ]
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "query",
                    "--input-json",
                    str(source),
                    "--source-max-age-seconds",
                    "2700",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["datasets"]["query_history"][0]["query_id"],
                "01abcdef-0123-4567-89ab-cdef01234567",
            )
            self.assertEqual(receipt["freshness"]["source_max_age_seconds"], 2700)
            self.assertFalse((root / ".receipt.json.tmp").exists())

    def test_access_selectors_are_exactly_scoped_and_privacy_safe(self) -> None:
        cases = (
            ("access-role-current", {"role": "DATA_READER"}, "DATA_READER"),
            ("access-role-parents", {"role": "DATA_READER"}, "DATA_READER"),
            ("access-user-current", {"user": "SERVICE_USER"}, "SERVICE_USER"),
            (
                "access-database-role-current",
                {"database_role": "ANALYTICS.READER"},
                "ANALYTICS.READER",
            ),
            ("access-future-database", {"database": "ANALYTICS"}, "ANALYTICS"),
            ("access-future-schema", {"schema": "ANALYTICS.CURATED"}, "ANALYTICS.CURATED"),
        )
        for surface, kwargs, raw_selector in cases:
            with self.subTest(surface=surface):
                path, template, rendered, sources, selector = MODULE.render_surface(surface, **kwargs)
                self.assertNotEqual(template, rendered)
                self.assertIn(raw_selector, rendered)
                receipt = MODULE.build_receipt(
                    surface,
                    "readonly",
                    rendered,
                    sources,
                    raw=[],
                    template_sql=template,
                    template_path=path,
                    selector=selector,
                    collected_at="2026-09-03T12:00:00Z",
                )
                self.assertEqual(receipt["schema_version"], "2")
                self.assertEqual(receipt["sql_sha256"], receipt["template_sha256"])
                self.assertNotEqual(receipt["template_sha256"], receipt["rendered_sql_sha256"])
                self.assertRegex(receipt["selector_fingerprint"], r"^sha256:[0-9a-f]{64}$")
                self.assertEqual(receipt["source_metadata"]["selector"], {next(iter(kwargs)): True})
                self.assertNotIn(raw_selector, json.dumps(receipt["source_metadata"]))

    def test_access_selectors_reject_fragments_quotes_and_wrong_scope(self) -> None:
        invalid = (
            ("access-role-current", {"role": "R; DROP ROLE R"}),
            ("access-role-current", {"role": '"CaseSensitive"'}),
            ("access-user-current", {"user": "USER NAME"}),
            ("access-future-database", {"database": "DB.SCHEMA"}),
            ("access-future-schema", {"schema": "DB"}),
            ("access-future-schema", {"schema": "DB.SCHEMA.EXTRA"}),
            ("access-database-role-current", {"database_role": "DB"}),
            ("access-database-role-current", {"database_role": "DB.ROLE\nSHOW USERS"}),
            ("access-session", {"role": "R"}),
        )
        for surface, kwargs in invalid:
            with self.subTest(surface=surface, kwargs=kwargs), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface(surface, **kwargs)
        with self.assertRaises(MODULE.CollectionError):
            MODULE.render_surface("access-role-current")
        with self.assertRaises(MODULE.CollectionError):
            MODULE.render_surface("access-role-current", role="R", user="U")

    def test_dynamic_access_sql_is_always_removed_from_temp_storage(self) -> None:
        captured_paths: list[Path] = []

        def runner(command, **kwargs):
            path = Path(command[command.index("--filename") + 1])
            captured_paths.append(path)
            self.assertTrue(path.exists())
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")

        receipt, code = MODULE.execute_surface(
            "access-role-current",
            "readonly",
            role="DATA_READER",
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(receipt["surface"], "access-role-current")
        self.assertTrue(captured_paths)
        self.assertTrue(all(not path.exists() for path in captured_paths))

        for failure in ("timeout", "bad-json", "oserror"):
            captured_paths.clear()

            def failing_runner(command, **kwargs):
                path = Path(command[command.index("--filename") + 1])
                captured_paths.append(path)
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(command, 120)
                if failure == "oserror":
                    raise OSError("synthetic runner failure")
                return subprocess.CompletedProcess(command, 0, stdout="not-json", stderr="")

            with self.subTest(failure=failure):
                if failure == "timeout":
                    _, failure_code = MODULE.execute_surface(
                        "access-role-current", "readonly", role="DATA_READER", runner=failing_runner
                    )
                    self.assertEqual(failure_code, 5)
                else:
                    with self.assertRaises((MODULE.CollectionError, OSError)):
                        MODULE.execute_surface(
                            "access-role-current", "readonly", role="DATA_READER", runner=failing_runner
                        )
                self.assertTrue(captured_paths)
                self.assertTrue(all(not path.exists() for path in captured_paths))

    def test_dynamic_selector_is_not_echoed_from_cli_errors(self) -> None:
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                7,
                stdout="",
                stderr="SQL: SHOW GRANTS TO ROLE CUSTOMER_SECRET_ROLE LIMIT 10000",
            )

        receipt, code = MODULE.execute_surface(
            "access-role-current",
            "readonly",
            role="customer_secret_role",
            runner=runner,
        )
        rendered = json.dumps(receipt)
        self.assertEqual(code, 7)
        self.assertNotIn("CUSTOMER_SECRET_ROLE", rendered)
        self.assertNotIn("customer_secret_role", rendered)
        self.assertIn("inspect local CLI diagnostics", rendered)

    def test_cost_windows_are_required_bounded_and_literal(self) -> None:
        start = "2026-08-01T00:00:00Z"
        end = "2026-08-02T00:00:00Z"
        for surface in sorted(MODULE.COST_WINDOW_SURFACES):
            with self.subTest(surface=surface):
                path, template, rendered, sources, selector = MODULE.render_surface(
                    surface, window_start=start, window_end=end
                )
                self.assertTrue(path.is_file())
                self.assertTrue(sources)
                self.assertNotEqual(rendered, template)
                self.assertEqual(selector, {"window_start": start, "window_end": end})
                self.assertNotIn("__WINDOW_START_UTC__", rendered)
                self.assertNotIn("__WINDOW_END_UTC__", rendered)
                with self.assertRaises(MODULE.CollectionError):
                    MODULE.render_surface(surface)
                with self.assertRaises(MODULE.CollectionError):
                    MODULE.render_surface(
                        surface,
                        window_start="2026-08-01T00:00:00Z'); DROP DATABASE PROD; --",
                        window_end=end,
                    )
                with self.assertRaises(MODULE.CollectionError):
                    MODULE.render_surface(
                        surface,
                        window_start="2026-08-01T00:00:00Z",
                        window_end="2026-08-09T00:00:01Z",
                    )

    def test_pipeline_history_requires_a_bounded_half_open_utc_window(self) -> None:
        start = "2026-08-01T00:00:00Z"
        end = "2026-08-08T00:00:00Z"
        path, template, rendered, sources, selector = MODULE.render_surface(
            "pipeline",
            window_start=start,
            window_end=end,
        )
        self.assertEqual(selector, {"window_start": start, "window_end": end})
        self.assertNotRegex(template.upper(), r"DATEADD\(\s*'DAY'\s*,\s*-7")
        self.assertIn(f"TO_TIMESTAMP_TZ('{start}')", rendered)
        self.assertIn(f"TO_TIMESTAMP_TZ('{end}')", rendered)
        for timestamp_column in ("COMPLETED_TIME", "REFRESH_END_TIME", "LAST_LOAD_TIME"):
            with self.subTest(timestamp_column=timestamp_column):
                self.assertRegex(
                    rendered.upper(),
                    rf"\b{timestamp_column}\s*>=\s*WINDOW_START_UTC",
                )
                self.assertRegex(
                    rendered.upper(),
                    rf"\b{timestamp_column}\s*<\s*LEAST\(\s*WINDOW_END_UTC",
                )
        self.assertIn("REFRESH_END_TIME IS NOT NULL", rendered.upper())
        self.assertIn("STATE <> 'EXECUTING'", rendered.upper())
        self.assertRegex(rendered.upper(), r"'PIPE_IDENTIFIER_SHA256'\s*,\s*IFF\(\s*PIPE_NAME IS NULL")

        for invalid_start, invalid_end in (
            (None, None),
            (start, None),
            (None, end),
            (end, start),
            (start, "2026-08-08T00:00:01Z"),
            ("2026-08-01T00:00:00+00:00", end),
        ):
            kwargs = {}
            if invalid_start is not None:
                kwargs["window_start"] = invalid_start
            if invalid_end is not None:
                kwargs["window_end"] = invalid_end
            with self.subTest(window=kwargs), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface("pipeline", **kwargs)

    def test_pipeline_history_receipt_is_schema2_and_privacy_bound(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface(
            "pipeline",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-02T00:00:00Z",
        )
        raw = [
            {
                "EVIDENCE": {
                    "_dataset": "execution_context",
                    "observed_at": "2026-08-02T00:05:00Z",
                    "account_identifier_sha256": "a" * 64,
                }
            },
            {"EVIDENCE": {"_dataset": "task_history", "task_key_sha256": "b" * 64}},
            {
                "EVIDENCE": {
                    "_dataset": "dynamic_table_refresh_history",
                    "dynamic_table_key_sha256": "c" * 64,
                }
            },
            {"EVIDENCE": {"_dataset": "copy_history", "target_key_sha256": "d" * 64}},
        ]
        receipt = MODULE.build_receipt(
            "pipeline",
            "raw-pipeline-profile",
            rendered,
            sources,
            raw=raw,
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collection_started_at="2026-08-02T00:04:00Z",
            collection_completed_at="2026-08-02T00:05:00Z",
        )
        expected = {
            "execution_context",
            "task_history",
            "dynamic_table_refresh_history",
            "copy_history",
        }
        self.assertEqual(receipt["schema_version"], "2")
        self.assertEqual(set(receipt["expected_datasets"]), expected)
        self.assertEqual(set(receipt["datasets"]), expected)
        self.assertEqual(receipt["cap_scope"], "per_dataset")
        self.assertRegex(receipt["connection_profile_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(receipt["result_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(receipt["source_metadata"]["selector_values"], selector)
        self.assertEqual(
            receipt["selector_fingerprint"],
            "sha256:" + hashlib.sha256(MODULE.canonical_json(selector)).hexdigest(),
        )
        self.assertEqual(
            receipt["rendered_sql_sha256"],
            "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        )
        self.assertNotIn("connection_profile", receipt)
        self.assertNotIn("raw-pipeline-profile", json.dumps(receipt))

    def test_pipeline_history_caps_each_dataset_independently(self) -> None:
        self.assertEqual(
            set(MODULE.CAP_DATASETS_BY_SURFACE["pipeline"]),
            {"task_history", "dynamic_table_refresh_history", "copy_history"},
        )
        _, sql, _ = MODULE.load_surface("pipeline")
        self.assertEqual(len(re.findall(r"\bLIMIT\s+5000\b", sql, flags=re.IGNORECASE)), 3)
        capped_sql = re.sub(r"\bLIMIT\s+5000\b", "LIMIT 2", sql, flags=re.IGNORECASE)
        context = {"EVIDENCE": {"_dataset": "execution_context", "observed_at": "2026-08-02T00:05:00Z"}}
        for dataset in MODULE.CAP_DATASETS_BY_SURFACE["pipeline"]:
            rows = [
                context,
                {"EVIDENCE": {"_dataset": dataset, "row": 1}},
                {"EVIDENCE": {"_dataset": dataset, "row": 2}},
            ]
            receipt = MODULE.build_receipt("pipeline", "readonly", capped_sql, ["pipeline"], raw=rows)
            with self.subTest(capped_dataset=dataset):
                self.assertEqual(receipt["cap_scope"], "per_dataset")
                self.assertTrue(receipt["truncation_possible"])

        below_each_cap = [
            context,
            *({"EVIDENCE": {"_dataset": dataset, "row": 1}} for dataset in MODULE.CAP_DATASETS_BY_SURFACE["pipeline"]),
        ]
        receipt = MODULE.build_receipt("pipeline", "readonly", capped_sql, ["pipeline"], raw=below_each_cap)
        self.assertGreater(receipt["row_count"], receipt["row_limit"])
        self.assertFalse(receipt["truncation_possible"])

    def test_pipeline_current_surfaces_have_exact_dataset_contracts(self) -> None:
        expected = {
            "pipeline-task-current": {"current_tasks", "execution_context"},
            "pipeline-stream-current": {"current_streams", "execution_context"},
            "pipeline-dynamic-table-current": {"current_dynamic_tables", "execution_context"},
            "pipeline-pipe-current": {"current_pipes", "execution_context"},
            "pipeline-pipe-status": {"execution_context", "pipe_status"},
        }
        registered = set(MODULE.SURFACES) | set(MODULE.SUBSURFACES)
        self.assertEqual(set(expected) & registered, set(expected))
        for surface, datasets in expected.items():
            with self.subTest(surface=surface):
                self.assertEqual(set(MODULE.RECEIPT_EXPECTED_DATASETS[surface]), datasets)
                path, template, rendered, sources, selector = MODULE.render_surface(
                    surface,
                    **({"pipe": "OPS.INGEST.EVENTS_PIPE"} if surface == "pipeline-pipe-status" else {}),
                )
                self.assertTrue(path.is_file())
                self.assertTrue(sources)
                self.assertIn("'_dataset', 'execution_context'", rendered)
                receipt = MODULE.build_receipt(
                    surface,
                    "readonly",
                    rendered,
                    sources,
                    raw=[],
                    template_sql=template,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                )
                self.assertEqual(set(receipt["datasets"]), datasets)
                self.assertEqual(receipt["schema_version"], "2")

    def test_pipeline_sql_omits_unbounded_provider_text_fields(self) -> None:
        forbidden_by_surface = {
            "pipeline": ("'scheduled_from',", "'error_code',", "'state_code',"),
            "pipeline-task-current": ("'schedule',", "'target_completion_interval',"),
            "pipeline-dynamic-table-current": ("'target_lag',",),
        }
        for surface, forbidden_fragments in forbidden_by_surface.items():
            _, sql, _ = MODULE.load_surface(surface)
            for fragment in forbidden_fragments:
                with self.subTest(surface=surface, fragment=fragment):
                    self.assertNotIn(fragment, sql)

    def test_pipeline_pipe_status_requires_one_strict_three_part_selector(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface(
            "pipeline-pipe-status",
            pipe="OPS.INGEST.EVENTS_PIPE",
        )
        self.assertEqual(selector, {"pipe": "OPS.INGEST.EVENTS_PIPE"})
        self.assertNotIn("__PIPE_IDENTIFIER__", rendered)
        object_key = "9" * 64
        receipt = MODULE.build_receipt(
            "pipeline-pipe-status",
            "readonly",
            rendered,
            sources,
            raw=[
                {"EVIDENCE": {"_dataset": "execution_context", "account_identifier_sha256": "a" * 64}},
                {
                    "EVIDENCE": {
                        "_dataset": "pipe_status",
                        "object_key_sha256": object_key,
                        "execution_state": "RUNNING",
                    }
                },
            ],
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
        )
        binding = {"pipe_object_key_sha256": object_key}
        self.assertEqual(receipt["source_metadata"]["selector_binding"], binding)
        self.assertEqual(receipt["source_metadata"]["rendered_sql_contract"], "privacy-bound-selector-v1")
        self.assertEqual(
            receipt["selector_fingerprint"],
            "sha256:" + hashlib.sha256(MODULE.canonical_json(binding)).hexdigest(),
        )
        privacy_bound_sql = template.replace("__PIPE_IDENTIFIER__", f"__PIPE_OBJECT_KEY_SHA256_{object_key}__")
        self.assertEqual(
            receipt["rendered_sql_sha256"],
            "sha256:" + hashlib.sha256(privacy_bound_sql.encode("utf-8")).hexdigest(),
        )
        self.assertNotIn("OPS.INGEST.EVENTS_PIPE", json.dumps(receipt))
        for value in (
            "EVENTS_PIPE",
            "INGEST.EVENTS_PIPE",
            "OPS.INGEST.EVENTS.PIPE",
            'OPS.INGEST."EVENTS_PIPE"',
            "OPS.INGEST.EVENTS_PIPE;DROP TABLE X",
            "OPS.INGEST.EVENTS_PIPE--comment",
            "OPS..EVENTS_PIPE",
        ):
            with self.subTest(pipe=value), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface("pipeline-pipe-status", pipe=value)

    def test_pipeline_pipe_status_error_receipt_does_not_hash_raw_selector(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface(
            "pipeline-pipe-status",
            pipe="OPS.INGEST.PRIVATE_CUSTOMER_PIPE",
        )
        receipt = MODULE.build_receipt(
            "pipeline-pipe-status",
            "readonly",
            rendered,
            sources,
            error={"code": "SNOW_CLI_FAILED", "message": "collection failed"},
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
        )
        template_hash = "sha256:" + hashlib.sha256(template.encode("utf-8")).hexdigest()
        raw_selector_hash = "sha256:" + hashlib.sha256(MODULE.canonical_json(selector)).hexdigest()
        self.assertEqual(receipt["status"], "error")
        self.assertEqual(receipt["rendered_sql_sha256"], template_hash)
        self.assertIsNone(receipt["selector_fingerprint"])
        self.assertNotEqual(receipt["selector_fingerprint"], raw_selector_hash)
        self.assertNotIn("selector_binding", receipt["source_metadata"])
        self.assertNotIn("PRIVATE_CUSTOMER_PIPE", json.dumps(receipt))

    def test_data_quality_surfaces_have_exact_schema_two_contracts(self) -> None:
        expected = {
            "data-quality": {"execution_context", "expectation_history"},
            "data-quality-associations-current": {"current_associations", "execution_context"},
            "data-quality-expectations-current": {"current_expectations", "execution_context"},
            "data-quality-notification-current": {"execution_context", "notification_associations"},
        }
        kwargs = {
            "data-quality": {
                "window_start": "2026-08-01T00:00:00Z",
                "window_end": "2026-08-02T00:00:00Z",
            },
            "data-quality-associations-current": {
                "data_quality_object": "governed.analytics.orders",
                "data_quality_domain": "TABLE",
            },
            "data-quality-expectations-current": {
                "data_quality_object": "governed.analytics.orders",
                "data_quality_domain": "TABLE",
            },
            "data-quality-notification-current": {
                "data_quality_object": "governed.analytics.orders",
                "data_quality_domain": "TABLE",
            },
        }
        for surface, datasets in expected.items():
            with self.subTest(surface=surface):
                path, template, rendered, sources, selector = MODULE.render_surface(surface, **kwargs.get(surface, {}))
                MODULE.validate_read_only_sql(rendered)
                receipt = MODULE.build_receipt(
                    surface,
                    "private-profile",
                    rendered,
                    sources,
                    raw=[],
                    template_sql=template,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                )
                self.assertEqual(receipt["schema_version"], "2")
                self.assertEqual(set(receipt["expected_datasets"]), datasets)
                self.assertEqual(set(receipt["datasets"]), datasets)
                self.assertEqual(receipt["cap_scope"], "per_dataset")
                self.assertRegex(receipt["result_sha256"], r"^sha256:[0-9a-f]{64}$")
                self.assertRegex(receipt["connection_profile_sha256"], r"^sha256:[0-9a-f]{64}$")
                self.assertNotIn("connection_profile", receipt)
                self.assertNotIn("private-profile", json.dumps(receipt))

    def test_data_quality_history_requires_bounded_half_open_utc_window(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface(
            "data-quality",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-08T00:00:00Z",
        )
        self.assertNotIn("__WINDOW_START_UTC__", rendered)
        self.assertNotIn("__WINDOW_END_UTC__", rendered)
        self.assertIn("h.MEASUREMENT_TIME >= c.window_start_utc", rendered)
        self.assertIn("h.MEASUREMENT_TIME < c.window_end_utc", rendered)
        self.assertIn("'window_semantics', 'HALF_OPEN_UTC'", template)
        self.assertIn("'provider_latency_documented', FALSE", template)
        self.assertIn("'settlement_policy_status', 'NOT_DECLARED'", template)
        self.assertEqual(
            selector,
            {"window_start": "2026-08-01T00:00:00Z", "window_end": "2026-08-08T00:00:00Z"},
        )
        receipt = MODULE.build_receipt(
            "data-quality",
            "readonly",
            rendered,
            sources,
            raw=[],
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
        )
        self.assertEqual(receipt["source_metadata"]["selector_values"], selector)
        self.assertEqual(
            receipt["selector_fingerprint"],
            "sha256:" + hashlib.sha256(MODULE.canonical_json(selector)).hexdigest(),
        )
        with self.assertRaises(MODULE.CollectionError):
            MODULE.render_surface(
                "data-quality",
                window_start="2026-08-01T00:00:00Z",
                window_end="2026-08-08T00:00:01Z",
            )

    def test_data_quality_sql_emits_only_hashed_identity_and_definition_fields(self) -> None:
        forbidden_output_keys = (
            "'table_id'",
            "'table_name'",
            "'table_schema'",
            "'table_database'",
            "'metric_id'",
            "'metric_name'",
            "'metric_schema'",
            "'metric_database'",
            "'reference_id'",
            "'expectation_id'",
            "'expectation_name'",
            "'expectation_expression'",
            "'execution_role'",
            "'schedule'",
            "'filter'",
            "'within_group'",
            "'properties'",
        )
        for surface in (
            "data-quality",
            "data-quality-associations-current",
            "data-quality-expectations-current",
            "data-quality-notification-current",
        ):
            _, sql, _ = MODULE.load_surface(surface)
            with self.subTest(surface=surface):
                self.assertIn("SHA2(", sql)
                self.assertIn("CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP())", sql)
                for context_key in (
                    "'observed_at'",
                    "'organization_name_sha256'",
                    "'account_identifier_sha256'",
                    "'collector_user_sha256'",
                    "'primary_role_sha256'",
                    "'primary_role_type'",
                    "'secondary_roles_sha256'",
                    "'timezone'",
                ):
                    self.assertIn(context_key, sql)
                for key in forbidden_output_keys:
                    self.assertNotIn(key, sql)
        _, associations_sql, _ = MODULE.load_surface("data-quality-associations-current")
        self.assertNotIn("DATA_QUALITY_NOTIFICATION_STATUS", associations_sql)
        for state in (
            "STARTED",
            "STARTED_AND_PENDING_SCHEDULE_UPDATE",
            "SUSPENDED",
            "SUSPENDED_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
            "SUSPENDED_DATA_METRIC_FUNCTION_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
            "SUSPENDED_TABLE_COLUMN_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
            "SUSPENDED_INSUFFICIENT_PRIVILEGE_TO_EXECUTE_DATA_METRIC_FUNCTION",
            "SUSPENDED_ACTIVE_EVENT_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
        ):
            self.assertIn(f"'{state}'", associations_sql)
        self.assertNotIn("visibility_lag_seconds", associations_sql)
        self.assertNotIn("visibility_watermark_utc", associations_sql)
        self.assertIn("BETWEEN 1 AND 1000", associations_sql)
        self.assertIn("ELSE 0", associations_sql)
        for surface in MODULE.DATA_QUALITY_SELECTOR_SURFACES:
            _, current_sql, _ = MODULE.load_surface(surface)
            with self.subTest(surface=surface):
                self.assertIn("source_counts AS", current_sql)
                self.assertIn("COUNT(*) AS source_row_count", current_sql)
                self.assertIn("'source_row_limit', 5000", current_sql)
                self.assertIn("'selected_object_key_sha256'", current_sql)
                self.assertIn("'selected_object_domain'", current_sql)
                self.assertNotIn("visibility_lag_seconds", current_sql)
                self.assertNotIn("visibility_watermark_utc", current_sql)

    def test_data_quality_receipts_apply_caps_per_dataset(self) -> None:
        datasets_by_surface = {
            "data-quality": "expectation_history",
            "data-quality-associations-current": "current_associations",
            "data-quality-expectations-current": "current_expectations",
            "data-quality-notification-current": "notification_associations",
        }
        for surface, dataset in datasets_by_surface.items():
            _, sql, _ = MODULE.load_surface(surface)
            capped_sql = re.sub(r"\bLIMIT\s+5000\b", "LIMIT 2", sql, flags=re.IGNORECASE)
            rows = [
                {"EVIDENCE": {"_dataset": "execution_context", "observed_at": "2026-08-02T00:00:00Z"}},
                {"EVIDENCE": {"_dataset": dataset, "object_key_sha256": "a" * 64}},
                {"EVIDENCE": {"_dataset": dataset, "object_key_sha256": "b" * 64}},
            ]
            receipt = MODULE.build_receipt(surface, "readonly", capped_sql, ["source"], raw=rows)
            with self.subTest(surface=surface):
                self.assertEqual(receipt["cap_scope"], "per_dataset")
                self.assertTrue(receipt["truncation_possible"])

    def test_data_quality_current_selectors_are_strict_and_privacy_bound(self) -> None:
        surfaces = (
            "data-quality-associations-current",
            "data-quality-expectations-current",
            "data-quality-notification-current",
        )
        for surface in surfaces:
            with self.subTest(surface=surface):
                with self.assertRaises(MODULE.CollectionError):
                    MODULE.render_surface(surface)
                path, template, rendered, sources, selector = MODULE.render_surface(
                    surface,
                    data_quality_object="governed.analytics.private_orders",
                    data_quality_domain="TABLE",
                )
                self.assertEqual(
                    selector,
                    {"data_quality_object": "GOVERNED.ANALYTICS.PRIVATE_ORDERS", "data_quality_domain": "TABLE"},
                )
                self.assertIn("GOVERNED.INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_", rendered)
                self.assertNotIn("__DATA_QUALITY_OBJECT_IDENTIFIER__", rendered)
                object_key = "9" * 64
                raw = [
                    {
                        "EVIDENCE": {
                            "_dataset": "execution_context",
                            "account_identifier_sha256": "a" * 64,
                            "selected_object_key_sha256": object_key,
                            "selected_object_domain": "TABLE",
                        }
                    }
                ]
                receipt = MODULE.build_receipt(
                    surface,
                    "readonly",
                    rendered,
                    sources,
                    raw=raw,
                    template_sql=template,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                )
                binding = {"selected_object_key_sha256": object_key, "selected_object_domain": "TABLE"}
                self.assertEqual(receipt["source_metadata"]["selector_binding"], binding)
                self.assertEqual(receipt["source_metadata"]["rendered_sql_contract"], "privacy-bound-selector-v1")
                self.assertEqual(
                    receipt["selector_fingerprint"],
                    "sha256:" + hashlib.sha256(MODULE.canonical_json(binding)).hexdigest(),
                )
                privacy_bound_sql = (
                    template.replace(
                        "__DATA_QUALITY_OBJECT_IDENTIFIER__",
                        f"__DATA_QUALITY_OBJECT_KEY_SHA256_{object_key}__",
                    )
                    .replace("__DATA_QUALITY_DOMAIN__", "__DATA_QUALITY_DOMAIN_TABLE__")
                    .replace(
                        "__DATA_QUALITY_DATABASE_IDENTIFIER__",
                        f"__DATA_QUALITY_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{object_key}__",
                    )
                )
                self.assertEqual(
                    receipt["rendered_sql_sha256"],
                    "sha256:" + hashlib.sha256(privacy_bound_sql.encode("utf-8")).hexdigest(),
                )
                self.assertNotIn("PRIVATE_ORDERS", json.dumps(receipt))
        for surface in surfaces:
            for value in (
                "GOVERNED.ANALYTICS",
                'GOVERNED.ANALYTICS."PRIVATE_ORDERS"',
                "GOVERNED.ANALYTICS.PRIVATE_ORDERS;DROP TABLE X",
                "GOVERNED..PRIVATE_ORDERS",
            ):
                with (
                    self.subTest(surface=surface, data_quality_object=value),
                    self.assertRaises(MODULE.CollectionError),
                ):
                    MODULE.render_surface(
                        surface,
                        data_quality_object=value,
                        data_quality_domain="TABLE",
                    )
            for domain in ("table", "MATERIALIZED VIEW", "STREAM"):
                with (
                    self.subTest(surface=surface, data_quality_domain=domain),
                    self.assertRaises(MODULE.CollectionError),
                ):
                    MODULE.render_surface(
                        surface,
                        data_quality_object="GOVERNED.ANALYTICS.PRIVATE_ORDERS",
                        data_quality_domain=domain,
                    )

    def test_data_quality_current_error_receipts_retain_template_proof_only(self) -> None:
        for surface in MODULE.DATA_QUALITY_SELECTOR_SURFACES:
            with self.subTest(surface=surface):
                path, template, rendered, sources, selector = MODULE.render_surface(
                    surface,
                    data_quality_object="GOVERNED.ANALYTICS.PRIVATE_ORDERS",
                    data_quality_domain="VIEW",
                )
                receipt = MODULE.build_receipt(
                    surface,
                    "readonly",
                    rendered,
                    sources,
                    raw=[
                        {
                            "EVIDENCE": {
                                "_dataset": "execution_context",
                                "selected_object_key_sha256": "9" * 64,
                                "selected_object_domain": "VIEW",
                            }
                        }
                    ],
                    error={"code": "SNOW_CLI_FAILED", "message": "collection failed"},
                    template_sql=template,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                )
                template_hash = "sha256:" + hashlib.sha256(template.encode("utf-8")).hexdigest()
                self.assertEqual(receipt["rendered_sql_sha256"], template_hash)
                self.assertIsNone(receipt["selector_fingerprint"])
                self.assertNotIn("selector_binding", receipt["source_metadata"])
                self.assertNotIn("PRIVATE_ORDERS", json.dumps(receipt))

    def test_data_quality_offline_normalization_is_rejected_for_every_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "saved.json"
            source.write_text("[]", encoding="utf-8")
            surfaces = {
                "data-quality": (
                    "--window-start",
                    "2026-08-01T00:00:00Z",
                    "--window-end",
                    "2026-08-02T00:00:00Z",
                ),
                "data-quality-associations-current": (
                    "--data-quality-object",
                    "GOVERNED.ANALYTICS.ORDERS",
                    "--data-quality-domain",
                    "TABLE",
                ),
                "data-quality-expectations-current": (
                    "--data-quality-object",
                    "GOVERNED.ANALYTICS.ORDERS",
                    "--data-quality-domain",
                    "TABLE",
                ),
                "data-quality-notification-current": (
                    "--data-quality-object",
                    "GOVERNED.ANALYTICS.ORDERS",
                    "--data-quality-domain",
                    "TABLE",
                ),
            }
            for surface, extra_args in surfaces.items():
                completed = subprocess.run(
                    [
                        "python3",
                        str(SCRIPT),
                        "--surface",
                        surface,
                        "--input-json",
                        str(source),
                        *extra_args,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                with self.subTest(surface=surface):
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("offline normalization is diagnostic-only", completed.stderr)

    def test_pipeline_offline_normalization_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "saved.json"
            output = root / "receipt.json"
            source.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "pipeline",
                    "--window-start",
                    "2026-08-01T00:00:00Z",
                    "--window-end",
                    "2026-08-02T00:00:00Z",
                    "--input-json",
                    str(source),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("offline normalization is diagnostic-only", completed.stderr)
            self.assertFalse(output.exists())

    def test_cost_offline_normalization_is_rejected_for_every_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "saved.json"
            source.write_text("[]", encoding="utf-8")
            cost_surfaces = ["cost", *(surface for surface in MODULE.SUBSURFACES if surface.startswith("cost-"))]
            for surface in sorted(cost_surfaces):
                output = root / f"{surface}.json"
                command = [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    surface,
                    "--input-json",
                    str(source),
                    "--output",
                    str(output),
                ]
                if surface in MODULE.COST_WINDOW_SURFACES:
                    command.extend(
                        [
                            "--window-start",
                            "2026-08-01T00:00:00Z",
                            "--window-end",
                            "2026-08-02T00:00:00Z",
                        ]
                    )
                completed = subprocess.run(command, capture_output=True, text=True, check=False)
                with self.subTest(surface=surface):
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("offline normalization is diagnostic-only", completed.stderr)
                    self.assertFalse(output.exists())

    def test_cost_receipt_binds_exact_datasets_context_and_per_dataset_caps(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface(
            "cost",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-02T00:00:00Z",
        )
        raw = [
            {"EVIDENCE": {"_dataset": "execution_context", "observed_at": "2026-09-03T12:00:00Z"}},
            *({"EVIDENCE": {"_dataset": dataset, "row": 1}} for dataset in MODULE.CAP_DATASETS_BY_SURFACE["cost"]),
        ]
        receipt = MODULE.build_receipt(
            "cost",
            "readonly",
            rendered,
            sources,
            raw=raw,
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collected_at="2026-09-03T12:00:00Z",
        )
        self.assertEqual(receipt["schema_version"], "2")
        self.assertEqual(receipt["collection_mode"], "live-cli")
        self.assertEqual(receipt["expected_datasets"], list(MODULE.RECEIPT_EXPECTED_DATASETS["cost"]))
        self.assertEqual(set(receipt["datasets"]), set(MODULE.RECEIPT_EXPECTED_DATASETS["cost"]))
        self.assertEqual(receipt["dataset_row_counts"]["execution_context"], 1)
        self.assertEqual(receipt["row_limit"], 5000)
        self.assertEqual(receipt["cap_scope"], "per_dataset")
        self.assertFalse(receipt["truncation_possible"])
        self.assertRegex(receipt["selector_fingerprint"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(receipt["result_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertIsNone(receipt["snowflake_query_id"])
        self.assertEqual(
            receipt["snowflake_query_id_status"],
            "not_exposed_by_snow_cli_json_ext",
        )

    def test_cost_sql_aggregates_multi_entity_metering_and_scopes_query_hashes(self) -> None:
        _, template, _, _, _ = MODULE.render_surface(
            "cost",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-02T00:00:00Z",
        )
        self.assertIn("'credits_used', SUM(CREDITS_USED)", template)
        self.assertEqual(
            [line.strip() for line in template.splitlines() if line.lstrip().startswith("GROUP BY ")],
            ["GROUP BY SERVICE_TYPE, START_TIME, END_TIME"],
        )
        self.assertIn("CURRENT_ACCOUNT_NAME(), qa.QUERY_HASH", template)
        self.assertIn("CURRENT_ACCOUNT_NAME(), qa.QUERY_PARAMETERIZED_HASH", template)

        _, adaptive, _, _, _ = MODULE.render_surface(
            "cost-adaptive",
            window_start="2026-08-01T00:00:00Z",
            window_end="2026-08-02T00:00:00Z",
        )
        self.assertIn(
            "'query_hash', IFF(QUERY_HASH IS NULL, NULL, "
            "SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), "
            "CURRENT_ACCOUNT_NAME(), QUERY_HASH)), 256))",
            adaptive,
        )
        self.assertIn(
            "'query_parameterized_hash', IFF(QUERY_PARAMETERIZED_HASH IS NULL, NULL, "
            "SHA2(TO_JSON(ARRAY_CONSTRUCT(CURRENT_ORGANIZATION_NAME(), "
            "CURRENT_ACCOUNT_NAME(), QUERY_PARAMETERIZED_HASH)), 256))",
            adaptive,
        )

    def test_cost_templates_never_use_globally_linkable_direct_identity_hashes(self) -> None:
        for path in sorted((HERE.parent / "sql").glob("cost*.sql")):
            sql = path.read_text(encoding="utf-8")
            with self.subTest(template=path.name):
                self.assertNotIn("SHA2(TO_VARCHAR", sql)
                if "_sha256'" in sql:
                    self.assertIn("CURRENT_ORGANIZATION_NAME()", sql)
                    self.assertIn("CURRENT_ACCOUNT_NAME()", sql)

    def test_current_show_templates_bind_context_in_the_same_pipe_statement(self) -> None:
        selectors = {
            "access-role-current": {"role": "ANALYST"},
            "access-role-parents": {"role": "ANALYST"},
            "access-user-current": {"user": "ALICE"},
            "access-database-role-current": {"database_role": "ANALYTICS.READER"},
            "access-future-database": {"database": "ANALYTICS"},
            "access-future-schema": {"schema": "ANALYTICS.CURATED"},
        }
        for surface, selector in selectors.items():
            with self.subTest(surface=surface):
                _, _, rendered, _, _ = MODULE.render_surface(surface, **selector)
                self.assertIn("->>", rendered)
                self.assertIn("CURRENT_SESSION()", rendered)
                self.assertIn("'_dataset', 'execution_context'", rendered)
                self.assertIn("FROM $1 AS src", rendered)
                self.assertNotIn('$1."', rendered)

        _, _, auth_current, _, _ = MODULE.render_surface("auth-current")
        self.assertIn("SHOW USERS LIMIT 10000", auth_current)
        self.assertIn("->>", auth_current)
        self.assertNotIn("CURRENT_ACCOUNT()", auth_current)
        self.assertIn("CURRENT_ORGANIZATION_NAME()", auth_current)
        self.assertIn("CURRENT_ACCOUNT_NAME()", auth_current)
        self.assertIn("'principal_scope', IFF(", auth_current)
        self.assertIn("'SNOWFLAKE_MANAGED_EXCLUDED'", auth_current)
        self.assertIn("normalized_show_rows AS", auth_current)
        self.assertIn("COALESCE(IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'type')), TRUE)", auth_current)
        self.assertIn("'type', USER_TYPE", auth_current)
        self.assertIn("USER_TYPE = 'SNOWFLAKE_SERVICE'", auth_current)
        self.assertIn("COALESCE(NOT IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'created_on')), FALSE)", auth_current)
        self.assertIn("COALESCE(NOT IS_NULL_VALUE(GET_IGNORE_CASE(SHOW_ROW, 'disabled')), FALSE)", auth_current)
        self.assertNotIn("'type', COALESCE(UPPER(TO_VARCHAR(GET_IGNORE_CASE", auth_current)
        self.assertNotIn("GET_IGNORE_CASE(SHOW_ROW, 'created_on') IS NOT NULL", auth_current)
        self.assertIn("'_dataset', 'execution_context'", auth_current)
        self.assertIn("FROM $1", auth_current)
        self.assertNotIn("WHERE", auth_current.upper())
        self.assertNotIn("TO_JSON(CURRENT_SECONDARY_ROLES())", auth_current)
        self.assertIn("TO_VARCHAR(CURRENT_SECONDARY_ROLES())", auth_current)

        for surface in ("auth", "auth-login-history"):
            with self.subTest(surface=surface):
                _, _, rendered, _, _ = MODULE.render_surface(surface)
                self.assertNotIn("TO_JSON(CURRENT_SECONDARY_ROLES())", rendered)
                self.assertIn("TO_VARCHAR(CURRENT_SECONDARY_ROLES())", rendered)
                self.assertNotIn("CURRENT_ACCOUNT()", rendered)
                self.assertIn("CURRENT_ORGANIZATION_NAME()", rendered)
                self.assertIn("CURRENT_ACCOUNT_NAME()", rendered)

        _, _, historical_users, _, _ = MODULE.render_surface("auth")
        self.assertIn("'principal_scope', IFF(", historical_users)
        self.assertIn("COALESCE(UPPER(TYPE), 'PERSON')", historical_users)
        self.assertNotIn("<> 'SNOWFLAKE_SERVICE'", historical_users.upper())

        _, _, login_history, _, _ = MODULE.render_surface("auth-login-history")
        self.assertIn("TRY_TO_BOOLEAN(TO_VARCHAR(IS_SUCCESS))", login_history)
        self.assertIn("AND EVENT_TYPE = 'LOGIN'", login_history)
        self.assertNotIn("TO_VARCHAR(REPORTED_CLIENT_TYPE)", login_history)
        self.assertNotIn("'reported_client_type_observation'", login_history)

    def test_auth_offline_normalization_is_rejected_for_every_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "saved.json"
            source.write_text("[]", encoding="utf-8")
            for surface in ("auth-current", "auth", "auth-login-history"):
                output = root / f"{surface}.json"
                completed = subprocess.run(
                    [
                        "python3",
                        str(SCRIPT),
                        "--surface",
                        surface,
                        "--input-json",
                        str(source),
                        "--output",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                with self.subTest(surface=surface):
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("offline normalization is diagnostic-only", completed.stderr)
                    self.assertFalse(output.exists())

    def test_auth_receipts_bind_exact_datasets_and_cap_semantics(self) -> None:
        cases = {
            "auth-current": ("current_users", "SHOW USERS"),
            "auth": ("historical_users", "SNOWFLAKE.ACCOUNT_USAGE.USERS"),
            "auth-login-history": ("login_history", "SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY"),
        }
        for surface, (cap_dataset, source_view) in cases.items():
            path, template, rendered, sources, selector = MODULE.render_surface(surface)
            raw = [
                {"EVIDENCE": {"_dataset": "execution_context", "observed_at": "2026-09-03T12:00:00Z"}},
                {"EVIDENCE": {"_dataset": cap_dataset, "row": 1}},
            ]
            receipt = MODULE.build_receipt(
                surface,
                "readonly",
                rendered,
                sources,
                raw=raw,
                template_sql=template,
                template_path=path,
                selector=selector,
                collected_at="2026-09-03T12:00:00Z",
                collection_mode="live-cli",
            )
            with self.subTest(surface=surface):
                self.assertEqual(receipt["schema_version"], "2")
                self.assertEqual(receipt["source_views"], [source_view])
                self.assertEqual(
                    receipt["expected_datasets"],
                    list(MODULE.RECEIPT_EXPECTED_DATASETS[surface]),
                )
                self.assertEqual(receipt["dataset_row_counts"][cap_dataset], 1)
                self.assertEqual(receipt["row_limit"], 10000)
                self.assertFalse(receipt["truncation_possible"])
                self.assertEqual(receipt["collection_mode"], "live-cli")
                self.assertEqual(receipt["non_claims"], list(MODULE.RECEIPT_NON_CLAIMS))
                self.assertNotIn("cap_scope", receipt)
                self.assertNotIn("result_sha256", receipt)

    def test_access_offline_normalization_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "saved.json"
            output = root / "receipt.json"
            source.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "access-role-current",
                    "--role",
                    "ANALYST",
                    "--input-json",
                    str(source),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("offline normalization is diagnostic-only", completed.stderr)
            self.assertFalse(output.exists())

    def test_access_receipt_counts_and_truncation_are_derived(self) -> None:
        path, template, rendered, sources, selector = MODULE.render_surface("access-role-current", role="DATA_READER")
        receipt = MODULE.build_receipt(
            "access-role-current",
            "readonly",
            rendered,
            sources,
            raw=[{"privilege": "SELECT"}, {"privilege": "USAGE"}],
            template_sql=template,
            template_path=path,
            selector=selector,
            collected_at="2026-09-03T12:00:00Z",
        )
        self.assertEqual(receipt["row_count"], 2)
        self.assertEqual(receipt["dataset_row_counts"], {"execution_context": 0, "rows": 2})
        self.assertEqual(receipt["row_limit"], 10000)
        self.assertFalse(receipt["truncation_possible"])

    def test_replication_surfaces_are_schema_2_live_only_and_bounded(self) -> None:
        start, end = "2026-09-03T00:00:00Z", "2026-09-04T00:00:00Z"
        cases = {
            "replication": {"window_start": start, "window_end": end},
            "replication-current": {},
            "replication-progress": {"window_start": start, "window_end": end},
            "replication-dangling": {"replication_group": "DR_GROUP"},
        }
        for surface, kwargs in cases.items():
            path, template, rendered, sources, selector = MODULE.render_surface(surface, **kwargs)
            data_name = next(name for name in MODULE.RECEIPT_EXPECTED_DATASETS[surface] if name != "execution_context")
            context = {"observed_at": end}
            if surface == "replication-dangling":
                context["selected_group_key_sha256"] = "a" * 64
            receipt = MODULE.build_receipt(
                surface,
                "readonly",
                rendered,
                sources,
                raw=[
                    {"EVIDENCE": {"_dataset": "execution_context", **context}},
                    {"EVIDENCE": {"_dataset": data_name, "group_key_sha256": "b" * 64}},
                ],
                template_sql=template,
                template_path=path,
                selector=selector,
                collected_at=end,
                collection_mode="live-cli",
            )
            with self.subTest(surface=surface):
                self.assertEqual(receipt["schema_version"], "2")
                self.assertEqual(receipt["collection_mode"], "live-cli")
                self.assertEqual(receipt["cap_scope"], "per_dataset")
                self.assertEqual(receipt["row_limit"], 5000)
                self.assertNotIn("connection_profile", receipt)
                self.assertRegex(receipt["connection_profile_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_replication_selector_and_window_validation_fail_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.CollectionError, "requires both window_start and window_end"):
            MODULE.render_surface("replication")
        with self.assertRaisesRegex(MODULE.CollectionError, "cannot exceed seven days"):
            MODULE.render_surface(
                "replication-progress",
                window_start="2026-08-01T00:00:00Z",
                window_end="2026-08-09T00:00:00Z",
            )
        for value in ("DR GROUP", "DR'; ALTER FAILOVER GROUP X PRIMARY;--", '"Quoted"', "A.B"):
            with self.subTest(value=value), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface("replication-dangling", replication_group=value)
        _, template, rendered, _, selector = MODULE.render_surface("replication-dangling", replication_group="DR_GROUP")
        self.assertNotEqual(template, rendered)
        self.assertEqual(selector, {"replication_group": "DR_GROUP"})
        _, _, lower_rendered, _, lower_selector = MODULE.render_surface(
            "replication-dangling", replication_group="dr_group"
        )
        self.assertEqual(lower_selector, {"replication_group": "DR_GROUP"})
        self.assertEqual(lower_rendered, rendered)
        for surface in ("replication", "replication-progress"):
            _, _, windowed, _, _ = MODULE.render_surface(
                surface, window_start="2026-09-03T00:00:00Z", window_end="2026-09-04T00:00:00Z"
            )
            self.assertIn("START_TIME >= TO_TIMESTAMP_TZ('2026-09-03T00:00:00Z')", windowed)
            self.assertIn("START_TIME < TO_TIMESTAMP_TZ('2026-09-04T00:00:00Z')", windowed)
        _, _, current_sql, _, _ = MODULE.render_surface("replication-current")
        self.assertIn('UPPER("account_name") = UPPER(CURRENT_ACCOUNT_NAME())', current_sql)

    def test_replication_offline_normalization_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "saved.json"
            source.write_text("[]", encoding="utf-8")
            cases = {
                "replication": ["--window-start", "2026-09-03T00:00:00Z", "--window-end", "2026-09-04T00:00:00Z"],
                "replication-current": [],
                "replication-progress": [
                    "--window-start",
                    "2026-09-03T00:00:00Z",
                    "--window-end",
                    "2026-09-04T00:00:00Z",
                ],
                "replication-dangling": ["--replication-group", "DR_GROUP"],
            }
            for surface, extra in cases.items():
                completed = subprocess.run(
                    ["python3", str(SCRIPT), "--surface", surface, "--input-json", str(source), *extra],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                with self.subTest(surface=surface):
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("offline normalization is diagnostic-only", completed.stderr)

    def test_system_replication_control_functions_are_rejected(self) -> None:
        for sql in (
            "SELECT SYSTEM$SCHEDULE_ASYNC_REPLICATION_GROUP_REFRESH('DR')",
            "SELECT SYSTEM$CANCEL_QUERY('abc')",
            "SELECT SYSTEM$ABORT_SESSION('abc')",
        ):
            with self.subTest(sql=sql), self.assertRaisesRegex(MODULE.CollectionError, "unreviewed SYSTEM"):
                MODULE.validate_read_only_sql(sql)
        MODULE.validate_read_only_sql("SELECT SYSTEM$PIPE_STATUS('DB.SCHEMA.PIPE')")

    def test_native_app_surfaces_require_strict_private_package_selector(self) -> None:
        for surface in (
            "native-app-versions-current",
            "native-app-release-directives-current",
            "native-app-upgrade-cohorts-current",
        ):
            with self.subTest(surface=surface):
                _, template, rendered, _, selector = MODULE.render_surface(surface, application_package="app_package")
                self.assertEqual(selector, {"application_package": "APP_PACKAGE"})
                self.assertNotIn("__APPLICATION_PACKAGE_IDENTIFIER__", rendered)
                self.assertIn("__APPLICATION_PACKAGE_IDENTIFIER__", template)
            with self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface(surface, application_package="APP; DROP TABLE X")

    def test_native_app_receipt_privacy_binds_package_hash(self) -> None:
        surface = "native-app-versions-current"
        path, template, rendered, sources, selector = MODULE.render_surface(
            surface, application_package="PRIVATE_PACKAGE"
        )
        package_key = "a" * 64
        raw = [
            {"EVIDENCE": {"_dataset": "execution_context", "selected_package_key_sha256": package_key}},
            {"EVIDENCE": {"_dataset": "versions", "package_key_sha256": package_key}},
        ]
        receipt = MODULE.build_receipt(
            surface,
            "observer",
            rendered,
            sources,
            raw=raw,
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
        )
        serialized = json.dumps(receipt)
        self.assertNotIn("PRIVATE_PACKAGE", serialized)
        self.assertEqual(
            receipt["source_metadata"]["selector_binding"],
            {"selected_package_key_sha256": package_key},
        )
        self.assertEqual(receipt["cap_scope"], "per_dataset")

    def test_native_app_error_receipt_never_fingerprints_selector(self) -> None:
        surface = "native-app-versions-current"
        path, template, rendered, sources, selector = MODULE.render_surface(
            surface, application_package="PRIVATE_PACKAGE"
        )
        receipt = MODULE.build_receipt(
            surface,
            "observer",
            rendered,
            sources,
            error={"message": "PRIVATE_PACKAGE failed"},
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
        )
        self.assertIsNone(receipt["selector_fingerprint"])
        self.assertNotIn("PRIVATE_PACKAGE", json.dumps(receipt))

    def test_native_app_offline_normalization_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "saved.json"
            source.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "native-app-versions-current",
                    "--application-package",
                    "APP_PACKAGE",
                    "--input-json",
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("offline normalization is diagnostic-only", completed.stderr)


if __name__ == "__main__":
    unittest.main()
