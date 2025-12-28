---
name: detecting-data-anomalies
description: |
  Identify anomalies and outliers in datasets using machine learning algorithms.
  Use when analyzing data for unusual patterns, outliers, or unexpected deviations from normal behavior.
  Trigger with phrases like "detect anomalies", "find outliers", or "identify unusual patterns".
  
allowed-tools: Read, Bash(python:*), Grep, Glob
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Anomaly Detection System

This skill provides automated assistance for anomaly detection system tasks.

## Prerequisites

Before using this skill, ensure you have:
- Dataset in accessible format (CSV, JSON, or database)
- Python environment with scikit-learn or similar ML libraries
- Understanding of data distribution and expected patterns
- Sufficient data volume for statistical significance
- Knowledge of domain-specific normal behavior
- Data preprocessing capabilities for cleaning and scaling

## Instructions

### Step 1: Prepare Data for Analysis
Set up the dataset for anomaly detection:
1. Load dataset using Read tool
2. Inspect data structure and identify relevant features
3. Clean data by handling missing values and inconsistencies
4. Normalize or scale features as appropriate for algorithm
5. Split temporal data if time-series analysis is needed

### Step 2: Select Detection Algorithm
Choose appropriate anomaly detection method based on data characteristics:
- **Isolation Forest**: For high-dimensional data with complex anomalies
- **One-Class SVM**: For clearly defined normal behavior patterns
- **Local Outlier Factor (LOF)**: For density-based anomaly detection
- **Statistical Methods**: For simple univariate or multivariate analysis
- **Autoencoders**: For complex patterns in large datasets

### Step 3: Configure Detection Parameters
Set algorithm parameters to balance sensitivity:
- Define contamination rate (expected proportion of anomalies)
- Set distance metrics appropriate for feature types
- Configure threshold values for anomaly scoring
- Establish validation strategy for parameter tuning

### Step 4: Execute Anomaly Detection
Run the detection algorithm on prepared data:
1. Apply selected algorithm using Bash tool
2. Generate anomaly scores for each data point
3. Classify points as normal or anomalous based on threshold
4. Extract characteristics of identified anomalies

### Step 5: Analyze and Report Results
Interpret detection results and provide insights:
- Summarize number and distribution of anomalies
- Highlight most significant outliers with context
- Identify patterns or clusters among anomalies
- Generate visualizations showing anomaly distribution
- Provide recommendations for further investigation

## Output

The skill produces comprehensive anomaly detection results:

### Anomaly Summary Report
- Total data points analyzed
- Number of anomalies detected
- Contamination rate (percentage of anomalies)
- Algorithm used and configuration parameters
- Confidence scores for detected anomalies

### Detailed Anomaly List
For each detected anomaly:
- Record identifier and timestamp (if applicable)
- Anomaly score and confidence level
- Feature values showing deviation from normal
- Contextual information about the outlier
- Severity classification (low, medium, high, critical)

### Statistical Analysis
- Distribution of anomaly scores across dataset
- Feature importance for anomaly classification
- Comparison with normal data patterns
- Temporal distribution of anomalies (if time-series)
- Clustering analysis of anomaly types

### Visualizations
- Scatter plots highlighting anomalies in feature space
- Time-series plots with anomaly markers
- Distribution histograms comparing normal vs anomalous data
- Heatmaps showing feature correlations for anomalies

### Recommendations
- Suggested follow-up investigations for critical anomalies
- Data quality improvements to reduce false positives
- Monitoring strategies for real-time detection
- Algorithm refinements based on domain knowledge

## Error Handling

Common issues and solutions:

**Insufficient Data Volume**
- Error: Not enough data points for statistical significance
- Solution: Collect more data, adjust contamination rate, or use simpler statistical methods

**High False Positive Rate**
- Error: Too many normal points classified as anomalies
- Solution: Adjust detection threshold, refine feature selection, or use domain-specific constraints

**Algorithm Performance Issues**
- Error: Detection algorithm too slow for large datasets
- Solution: Use sampling techniques, optimize parameters, or switch to faster algorithms like Isolation Forest

**Feature Scaling Problems**
- Error: Anomalies dominated by high-magnitude features
- Solution: Apply appropriate normalization or standardization to all features before detection

**Missing Ground Truth**
- Error: Unable to validate detection accuracy without labels
- Solution: Use domain expertise for manual validation, implement feedback loop for model improvement

## Resources

### Anomaly Detection Algorithms
- Isolation Forest documentation and implementation examples
- One-Class SVM for novelty detection
- Local Outlier Factor (LOF) for density-based detection
- Autoencoder-based anomaly detection for deep learning approaches

### Python Libraries
- scikit-learn anomaly detection module
- PyOD (Python Outlier Detection) comprehensive library
- TensorFlow/PyTorch for deep learning-based detection
- statsmodels for statistical anomaly detection

### Domain-Specific Applications
- Fraud detection in financial transactions
- Network intrusion detection and security monitoring
- Manufacturing quality control and defect detection
- Healthcare anomaly detection for patient monitoring
- IoT sensor data anomaly identification

### Best Practices
- Balance sensitivity to avoid excessive false positives
- Validate results with domain experts
- Monitor detection performance over time
- Update models as normal behavior evolves
- Document anomaly investigation procedures

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.