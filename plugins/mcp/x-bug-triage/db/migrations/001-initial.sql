-- X Bug Triage Plugin — SQLite Schema v1
-- 8 tables + schema versioning

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (datetime('now')),
  description TEXT
);

CREATE TABLE IF NOT EXISTS triage_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'partial', 'failed')),
  accounts_ingested TEXT,
  endpoints_summary TEXT,
  candidates_parsed INTEGER NOT NULL DEFAULT 0,
  clusters_created INTEGER NOT NULL DEFAULT 0,
  clusters_updated INTEGER NOT NULL DEFAULT 0,
  warnings TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
  post_id TEXT PRIMARY KEY,
  author_handle TEXT NOT NULL,
  author_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('reply', 'mention', 'quote_post', 'search_hit', 'stream_hit')),
  product_surface TEXT,
  feature_area TEXT,
  symptoms TEXT,
  error_strings TEXT,
  repro_hints TEXT,
  urls TEXT,
  has_media INTEGER NOT NULL DEFAULT 0,
  media_keys TEXT,
  language TEXT,
  conversation_id TEXT,
  thread_root_id TEXT,
  reply_to_id TEXT,
  referenced_post_ids TEXT,
  public_metrics TEXT,
  classification TEXT NOT NULL CHECK (classification IN (
    'bug_report', 'sarcastic_bug_report', 'feature_request', 'account_problem',
    'billing_problem', 'policy_or_expectation_mismatch', 'ux_friction',
    'model_quality_issue', 'user_error_or_confusion', 'praise', 'noise', 'needs_review'
  )),
  classification_confidence REAL NOT NULL,
  classification_rationale TEXT,
  report_quality_score REAL,
  independence_score REAL,
  account_authenticity_score REAL,
  historical_accuracy_score REAL,
  reporter_reliability_score REAL,
  reporter_category TEXT NOT NULL DEFAULT 'public' CHECK (reporter_category IN ('public', 'internal', 'partner', 'tester')),
  pii_flags TEXT,
  raw_text_redacted TEXT,
  raw_text_storage_policy TEXT NOT NULL DEFAULT 'store_redacted' CHECK (raw_text_storage_policy IN ('store_redacted', 'store_hash_only', 'do_not_store')),
  triage_run_id TEXT NOT NULL REFERENCES triage_runs(run_id)
);

CREATE TABLE IF NOT EXISTS clusters (
  cluster_id TEXT PRIMARY KEY,
  bug_signature TEXT NOT NULL,
  cluster_family TEXT NOT NULL CHECK (cluster_family IN ('product_defect', 'model_quality_defect', 'policy_mismatch', 'ux_friction')),
  product_surface TEXT,
  feature_area TEXT,
  title TEXT,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  severity_rationale TEXT,
  state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'filed', 'monitoring', 'fix_deployed', 'resolved', 'closed', 'suppressed')),
  sub_status TEXT CHECK (sub_status IS NULL OR sub_status IN ('new_evidence', 'late_tail', 'regression_reopened', 'possible_duplicate')),
  report_count INTEGER NOT NULL DEFAULT 0,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  triage_run_id TEXT NOT NULL REFERENCES triage_runs(run_id)
);

CREATE TABLE IF NOT EXISTS cluster_posts (
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  post_id TEXT NOT NULL REFERENCES candidates(post_id),
  added_at TEXT NOT NULL,
  added_by_run_id TEXT NOT NULL REFERENCES triage_runs(run_id),
  PRIMARY KEY (cluster_id, post_id)
);

CREATE TABLE IF NOT EXISTS overrides (
  override_id TEXT PRIMARY KEY,
  override_type TEXT NOT NULL CHECK (override_type IN (
    'cluster_merge', 'cluster_split', 'noise_suppression', 'routing_override',
    'issue_family_link', 'severity_override', 'label_correction', 'snooze'
  )),
  target_cluster_id TEXT,
  parameters TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suppression_rules (
  rule_id TEXT PRIMARY KEY,
  pattern_type TEXT NOT NULL,
  pattern_value TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS issue_links (
  link_id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  issue_url TEXT NOT NULL,
  issue_number INTEGER,
  repo TEXT NOT NULL,
  link_type TEXT NOT NULL CHECK (link_type IN ('filed', 'merged', 'related')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'ingest_run_started', 'ingest_run_completed', 'source_fetched',
    'candidate_classified', 'pii_redaction', 'cluster_created',
    'cluster_updated', 'cluster_state_changed', 'routing_recommendation',
    'escalation_triggered', 'human_action', 'override_created'
  )),
  timestamp TEXT NOT NULL,
  run_id TEXT,
  cluster_id TEXT,
  post_id TEXT,
  details TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_candidates_triage_run ON candidates(triage_run_id);
CREATE INDEX IF NOT EXISTS idx_candidates_classification ON candidates(classification);
CREATE INDEX IF NOT EXISTS idx_candidates_timestamp ON candidates(timestamp);
CREATE INDEX IF NOT EXISTS idx_clusters_state ON clusters(state);
CREATE INDEX IF NOT EXISTS idx_clusters_family ON clusters(cluster_family);
CREATE INDEX IF NOT EXISTS idx_clusters_signature ON clusters(bug_signature);
CREATE INDEX IF NOT EXISTS idx_cluster_posts_post ON cluster_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_overrides_type ON overrides(override_type);
CREATE INDEX IF NOT EXISTS idx_overrides_active ON overrides(active);
CREATE INDEX IF NOT EXISTS idx_suppression_active ON suppression_rules(active);
CREATE INDEX IF NOT EXISTS idx_issue_links_cluster ON issue_links(cluster_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_run ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
