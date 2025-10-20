---
name: Building Recommendation Systems
description: |
  This skill empowers Claude to construct recommendation systems using collaborative filtering, content-based filtering, or hybrid approaches. It analyzes user preferences, item features, and interaction data to generate personalized recommendations. Use this skill when the user requests to build a recommendation engine, needs help with collaborative filtering, wants to implement content-based filtering, or seeks to rank items based on relevance for a specific user or group of users. It is triggered by requests involving "recommendations", "collaborative filtering", "content-based filtering", "ranking items", or "building a recommender".
---

## Overview

This skill enables Claude to design and implement recommendation systems tailored to specific datasets and use cases. It automates the process of selecting appropriate algorithms, preprocessing data, training models, and evaluating performance, ultimately providing users with a functional recommendation engine.

## How It Works

1. **Analyzing Requirements**: Claude identifies the type of recommendation needed (collaborative, content-based, hybrid), data availability, and performance goals.
2. **Generating Code**: Claude generates Python code using relevant libraries (e.g., scikit-learn, TensorFlow, PyTorch) to build the recommendation model. This includes data loading, preprocessing, model training, and evaluation.
3. **Implementing Best Practices**: The code incorporates best practices for recommendation system development, such as handling cold starts, addressing scalability, and mitigating bias.

## When to Use This Skill

This skill activates when you need to:
- Build a personalized movie recommendation system.
- Create a product recommendation engine for an e-commerce platform.
- Implement a content recommendation system for a news website.

## Examples

### Example 1: Personalized Movie Recommendations

User request: "Build a movie recommendation system using collaborative filtering."

The skill will:
1. Generate code to load and preprocess movie rating data.
2. Implement a collaborative filtering algorithm (e.g., matrix factorization) to predict user preferences.

### Example 2: E-commerce Product Recommendations

User request: "Create a product recommendation engine for an online store, using content-based filtering."

The skill will:
1. Generate code to extract features from product descriptions and user purchase history.
2. Implement a content-based filtering algorithm to recommend similar products.

## Best Practices

- **Data Preprocessing**: Ensure data is properly cleaned and formatted before training the recommendation model.
- **Model Evaluation**: Use appropriate metrics (e.g., precision, recall, NDCG) to evaluate the performance of the recommendation system.
- **Scalability**: Design the recommendation system to handle large datasets and user bases efficiently.

## Integration

This skill can be integrated with other Claude Code plugins to access data sources, deploy models, and monitor performance. For example, it can use data analysis plugins to extract features from raw data and deployment plugins to deploy the recommendation system to a production environment.