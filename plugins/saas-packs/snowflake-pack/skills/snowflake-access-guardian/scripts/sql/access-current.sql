-- Current session-visible account grants. SHOW output is intentionally kept
-- operator-scoped; it is not a substitute for named SHOW GRANTS TO ROLE/USER
-- and SHOW FUTURE GRANTS checks supplied with the access request.
SHOW GRANTS ON ACCOUNT LIMIT 10000;
