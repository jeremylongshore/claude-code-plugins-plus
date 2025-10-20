---
name: Processing Computer Vision Tasks
description: |
  This skill enables Claude to process and analyze images using computer vision techniques. It's used to perform tasks such as object detection, image classification, and image segmentation. Use this skill when a user requests analysis of an image, asks for identification of objects within an image, or needs help with other computer vision related tasks. Trigger terms include "analyze image", "object detection", "image classification", "image segmentation", "computer vision", "process image", or when the user provides an image and asks for insights.
---

## Overview

This skill empowers Claude to leverage the computer-vision-processor plugin to analyze images, detect objects, and extract meaningful information. It automates computer vision workflows, optimizes performance, and provides detailed insights based on image content.

## How It Works

1. **Analyzing the Request**: Claude identifies the need for computer vision processing based on the user's request and trigger terms.
2. **Generating Code**: Claude generates the appropriate Python code to interact with the computer-vision-processor plugin, specifying the desired analysis type (e.g., object detection, image classification).
3. **Executing the Task**: The generated code is executed using the `/process-vision` command, which processes the image and returns the results.

## When to Use This Skill

This skill activates when you need to:
- Analyze an image for specific objects or features.
- Classify an image into predefined categories.
- Segment an image to identify different regions or objects.

## Examples

### Example 1: Object Detection

User request: "Analyze this image and identify all the cars and pedestrians."

The skill will:
1. Generate code to perform object detection on the provided image using the computer-vision-processor plugin.
2. Return a list of bounding boxes and labels for each detected car and pedestrian.

### Example 2: Image Classification

User request: "Classify this image. Is it a cat or a dog?"

The skill will:
1. Generate code to perform image classification on the provided image using the computer-vision-processor plugin.
2. Return the classification result (e.g., "cat" or "dog") along with a confidence score.

## Best Practices

- **Data Validation**: Always validate the input image to ensure it's in a supported format and resolution.
- **Error Handling**: Implement robust error handling to gracefully manage potential issues during image processing.
- **Performance Optimization**: Choose the appropriate computer vision techniques and parameters to optimize performance for the specific task.

## Integration

This skill utilizes the `/process-vision` command provided by the computer-vision-processor plugin. It can be integrated with other skills to further process the results of the computer vision analysis, such as generating reports or triggering actions based on detected objects.