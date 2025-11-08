# Scripts

Bundled resources for performance-regression-detector skill

- [ ] analyze_metrics.py: Analyzes performance metrics from CI/CD pipeline output, comparing against baselines and thresholds. Returns a JSON object indicating regressions.
- [ ] generate_report.py: Generates a human-readable report summarizing detected performance regressions, including affected metrics, severity, and potential causes.
- [ ] create_github_comment.py: Creates a comment on a GitHub pull request, highlighting detected performance regressions and linking to the generated report.
