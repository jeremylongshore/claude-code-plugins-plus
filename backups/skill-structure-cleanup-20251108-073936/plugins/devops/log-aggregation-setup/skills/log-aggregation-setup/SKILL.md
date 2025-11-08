---
name: setting-up-log-aggregation
description: |
  This skill sets up log aggregation solutions using ELK (Elasticsearch, Logstash, Kibana), Loki, or Splunk. It generates production-ready configurations and setup code based on specific requirements and infrastructure. Use this skill when the user requests to set up logging infrastructure, configure log aggregation, deploy ELK stack, deploy Loki, deploy Splunk, or needs help with observability. It is triggered by terms like "log aggregation," "ELK setup," "Loki configuration," "Splunk deployment," or similar requests for centralized logging solutions.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill simplifies the deployment and configuration of log aggregation systems. It automates the process of setting up ELK, Loki, or Splunk, providing production-ready configurations tailored to your environment.

## How It Works

1. **Requirement Gathering**: The skill identifies the user's specific requirements, including the desired log aggregation platform (ELK, Loki, or Splunk), infrastructure details, and security considerations.
2. **Configuration Generation**: Based on the gathered requirements, the skill generates the necessary configuration files for the chosen platform. This includes configurations for data ingestion, processing, storage, and visualization.
3. **Setup Code Generation**: The skill provides the setup code needed to deploy and configure the log aggregation solution on the target infrastructure. This might include scripts, Docker Compose files, or other deployment artifacts.

## When to Use This Skill

This skill activates when you need to:
- Deploy a new log aggregation system.
- Configure an existing log aggregation system.
- Migrate from one log aggregation system to another.

## Examples

### Example 1: Deploying an ELK Stack

User request: "Set up an ELK stack for my Kubernetes cluster to aggregate application logs."

The skill will:
1. Generate Elasticsearch, Logstash, and Kibana configuration files optimized for Kubernetes.
2. Provide a Docker Compose file or Kubernetes manifests for deploying the ELK stack.

### Example 2: Configuring Loki for a Docker Swarm

User request: "Configure Loki to aggregate logs from my Docker Swarm environment."

The skill will:
1. Generate a Loki configuration file optimized for Docker Swarm.
2. Provide instructions for deploying Loki as a service within the Swarm.

## Best Practices

- **Security**: Ensure that all generated configurations adhere to security best practices, including proper authentication and authorization mechanisms.
- **Scalability**: Design the log aggregation system to be scalable, allowing it to handle increasing log volumes over time.
- **Monitoring**: Implement monitoring for the log aggregation system itself to ensure its health and performance.

## Integration

This skill can integrate with other deployment and infrastructure management tools in the Claude Code ecosystem to automate the entire deployment process. It can also work with security analysis tools to ensure log data is securely handled.