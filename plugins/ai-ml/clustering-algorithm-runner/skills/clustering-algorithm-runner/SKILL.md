---
name: running-clustering-algorithms
description: |
  This skill enables Claude to execute clustering algorithms on datasets. It is used when the user requests to perform clustering, identify groups within data, or analyze data structure. The skill supports algorithms like K-means, DBSCAN, and hierarchical clustering. Claude should use this skill when the user explicitly asks to "run clustering," "perform a cluster analysis," or "group data points" and provides a dataset or a way to access one. The skill also handles data validation, error handling, performance metrics, and artifact saving.
---

## Overview

This skill empowers Claude to perform clustering analysis on provided datasets. It allows for automated execution of various clustering algorithms, providing insights into data groupings and structures.

## How It Works

1. **Analyzing the Context**: Claude analyzes the user's request to determine the dataset, desired clustering algorithm (if specified), and any specific requirements.
2. **Generating Code**: Claude generates Python code using appropriate ML libraries (e.g., scikit-learn) to perform the clustering task, including data loading, preprocessing, algorithm execution, and result visualization.
3. **Executing Clustering**: The generated code is executed, and the clustering algorithm is applied to the dataset.
4. **Providing Results**: Claude presents the results, including cluster assignments, performance metrics (e.g., silhouette score, Davies-Bouldin index), and visualizations (e.g., scatter plots with cluster labels).

## When to Use This Skill

This skill activates when you need to:
- Identify distinct groups within a dataset.
- Perform a cluster analysis to understand data structure.
- Run K-means, DBSCAN, or hierarchical clustering on a given dataset.

## Examples

### Example 1: Customer Segmentation

User request: "Run clustering on this customer data to identify customer segments. The data is in customer_data.csv."

The skill will:
1. Load the customer_data.csv dataset.
2. Perform K-means clustering to identify distinct customer segments based on their attributes.
3. Provide a visualization of the customer segments and their characteristics.

### Example 2: Anomaly Detection

User request: "Perform DBSCAN clustering on this network traffic data to identify anomalies. The data is available at network_traffic.txt."

The skill will:
1. Load the network_traffic.txt dataset.
2. Perform DBSCAN clustering to identify outliers representing anomalous network traffic.
3. Report the identified anomalies and their characteristics.

## Best Practices

- **Data Preprocessing**: Always preprocess the data (e.g., scaling, normalization) before applying clustering algorithms to improve performance and accuracy.
- **Algorithm Selection**: Choose the appropriate clustering algorithm based on the data characteristics and the desired outcome. K-means is suitable for spherical clusters, while DBSCAN is better for non-spherical clusters and anomaly detection.
- **Parameter Tuning**: Tune the parameters of the clustering algorithm (e.g., number of clusters in K-means, epsilon and min_samples in DBSCAN) to optimize the results.

## Integration

This skill can be integrated with data loading skills to retrieve datasets from various sources. It can also be combined with visualization skills to generate insightful visualizations of the clustering results.