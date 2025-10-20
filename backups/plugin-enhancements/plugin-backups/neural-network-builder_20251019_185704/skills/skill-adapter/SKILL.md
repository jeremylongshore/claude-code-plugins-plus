---
name: Building Neural Networks
description: |
  This skill allows Claude to construct and configure neural network architectures using the neural-network-builder plugin. It should be used when the user requests the creation of a new neural network, modification of an existing one, or assistance with defining the layers, parameters, and training process. The skill is triggered by requests involving terms like "build a neural network," "define network architecture," "configure layers," or specific mentions of neural network types (e.g., "CNN," "RNN," "transformer").
---

## Overview

This skill empowers Claude to design and implement neural networks tailored to specific tasks. It leverages the neural-network-builder plugin to automate the process of defining network architectures, configuring layers, and setting training parameters. This ensures efficient and accurate creation of neural network models.

## How It Works

1. **Analyzing Requirements**: Claude analyzes the user's request to understand the desired neural network architecture, task, and performance goals.
2. **Generating Configuration**: Based on the analysis, Claude generates the appropriate configuration for the neural-network-builder plugin, specifying the layers, activation functions, and other relevant parameters.
3. **Executing Build**: Claude executes the `build-nn` command, triggering the neural-network-builder plugin to construct the neural network based on the generated configuration.

## When to Use This Skill

This skill activates when you need to:
- Create a new neural network architecture for a specific machine learning task.
- Modify an existing neural network's layers, parameters, or training process.
- Design a neural network using specific layer types, such as convolutional, recurrent, or transformer layers.

## Examples

### Example 1: Image Classification

User request: "Build a convolutional neural network for image classification with three convolutional layers and two fully connected layers."

The skill will:
1. Analyze the request and determine the required CNN architecture.
2. Generate the configuration for the `build-nn` command, specifying the layer types, filter sizes, and activation functions.

### Example 2: Text Generation

User request: "Define an RNN architecture for text generation with LSTM cells and an embedding layer."

The skill will:
1. Analyze the request and determine the required RNN architecture.
2. Generate the configuration for the `build-nn` command, specifying the LSTM cell parameters, embedding dimension, and output layer.

## Best Practices

- **Layer Selection**: Choose appropriate layer types (e.g., convolutional, recurrent, transformer) based on the task and data characteristics.
- **Parameter Tuning**: Experiment with different parameter values (e.g., learning rate, batch size, number of layers) to optimize performance.
- **Regularization**: Implement regularization techniques (e.g., dropout, L1/L2 regularization) to prevent overfitting.

## Integration

This skill integrates with the core Claude Code environment by utilizing the `build-nn` command provided by the neural-network-builder plugin. It can be combined with other skills for data preprocessing, model evaluation, and deployment.