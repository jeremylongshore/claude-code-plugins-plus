from __future__ import annotations

import importlib.util
import json
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
        expected_sql = {
            "snowflake-access-guardian": "access.sql",
            "snowflake-cost-leak-hunter": "cost.sql",
            "snowflake-data-quality-sentinel": "data-quality.sql",
            "snowflake-deploy-medic": "query.sql",
            "snowflake-failover-readiness-drill": "replication.sql",
            "snowflake-pipeline-guardian": "pipeline.sql",
            "snowflake-query-forensics": "query.sql",
            "snowflake-strong-auth-migration-pilot": "auth.sql",
        }
        skills_dir = SCRIPT.parents[2] / "skills"
        bundled = sorted(skills_dir.glob("*/scripts/collect_snowflake_evidence.py"))
        self.assertEqual(len(bundled), 8)
        for path in bundled:
            with self.subTest(skill=path.parents[1].name):
                self.assertEqual(path.read_bytes(), canonical)
                bundled_sql = {item.name: item.read_bytes() for item in sorted((path.parent / "sql").glob("*.sql"))}
                filename = expected_sql[path.parents[1].name]
                self.assertEqual(bundled_sql, {filename: canonical_sql[filename]})

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
            "hasPassword": True,
            "has_pat": False,
            "hasRsaPublicKey": True,
            "has-workload-identity": False,
        }
        datasets, _ = MODULE.normalize_cli_json([{"EVIDENCE": {"_dataset": "users", **safe_flags}}])
        for key, expected in safe_flags.items():
            self.assertIs(datasets["users"][0][key], expected)

    def test_relevant_sql_surfaces_are_deterministically_ordered(self) -> None:
        for surface in ("cost", "query", "pipeline"):
            with self.subTest(surface=surface):
                _, sql, _ = MODULE.load_surface(surface)
                self.assertIn("ORDER BY dataset, sort_key", sql)

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

            receipt, code = MODULE.execute_surface("cost", "readonly", runner=runner)
            rendered = json.dumps(receipt)

            with self.subTest(message=message):
                self.assertEqual(code, 5)
                self.assertEqual(receipt["status"], "error")
                self.assertEqual(receipt["row_count"], 0)
                for fragment in forbidden:
                    self.assertNotIn(fragment, rendered)
                self.assertTrue(
                    any(
                        marker in rendered
                        for marker in (
                            "[REDACTED_AUTHORIZATION]",
                            "[REDACTED_CREDENTIAL]",
                            "[REDACTED_SQL]",
                        )
                    )
                )

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

                with self.subTest(message=message):
                    self.assertEqual(json.loads(rendered)["status"], "error")
                    for fragment in forbidden:
                        self.assertNotIn(fragment, rendered)
                    self.assertRegex(rendered, r"\[REDACTED_(?:AUTHORIZATION|CREDENTIAL|SQL)\]")

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
                        "cost",
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
                    "cost",
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


if __name__ == "__main__":
    unittest.main()
