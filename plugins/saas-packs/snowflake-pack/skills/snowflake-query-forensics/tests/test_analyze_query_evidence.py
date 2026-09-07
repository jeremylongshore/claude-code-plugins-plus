from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "analyze_query_evidence.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
OTHER_QUERY_ID = "01fedcba-9876-4321-89ab-cdef01234567"
OLD_QUERY_ID = "01234567-89ab-cdef-0123-456789abcdef"
NEW_QUERY_ID = "89abcdef-0123-4567-89ab-cdef01234567"
ADVERSARIAL_OUTPUT_VALUES = (
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
ADVERSARIAL_OUTPUT_VALUES += SELECT_BOUNDARY_SQL + VALUES_EXPRESSION_SQL + DIAGNOSTIC_WRAPPED_SQL
ADVERSARIAL_OUTPUT_VALUES += (
    ("VALUES (", ("VALUES (",)),
    ("VALUES (" + "(" * 20_000, ("VALUES (",)),
    ("VALUES (" + ",".join("1" for _ in range(3_000)) + ")", ("VALUES (1",)),
)

SAFE_OUTPUT_VALUES = (
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
SAFE_OUTPUT_VALUES += (
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

SPEC = importlib.util.spec_from_file_location("analyze_query_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

COLLECTOR_SCRIPT = SKILL_DIR / "scripts" / "collect_snowflake_evidence.py"
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", COLLECTOR_SCRIPT)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)


class QueryEvidenceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def valid_receipt(self, data: dict) -> dict:
        raw = []
        for dataset in ("query_history", "warehouse_load"):
            if dataset in data:
                value = data.get(dataset, [])
                rows = [value] if isinstance(value, dict) else value
                raw.extend({"EVIDENCE": {"_dataset": dataset, **row}} for row in rows if isinstance(row, dict))
        _, sql, sources = COLLECTOR.load_surface("query")
        return COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )

    def rehash_receipt(self, receipt: dict) -> None:
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(body)).hexdigest()}"

    def analyze_trusted(self, data: dict) -> dict:
        if "collector_receipt" not in data:
            data["collector_receipt"] = self.valid_receipt(data)
        return MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

    def test_sanitizers_are_bounded_total_functions_under_adversarial_shapes(self) -> None:
        class ExplodingString:
            def __str__(self) -> str:
                raise ValueError("must not escape")

        self.assertEqual(MODULE.safe_text(ExplodingString()), "[REDACTED_CREDENTIAL]")
        self.assertEqual(MODULE.safe_text("VALUES (" + "(" * 50_000), "[REDACTED_SQL]")
        self.assertEqual(len(MODULE.safe_text("ordinary-note " + "x" * 50_000)), 2000)

        for depth in range(80):
            statement = f"VALUES ({'(' * depth}'depth-secret'{')' * depth})"
            with self.subTest(depth=depth):
                self.assertEqual(MODULE.safe_text(statement), "[REDACTED_SQL]")

        cyclic: list[object] = []
        cyclic.append(cyclic)
        sanitized = MODULE.sanitize_output_tree({"nested": cyclic})
        self.assertIsInstance(sanitized, dict)
        self.assertIn("[REDACTED_CREDENTIAL]", json.dumps(sanitized))

        wide = list(range(MODULE.MAX_SANITIZE_TREE_NODES + 5_000))
        sanitized_wide = MODULE.sanitize_output_tree(wide)
        self.assertLessEqual(len(sanitized_wide), MODULE.MAX_SANITIZE_TREE_NODES)
        self.assertEqual(sanitized_wide[-1], "[REDACTED_CREDENTIAL]")
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.reject_secret_fields(wide)

    def test_separates_observations_ratios_and_hypotheses(self) -> None:
        result = self.analyze_trusted(self.load_fixture("query_evidence.json"))
        self.assertFalse(result["completeness_claim_blocked"])
        confirmed_metrics = {item["metric"] for item in result["confirmed_observations"]}
        self.assertIn("queued_overload_time_ms", confirmed_metrics)
        self.assertIn("transaction_blocked_time_ms", confirmed_metrics)
        self.assertIn("bytes_spilled_remote_storage", confirmed_metrics)
        self.assertIn("QUERY_INSIGHT_REMOTE_SPILLAGE", confirmed_metrics)

        derived = {(item["metric"], item["operator_id"]): item for item in result["estimated_or_derived_metrics"]}
        self.assertEqual(derived[("output_to_input_row_multiple", "3")]["value"], "5")
        self.assertEqual(derived[("partitions_scanned_fraction", "3")]["value"], "1")
        self.assertEqual(derived[("partitions_scanned_fraction", "4")]["value"], "0.2")

        hypotheses = {item["hypothesis"] for item in result["at_risk_hypotheses"]}
        self.assertIn("join expansion requires semantic review", hypotheses)
        self.assertIn("no partition pruning observed for this scan", hypotheses)
        self.assertIn("query shape or warehouse capacity contributed to remote spill", hypotheses)
        self.assertEqual(result["top_operators_by_observed_percentage"][0]["operator_id"], "3")
        self.assertEqual(result["timeline_ms"]["total_elapsed_time_ms"], "153000")
        self.assertEqual(result["timeline_ms"]["other_or_unexplained_time_ms"], "0")
        self.assertTrue(all(item["falsification_evidence"] for item in result["at_risk_hypotheses"]))

    def test_running_query_reports_unknown_operator_state(self) -> None:
        result = MODULE.analyze(self.load_fixture("query_evidence_incomplete.json"))
        self.assertFalse(result["estimated_or_derived_metrics"])
        self.assertFalse(result["at_risk_hypotheses"])
        warnings = "\n".join(result["warnings"])
        self.assertIn("operator statistics absent", warnings)
        self.assertIn("until completion", warnings)
        self.assertIn("absence is not proof", warnings)

    def test_running_query_does_not_interpret_supplied_operator_evidence(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["execution_status"] = "running"
        result = self.analyze_trusted(data)
        self.assertEqual(result["top_operators_by_observed_percentage"], [])
        self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
        self.assertTrue(result["completeness_claim_blocked"])
        operator_hypotheses = {
            "join expansion requires semantic review",
            "no partition pruning observed for this scan",
            "query shape or warehouse capacity contributed to remote spill",
        }
        self.assertTrue(operator_hypotheses.isdisjoint({item["hypothesis"] for item in result["at_risk_hypotheses"]}))
        self.assertFalse(any(item["kind"] == "operator" for item in result["confirmed_observations"]))

    def test_rejects_impossible_percentages_and_partition_counts(self) -> None:
        percentage = self.load_fixture("query_evidence.json")
        percentage["operators"][0]["execution_time_breakdown"]["overall_percentage"] = 1000
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(percentage)
        partitions = self.load_fixture("query_evidence.json")
        partitions["operators"][0]["operator_statistics"]["pruning"] = {
            "partitions_scanned": 200,
            "partitions_total": 100,
        }
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(partitions)

    def test_rejects_negative_operator_counter(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["operators"][0]["operator_statistics"]["input_rows"] = -1
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(data)

    def test_rejects_future_history_timestamp(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["history_source_max_time"] = "2026-08-30T12:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_requires_scope_owner_and_non_future_collection(self) -> None:
        for field in ("account", "role", "history_source", "experiment_owner"):
            data = self.load_fixture("query_evidence.json")
            data["metadata"][field] = ""
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)
        future = self.load_fixture("query_evidence.json")
        future["metadata"]["collected_at"] = "2099-01-01T00:00:00Z"
        future["metadata"]["history_source_max_time"] = "2098-01-01T00:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(future)

    def test_redacts_insight_messages_and_rejects_secret_fields(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_insights"][0]["message"] = "password=hunter2 token=abc123 https://signed.example/?sig=xyz"
        rendered = json.dumps(self.analyze_trusted(data))
        self.assertNotIn("hunter2", rendered)
        self.assertNotIn("abc123", rendered)
        self.assertNotIn("signed.example", rendered)
        for field in ("api_key", "SESSION_TOKEN", "jwt"):
            bad = self.load_fixture("query_evidence.json")
            bad[field] = "never"
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(bad)
        for field in ("hasPassword", "has_pat", "hasRsaPublicKey", "has-workload-identity"):
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.reject_secret_fields({field: "not-a-boolean-secret"})
        MODULE.reject_secret_fields(
            {
                "hasPassword": True,
                "has_pat": False,
                "hasRsaPublicKey": True,
                "has-workload-identity": False,
            }
        )

    def test_recursively_redacts_unsafe_scalar_values_from_json_and_markdown(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_insights"][0]["message"] = (
            "password=hunter2 token=abc123 authorization=Bearer deadbeef; SELECT salary, ssn FROM payroll"
        )

        result = self.analyze_trusted(data)
        rendered_json = json.dumps(result)
        rendered_markdown = MODULE.render_markdown(result)

        for rendered in (rendered_json, rendered_markdown):
            self.assertNotIn("hunter2", rendered)
            self.assertNotIn("abc123", rendered)
            self.assertNotIn("deadbeef", rendered)
            self.assertNotIn("SELECT salary, ssn FROM payroll", rendered)
            self.assertIn("[REDACTED_CREDENTIAL]", rendered)

        arbitrary = MODULE.sanitize_output_tree(
            {
                "allowed_key": [
                    "password=arbitrary-secret",
                    {"nested": "SELECT card_number FROM payments"},
                ]
            }
        )
        arbitrary_rendered = json.dumps(arbitrary)
        self.assertNotIn("arbitrary-secret", arbitrary_rendered)
        self.assertNotIn("card_number", arbitrary_rendered)
        self.assertIn("[REDACTED_CREDENTIAL]", arbitrary_rendered)
        self.assertIn("[REDACTED_SQL]", arbitrary_rendered)

        for legitimate in (
            "A matching out-of-band digest proves only canonical bundle parity.",
            "The OAuth flow was reviewed without including credentials.",
            "The signature scheme is documented.",
            *SAFE_OUTPUT_VALUES,
        ):
            with self.subTest(legitimate=legitimate):
                self.assertEqual(MODULE.safe_text(legitimate), legitimate)

        unsafe_flags = {
            "hasPassword": "password-flag-secret",
            "has_pat": "pat-flag-secret",
            "hasRsaPublicKey": "rsa-flag-secret",
            "has-workload-identity": "identity-flag-secret",
        }
        self.assertEqual(
            MODULE.sanitize_output_tree(unsafe_flags),
            {key: "[REDACTED_CREDENTIAL]" for key in unsafe_flags},
        )
        safe_flags = {
            "hasPassword": True,
            "has_pat": False,
            "hasRsaPublicKey": True,
            "has-workload-identity": False,
        }
        self.assertEqual(MODULE.sanitize_output_tree(safe_flags), safe_flags)

    def test_rejects_unsafe_output_identifiers_before_rendering(self) -> None:
        mutations = {
            "operator_id": lambda data: data["operators"][0].__setitem__("operator_id", "token=abc123"),
            "operator_type": lambda data: data["operators"][0].__setitem__(
                "operator_type", "SELECT salary, ssn FROM payroll"
            ),
            "experiment_owner": lambda data: data["metadata"].__setitem__(
                "experiment_owner", "authorization=Bearer-secret"
            ),
        }
        for field, mutate in mutations.items():
            data = self.load_fixture("query_evidence.json")
            mutate(data)
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                self.analyze_trusted(data)

    def test_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "evidence.json"
            json_out = Path(directory) / "packet.json"
            markdown_out = Path(directory) / "packet.md"
            data = self.load_fixture("query_evidence.json")
            data["collector_receipt"] = self.valid_receipt(data)
            input_path.write_text(json.dumps(data), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--trusted-input-sha256",
                    MODULE.input_sha256(data),
                    "--json-out",
                    str(json_out),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(json_out.read_text())["schema_version"], "2.0")
            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIn("## Confirmed observations", markdown)
            self.assertIn("## Estimated or derived metrics", markdown)
            self.assertIn("## At-risk hypotheses", markdown)
            self.assertIn("## Timeline", markdown)
            self.assertIn("## One-variable experiment boundary", markdown)

            digest = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--print-input-sha256",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(digest.returncode, 0, digest.stderr)
            self.assertEqual(digest.stdout.strip(), MODULE.input_sha256(data))

    def test_cli_artifacts_remove_credentials_and_raw_sql_across_formats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "adversarial-evidence.json"
            json_out = root / "packet.json"
            markdown_out = root / "packet.md"
            data = self.load_fixture("query_evidence.json")
            query_id = data["metadata"]["query_id"]
            output_values = [value for value, _ in ADVERSARIAL_OUTPUT_VALUES] + list(SAFE_OUTPUT_VALUES)
            data["query_insights"] = [
                {
                    "query_id": query_id,
                    "type_id": f"REDACTION_CASE_{index:02d}",
                    "message": value,
                }
                for index, value in enumerate(output_values)
            ]
            data["collector_receipt"] = self.valid_receipt(data)
            input_path.write_text(json.dumps(data), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--trusted-input-sha256",
                    MODULE.input_sha256(data),
                    "--json-out",
                    str(json_out),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            artifacts = (
                json_out.read_text(encoding="utf-8"),
                markdown_out.read_text(encoding="utf-8"),
            )
            for index, (value, forbidden) in enumerate(ADVERSARIAL_OUTPUT_VALUES):
                with self.subTest(value=value):
                    expected = MODULE.safe_text(value)
                    self.assertEqual(expected, COLLECTOR.sanitize_text(value))
                    for artifact in artifacts:
                        metric = f"REDACTION_CASE_{index:02d}"
                        metric_position = artifact.find(metric)
                        self.assertGreaterEqual(metric_position, 0)
                        self.assertIn(expected, artifact[metric_position : metric_position + 500])
                        for fragment in forbidden:
                            self.assertNotIn(fragment, artifact)
            for artifact in artifacts:
                self.assertIn("[REDACTED_AUTHORIZATION]", artifact)
                self.assertIn("[REDACTED_CREDENTIAL]", artifact)
                self.assertIn("[REDACTED_SQL]", artifact)
                for safe_value in SAFE_OUTPUT_VALUES:
                    self.assertIn(safe_value, artifact)

    def test_correlates_load_hashes_and_sos_roi_without_recommending_mutation(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["warehouse_load"] = [
            {
                "warehouse_name": "ETL_WH",
                "start_time": "2026-08-30T10:20:00Z",
                "end_time": "2026-08-30T10:22:00Z",
                "avg_running": "1.2",
                "avg_queued_load": "0.4",
                "avg_queued_provisioning": "0",
            }
        ]
        data["query_runs"] = [
            {
                "query_id": OLD_QUERY_ID,
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "1000",
            },
            {
                "query_id": NEW_QUERY_ID,
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "2000",
            },
        ]
        data["comparison_alignment"] = {
            "status": "aligned",
            "warehouse_name": "ETL_WH",
            "data_scope": "orders-2026-08-30",
            "parameters": {},
            "cache_state": "disabled",
            "session_parameters": {},
        }
        data["search_optimization"] = {
            "credits_used": "2.5",
            "latency_before_ms": "5000",
            "latency_after_ms": "2500",
            "bytes_scanned_before": "1000",
            "bytes_scanned_after": "400",
        }
        data["query_insights_status"] = {"status": "available", "reason": "operator-supplied Query Insights export"}
        result = self.analyze_trusted(data)
        self.assertEqual(result["warehouse_load_summary"][0]["avg_queued_load_sum"], "0.4")
        self.assertEqual(result["query_hash_comparison"][0]["sample_count"], 2)
        self.assertEqual(result["search_optimization_roi"][0]["latency_reduction_ms"], "2500")
        self.assertEqual(result["query_insights_coverage"]["status"], "available")

    def test_rejects_query_identity_mismatch(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["query_id"] = OTHER_QUERY_ID
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_rejects_non_uuid_or_cross_query_evidence_ids(self) -> None:
        for field_path in ("metadata", "operator", "insight"):
            data = self.load_fixture("query_evidence.json")
            if field_path == "metadata":
                data["metadata"]["query_id"] = "01abc; DROP TABLE audit_log"
            elif field_path == "operator":
                data["operators"][0]["query_id"] = OTHER_QUERY_ID
            else:
                data["query_insights"][0]["query_id"] = OTHER_QUERY_ID
            with self.subTest(field_path=field_path), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)
        for invalid in ("old", "01abc-example", "a_b.c"):
            data = self.load_fixture("query_evidence.json")
            data["metadata"]["query_id"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_nonterminal_supplied_rows_fail_closed_before_interpretation(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["execution_status"] = "running"
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertEqual(result["top_operators_by_observed_percentage"], [])

        for dataset in ("operators", "query_insights"):
            cross_query = self.load_fixture("query_evidence.json")
            cross_query["query_history"]["execution_status"] = "running"
            cross_query["collector_receipt"] = self.valid_receipt(cross_query)
            cross_query[dataset][0]["query_id"] = OTHER_QUERY_ID
            with self.subTest(dataset=dataset), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(cross_query, trusted_input_sha256=MODULE.input_sha256(cross_query))

    def test_nonterminal_empty_rows_never_vacuously_bind(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["operators"] = []
        data["query_insights"] = []
        data["query_history"]["execution_status"] = "running"
        data["collector_receipt"] = self.valid_receipt(data)

        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertEqual(result["confirmed_observations"], [])
        self.assertEqual(result["estimated_or_derived_metrics"], [])
        self.assertEqual(result["at_risk_hypotheses"], [])

    def test_terminal_missing_operator_evidence_is_always_partial(self) -> None:
        for representation in ("empty", "missing"):
            data = self.load_fixture("query_evidence.json")
            data["query_insights"] = []
            if representation == "empty":
                data["operators"] = []
            else:
                del data["operators"]
            data["collector_receipt"] = self.valid_receipt(data)

            result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

            with self.subTest(representation=representation):
                self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
                self.assertTrue(result["completeness_claim_blocked"])
                self.assertEqual(result["confirmed_observations"], [])
                self.assertEqual(result["estimated_or_derived_metrics"], [])
                self.assertEqual(result["at_risk_hypotheses"], [])

    def test_terminal_operator_minimum_allows_optional_empty_insights(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_insights"] = []

        result = self.analyze_trusted(data)

        self.assertEqual(result["evidence_binding"]["status"], "BOUND")
        self.assertFalse(result["completeness_claim_blocked"])
        self.assertTrue(result["confirmed_observations"])
        self.assertEqual(result["query_insights_coverage"]["status"], "unknown")

    def test_unbound_operator_or_insight_rows_are_excluded_and_block_completeness(self) -> None:
        for dataset in ("operators", "query_insights"):
            data = self.load_fixture("query_evidence.json")
            data["collector_receipt"] = self.valid_receipt(data)
            del data[dataset][0]["query_id"]
            result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
            self.assertTrue(result["completeness_claim_blocked"])
            self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
            self.assertTrue(any(f"{dataset}[0]: query_id absent" in item for item in result["warnings"]))
            if dataset == "operators":
                self.assertNotIn("3", {item["operator_id"] for item in result["top_operators_by_observed_percentage"]})
            else:
                self.assertNotIn(
                    "QUERY_INSIGHT_REMOTE_SPILLAGE",
                    {item["metric"] for item in result["confirmed_observations"]},
                )

    def test_declared_source_freshness_is_enforced(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["source_max_age_seconds"] = 60
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(result["source_freshness"]["status"], "STALE")
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertTrue(any("exceeds the declared freshness bound" in item for item in result["warnings"]))

        for invalid in (None, 0, -1, True, "2700"):
            data = self.load_fixture("query_evidence.json")
            data["metadata"]["source_max_age_seconds"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_freshness_metadata_cannot_override_receipt_binding(self) -> None:
        mutations = {
            "history_source_max_time": "2026-08-30T10:59:59Z",
            "source_max_age_seconds": 9999,
            "collected_at": "2026-08-30T11:00:01Z",
        }
        for field, value in mutations.items():
            data = self.load_fixture("query_evidence.json")
            data["metadata"]["source_max_age_seconds"] = 60
            data["collector_receipt"] = self.valid_receipt(data)
            data["metadata"][field] = value
            result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
            self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
            self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
            self.assertTrue(result["completeness_claim_blocked"])

        rehashed = self.load_fixture("query_evidence.json")
        rehashed["metadata"]["history_source_max_time"] = "2026-08-30T10:59:59Z"
        receipt = self.valid_receipt(self.load_fixture("query_evidence.json"))
        receipt["freshness"]["dataset_max_time"] = "2026-08-30T10:59:59Z"
        self.rehash_receipt(receipt)
        rehashed["collector_receipt"] = receipt
        result = MODULE.analyze(rehashed, trusted_input_sha256=MODULE.input_sha256(rehashed))
        self.assertIn(
            "freshness dataset_max_time is not derived from all query_history receipt rows",
            result["collector_receipt_assessment"]["issues"],
        )
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_unrelated_history_row_cannot_freshen_anchor(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["source_max_age_seconds"] = 60
        raw = [
            {"EVIDENCE": {"_dataset": "query_history", **data["query_history"]}},
            {
                "EVIDENCE": {
                    "_dataset": "query_history",
                    "query_id": OTHER_QUERY_ID,
                    "start_time": "2026-08-30T10:58:00Z",
                    "end_time": "2026-08-30T10:59:00Z",
                }
            },
        ]
        _, sql, sources = COLLECTOR.load_surface("query")
        data["collector_receipt"] = COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )
        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["source_freshness"]["status"], "STALE")
        self.assertTrue(result["completeness_claim_blocked"])

        claimed_fresh = json.loads(json.dumps(data))
        claimed_fresh["metadata"]["history_source_max_time"] = "2026-08-30T10:59:00Z"
        result = MODULE.analyze(
            claimed_fresh,
            trusted_input_sha256=MODULE.input_sha256(claimed_fresh),
        )
        self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
        self.assertIn(
            "metadata.history_source_max_time is not derived from the anchor query receipt row",
            result["collector_receipt_assessment"]["issues"],
        )
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")

    def test_metadata_source_and_role_must_match_exact_receipted_values(self) -> None:
        raw = self.load_fixture("collector_query_output.json")
        for field, value, expected_issue in (
            (
                "history_source",
                MODULE.INFORMATION_SCHEMA_HISTORY_SOURCE,
                "metadata.history_source does not match the receipted query-history source",
            ),
            (
                "role",
                "ACCOUNTADMIN",
                "metadata.role does not match the receipted anchor role_name",
            ),
        ):
            data = self.load_fixture("query_evidence.json")
            _, sql, sources = COLLECTOR.load_surface("query")
            receipt = COLLECTOR.build_receipt(
                "query",
                "readonly",
                sql,
                sources,
                raw=raw,
                collected_at=data["metadata"]["collected_at"],
                source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
            )
            data["query_history"] = receipt["datasets"]["query_history"][0]
            data["collector_receipt"] = receipt
            data["metadata"][field] = value

            result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

            with self.subTest(field=field):
                self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
                self.assertIn(expected_issue, result["collector_receipt_assessment"]["issues"])
                self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
                self.assertTrue(result["completeness_claim_blocked"])
                self.assertEqual(result["confirmed_observations"], [])

    def test_exact_receipted_source_and_role_allow_terminal_claims(self) -> None:
        raw = self.load_fixture("collector_query_output.json")
        data = self.load_fixture("query_evidence.json")
        _, sql, sources = COLLECTOR.load_surface("query")
        receipt = COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )
        data["query_history"] = receipt["datasets"]["query_history"][0]
        data["collector_receipt"] = receipt

        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["history_source"], MODULE.ACCOUNT_USAGE_HISTORY_SOURCE)
        self.assertEqual(result["query"]["role"], "QUERY_AUDITOR")
        self.assertEqual(result["evidence_binding"]["status"], "BOUND")
        self.assertFalse(result["completeness_claim_blocked"])
        self.assertTrue(result["confirmed_observations"])

    def test_duplicate_anchor_history_row_fails_closed(self) -> None:
        data = self.load_fixture("query_evidence.json")
        duplicate = dict(data["query_history"])
        duplicate["start_time"] = "2026-08-30T10:58:00Z"
        duplicate["end_time"] = "2026-08-30T10:59:00Z"
        raw = [
            {"EVIDENCE": {"_dataset": "query_history", **data["query_history"]}},
            {"EVIDENCE": {"_dataset": "query_history", **duplicate}},
        ]
        _, sql, sources = COLLECTOR.load_surface("query")
        data["collector_receipt"] = COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )

        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
        self.assertIn(
            "query_history receipt must contain exactly one row for metadata.query_id",
            result["collector_receipt_assessment"]["issues"],
        )
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_rejects_legacy_input_schema_explicitly(self) -> None:
        data = self.load_fixture("query_evidence.json")
        del data["schema_version"]
        with self.assertRaisesRegex(MODULE.EvidenceError, "schema_version must be 2.0"):
            MODULE.analyze(data)

    def test_load_correlation_requires_same_interval_and_warehouse(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["warehouse_load"] = [
            {
                "warehouse_name": "OTHER_WH",
                "start_time": "2026-08-30T10:20:00Z",
                "end_time": "2026-08-30T10:22:00Z",
                "avg_queued_load": "99",
            },
            {
                "warehouse_name": "ETL_WH",
                "start_time": "2026-08-30T09:00:00Z",
                "end_time": "2026-08-30T09:05:00Z",
                "avg_queued_load": "88",
            },
        ]
        result = self.analyze_trusted(data)
        self.assertEqual(result["warehouse_load_summary"], [])
        self.assertTrue(any("outside the query interval or warehouse" in item for item in result["warnings"]))

    def test_unaligned_hash_runs_are_not_compared(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_runs"] = [
            {
                "query_id": OLD_QUERY_ID,
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "1000",
            },
            {
                "query_id": NEW_QUERY_ID,
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "2000",
            },
        ]
        result = self.analyze_trusted(data)
        self.assertEqual(result["query_hash_comparison"], [])
        self.assertTrue(any("aligned comparison receipt is missing" in item for item in result["warnings"]))

    def test_rejects_raw_identity_and_query_tag_fields(self) -> None:
        for field in ("user_name", "query_tag"):
            data = self.load_fixture("query_evidence.json")
            data["query_history"][field] = "raw-value"
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_trusted_local_collector_receipt_is_accepted(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["evidence_trust"]["status"], "TRUSTED_LOCAL_DIGEST")
        self.assertFalse(result["completeness_claim_blocked"])

    def test_self_consistent_receipt_without_trust_anchor_blocks_claims(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data)
        self.assertEqual(result["collector_receipt_assessment"]["status"], "self_consistent_untrusted")
        self.assertEqual(result["collector_receipt_assessment"]["integrity_status"], "CONSISTENT")
        self.assertEqual(result["evidence_trust"]["status"], "UNTRUSTED")
        self.assertEqual(result["confirmed_observations"], [])
        self.assertEqual(result["top_operators_by_observed_percentage"], [])
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
        self.assertEqual(result["source_freshness"]["calculated_status"], "UNVERIFIED")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_forged_and_rehashed_dataset_remains_untrusted(self) -> None:
        data = self.load_fixture("query_evidence.json")
        receipt = self.valid_receipt(data)
        forged_value = 999999999
        data["query_history"]["bytes_scanned"] = forged_value
        receipt["datasets"]["query_history"][0]["bytes_scanned"] = forged_value
        self.rehash_receipt(receipt)
        data["collector_receipt"] = receipt

        result = MODULE.analyze(data)

        self.assertEqual(result["collector_receipt_assessment"]["status"], "self_consistent_untrusted")
        self.assertEqual(result["evidence_trust"]["status"], "UNTRUSTED")
        self.assertEqual(result["confirmed_observations"], [])
        self.assertEqual(result["estimated_or_derived_metrics"], [])
        self.assertEqual(result["at_risk_hypotheses"], [])
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
        self.assertEqual(result["source_freshness"]["calculated_status"], "UNVERIFIED")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_trusted_digest_mismatch_blocks_claims(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        trusted_digest = MODULE.input_sha256(data)
        data["operators"][0]["operator_statistics"]["input_rows"] += 1

        result = MODULE.analyze(data, trusted_input_sha256=trusted_digest)

        self.assertEqual(result["evidence_trust"]["status"], "DIGEST_MISMATCH")
        self.assertEqual(result["collector_receipt_assessment"]["status"], "self_consistent_untrusted")
        self.assertEqual(result["confirmed_observations"], [])
        self.assertEqual(result["source_freshness"]["status"], "UNVERIFIED")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_truncated_or_unverifiable_receipt_blocks_completeness(self) -> None:
        for mutation in ("truncate", "hash"):
            data = self.load_fixture("query_evidence.json")
            receipt = self.valid_receipt(data)
            if mutation == "truncate":
                receipt["truncation_possible"] = True
                self.rehash_receipt(receipt)
            else:
                del receipt["receipt_sha256"]
            data["collector_receipt"] = receipt
            result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
            self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
            self.assertTrue(result["completeness_claim_blocked"])
            self.assertTrue(any("collector receipt unverifiable" in item for item in result["warnings"]))

    def test_rehashed_row_limit_change_cannot_hide_cap_hit(self) -> None:
        data = self.load_fixture("query_evidence.json")
        raw = [{"EVIDENCE": {"_dataset": "query_history", **data["query_history"]}} for _ in range(1000)]
        _, sql, sources = COLLECTOR.load_surface("query")
        receipt = COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )
        self.assertTrue(receipt["truncation_possible"])
        receipt["row_limit"] = 1001
        receipt["truncation_possible"] = False
        self.rehash_receipt(receipt)
        data["collector_receipt"] = receipt

        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertEqual(result["collector_receipt_assessment"]["status"], "invalid")
        issues = result["collector_receipt_assessment"]["issues"]
        self.assertIn("row_limit does not match the reviewed query SQL cap", issues)
        self.assertIn("truncation_possible does not match row_count and the reviewed SQL cap", issues)
        self.assertIn("row_count is at or above the reviewed SQL cap", issues)
        self.assertTrue(result["completeness_claim_blocked"])

    def test_collector_query_output_matches_analyzer_schema_exactly(self) -> None:
        raw = self.load_fixture("collector_query_output.json")
        data = self.load_fixture("query_evidence.json")
        data["operators"] = []
        data["query_insights"] = []
        _, sql, sources = COLLECTOR.load_surface("query")
        receipt = COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
            source_max_age_seconds=data["metadata"]["source_max_age_seconds"],
        )
        data["query_history"] = receipt["datasets"]["query_history"][0]
        data["collector_receipt"] = receipt

        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))

        self.assertEqual(result["collector_receipt_assessment"]["status"], "trusted_local_boundary")
        self.assertEqual(result["timeline_ms"]["total_elapsed_time_ms"], "153000")
        self.assertEqual(result["timeline_ms"]["queued_overload_time_ms"], "30000")
        self.assertEqual(result["confirmed_observations"], [])
        self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertTrue(any("required operator statistics are absent" in item for item in result["warnings"]))

        sql_text = (SKILL_DIR / "scripts" / "sql" / "query.sql").read_text(encoding="utf-8")
        self.assertIn("'total_elapsed_time_ms', TOTAL_ELAPSED_TIME", sql_text)
        self.assertNotIn("'total_elapsed_time', TOTAL_ELAPSED_TIME", sql_text)

    def test_terminal_statuses_are_scoped_to_the_receipted_surface(self) -> None:
        for terminal_status in ("failed_with_error", "failed_with_incident"):
            self.assertTrue(MODULE.status_is_terminal(MODULE.INFORMATION_SCHEMA_HISTORY_SOURCE, terminal_status))
            data = self.load_fixture("query_evidence.json")
            data["query_history"]["execution_status"] = terminal_status
            result = self.analyze_trusted(data)
            with self.subTest(terminal_status=terminal_status):
                self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
                self.assertTrue(result["completeness_claim_blocked"])
                self.assertEqual(result["confirmed_observations"], [])
                self.assertFalse(result["top_operators_by_observed_percentage"])
        for terminal_status in ("success", "fail", "incident"):
            self.assertTrue(MODULE.status_is_terminal(MODULE.ACCOUNT_USAGE_HISTORY_SOURCE, terminal_status))
        self.assertFalse(MODULE.status_is_terminal(MODULE.ACCOUNT_USAGE_HISTORY_SOURCE, "failed_with_error"))
        self.assertFalse(MODULE.status_is_terminal(MODULE.INFORMATION_SCHEMA_HISTORY_SOURCE, "fail"))

    def test_unknown_execution_status_fails_closed(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["execution_status"] = "finished_somehow"
        result = self.analyze_trusted(data)
        self.assertEqual(result["evidence_binding"]["status"], "INCOMPLETE")
        self.assertFalse(
            any(item["kind"] in {"operator", "query_insight"} for item in result["confirmed_observations"])
        )
        self.assertEqual(result["top_operators_by_observed_percentage"], [])
        self.assertTrue(result["completeness_claim_blocked"])

    def test_rejects_sql_shaped_query_hash(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["query_hash"] = "SELECT secret FROM customer_data"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_receipt_dataset_tamper_blocks_completeness(self) -> None:
        data = self.load_fixture("query_evidence.json")
        receipt = self.valid_receipt(data)
        receipt["datasets"]["query_history"][0]["query_id"] = OTHER_QUERY_ID
        self.rehash_receipt(receipt)
        data["collector_receipt"] = receipt
        result = MODULE.analyze(data, trusted_input_sha256=MODULE.input_sha256(data))
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertIn(
            "query_history rows do not match collector receipt", result["collector_receipt_assessment"]["issues"]
        )


if __name__ == "__main__":
    unittest.main()
