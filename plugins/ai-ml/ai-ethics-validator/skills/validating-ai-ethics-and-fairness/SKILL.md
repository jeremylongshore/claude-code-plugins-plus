---
name: validating-ai-ethics-and-fairness
description: |
  Validate AI/ML models and datasets for bias, fairness, and ethical concerns.
  Use when auditing AI systems for ethical compliance, fairness assessment, or bias detection.
  Trigger with phrases like "evaluate model fairness", "check for bias", or "validate AI ethics".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# AI Ethics Validator

## Overview

Validate AI/ML models and datasets for bias, fairness, and ethical compliance using quantitative fairness metrics and structured audit workflows. This skill computes demographic parity, equalized odds, calibration scores, and disparate impact ratios across protected groups, then generates severity-classified findings with actionable mitigation strategies aligned to IEEE, EU, and ACM ethical frameworks.

## Prerequisites

- Python 3.9+ with Fairlearn >= 0.9 (`pip install fairlearn`)
- IBM AI Fairness 360 toolkit (`pip install aif360`) for comprehensive bias analysis
- pandas, NumPy, and scikit-learn for data manipulation and model evaluation
- Model predictions (probabilities or binary labels) and corresponding ground truth labels
- Demographic attribute columns (age, gender, race, etc.) accessible under appropriate data governance
- Optional: Google What-If Tool for interactive fairness exploration on TensorFlow models

## Instructions

1. Load the model predictions and ground truth dataset using the Read tool; verify schema includes sensitive attribute columns
2. Define the protected attributes and privileged/unprivileged group definitions for the fairness analysis
3. Compute representation statistics: group counts, class label distributions, and feature coverage per demographic segment
4. Calculate core fairness metrics using Fairlearn or AIF360:
   - Demographic parity ratio (selection rate parity across groups)
   - Equalized odds difference (TPR and FPR parity)
   - Equal opportunity difference (TPR parity only)
   - Predictive parity (precision parity across groups)
   - Calibration scores per group (predicted probability vs observed outcome)
5. Apply four-fifths rule: flag any metric where the ratio falls below 0.80 as potential adverse impact
6. Classify each finding by severity: low (ratio 0.90-1.0), medium (0.80-0.90), high (0.70-0.80), critical (below 0.70)
7. Identify proxy variables by computing correlation between non-protected features and sensitive attributes
8. Generate mitigation recommendations: resampling, reweighting, threshold adjustment, or in-processing constraints (e.g., `ExponentiatedGradient` from Fairlearn)
9. Produce a compliance assessment mapping findings to IEEE Ethically Aligned Design, EU Ethics Guidelines for Trustworthy AI, and ACM Code of Ethics
10. Document all ethical decisions, trade-offs, and residual risks in a structured audit report

## Output

- Fairness metric dashboard: per-group values for demographic parity, equalized odds, equal opportunity, predictive parity, and calibration
- Severity-classified findings table: metric name, affected groups, ratio value, severity level, recommended action
- Representation analysis: group sizes, class distributions, feature coverage gaps
- Proxy variable report: features correlated with protected attributes above threshold (r > 0.3)
- Mitigation plan: ranked strategies with expected fairness improvement and accuracy trade-off estimates
- Compliance matrix: pass/fail against IEEE, EU, and ACM ethical guidelines with evidence citations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient group sample size | Fewer than 30 observations in a demographic group | Aggregate related subgroups; use bootstrap confidence intervals; flag metric as unreliable |
| Missing sensitive attributes | Protected attribute columns absent from dataset | Apply proxy detection via correlated features; request attribute access under data governance approval |
| Conflicting fairness criteria | Demographic parity and equalized odds contradict | Document the impossibility theorem trade-off; prioritize the metric most aligned with the deployment context |
| Data quality failures | Inconsistent encoding or null values in attribute columns | Standardize categorical encodings; impute or exclude nulls; validate with schema checks before analysis |
| Model output format mismatch | Predictions not in expected probability or binary format | Convert logits to probabilities via sigmoid; binarize at the decision threshold before metric computation |

## Examples

**Scenario 1: Hiring Model Audit** -- Validate a resume-screening classifier for gender and age bias. Compute demographic parity across male/female groups and age buckets (18-30, 31-50, 51+). Apply the four-fifths rule. Finding: female selection rate at 0.72 of male rate (critical severity). Recommend reweighting training samples and adjusting the decision threshold.

**Scenario 2: Credit Scoring Fairness** -- Assess a credit approval model for racial disparate impact. Calculate equalized odds (TPR and FPR) across racial groups. Finding: FPR for Group A is 2.1x Group B (high severity). Recommend in-processing constraint using `ExponentiatedGradient` with `FalsePositiveRateParity`.

**Scenario 3: Healthcare Risk Prediction** -- Evaluate a patient risk model for age and socioeconomic bias. Compute calibration curves per group. Finding: model overestimates risk for low-income patients by 15%. Recommend recalibration using Platt scaling per subgroup with post-deployment monitoring for fairness drift.

## Resources

- [Fairlearn Documentation](https://fairlearn.org/) -- bias detection, mitigation algorithms, MetricFrame API
- [AI Fairness 360 (AIF360)](https://aif360.mybluemix.net/) -- comprehensive fairness toolkit with 70+ metrics
- [Google What-If Tool](https://pair-code.github.io/what-if-tool/) -- interactive fairness exploration
- [EU Ethics Guidelines for Trustworthy AI](https://ec.europa.eu/digital-strategy/en/policies/expert-group-ai) -- regulatory framework
- [IEEE Ethically Aligned Design](https://ethicsinaction.ieee.org/) -- technical ethics standards
- Impossibility theorem reference: Chouldechova (2017) on incompatibility of fairness criteria