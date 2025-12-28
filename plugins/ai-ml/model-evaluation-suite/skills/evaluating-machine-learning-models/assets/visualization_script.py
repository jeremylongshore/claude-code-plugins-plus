#!/usr/bin/env python3

"""
visualization_script.py

This script generates visualizations of model performance metrics.
It supports various plot types and data formats.

Example Usage:
    To generate a scatter plot of predicted vs. actual values:
    python visualization_script.py --plot_type scatter --actual_values actual.csv --predicted_values predicted.csv --output scatter_plot.png

    To generate a histogram of errors:
    python visualization_script.py --plot_type histogram --errors errors.csv --output error_histogram.png
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os


def generate_scatter_plot(actual_values_path, predicted_values_path, output_path):
    """
    Generates a scatter plot of actual vs. predicted values.

    Args:
        actual_values_path (str): Path to the CSV file containing actual values.
        predicted_values_path (str): Path to the CSV file containing predicted values.
        output_path (str): Path to save the generated plot.
    """
    try:
        actual_values = pd.read_csv(actual_values_path).values.flatten()
        predicted_values = pd.read_csv(predicted_values_path).values.flatten()

        plt.figure(figsize=(10, 8))
        sns.scatterplot(x=actual_values, y=predicted_values)
        plt.xlabel("Actual Values")
        plt.ylabel("Predicted Values")
        plt.title("Actual vs. Predicted Values")
        plt.savefig(output_path)
        plt.close()

        print(f"Scatter plot saved to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
    except Exception as e:
        print(f"Error generating scatter plot: {e}")


def generate_histogram(errors_path, output_path):
    """
    Generates a histogram of errors.

    Args:
        errors_path (str): Path to the CSV file containing errors.
        output_path (str): Path to save the generated plot.
    """
    try:
        errors = pd.read_csv(errors_path).values.flatten()

        plt.figure(figsize=(10, 8))
        sns.histplot(errors, kde=True)  # Add kernel density estimate
        plt.xlabel("Error")
        plt.ylabel("Frequency")
        plt.title("Distribution of Errors")
        plt.savefig(output_path)
        plt.close()

        print(f"Histogram saved to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
    except Exception as e:
        print(f"Error generating histogram: {e}")


def generate_residual_plot(actual_values_path, predicted_values_path, output_path):
    """
    Generates a residual plot.

    Args:
        actual_values_path (str): Path to the CSV file containing actual values.
        predicted_values_path (str): Path to the CSV file containing predicted values.
        output_path (str): Path to save the generated plot.
    """
    try:
        actual_values = pd.read_csv(actual_values_path).values.flatten()
        predicted_values = pd.read_csv(predicted_values_path).values.flatten()

        residuals = actual_values - predicted_values

        plt.figure(figsize=(10, 8))
        sns.scatterplot(x=predicted_values, y=residuals)
        plt.xlabel("Predicted Values")
        plt.ylabel("Residuals")
        plt.title("Residual Plot")
        plt.axhline(y=0, color='r', linestyle='--')  # Add a horizontal line at y=0
        plt.savefig(output_path)
        plt.close()

        print(f"Residual plot saved to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}")
    except Exception as e:
        print(f"Error generating residual plot: {e}")


def main():
    """
    Main function to parse arguments and generate visualizations.
    """
    parser = argparse.ArgumentParser(
        description="Generate visualizations of model performance metrics."
    )
    parser.add_argument(
        "--plot_type",
        type=str,
        required=True,
        choices=["scatter", "histogram", "residual"],
        help="Type of plot to generate (scatter, histogram, residual).",
    )
    parser.add_argument(
        "--actual_values",
        type=str,
        help="Path to the CSV file containing actual values (required for scatter and residual plots).",
    )
    parser.add_argument(
        "--predicted_values",
        type=str,
        help="Path to the CSV file containing predicted values (required for scatter and residual plots).",
    )
    parser.add_argument(
        "--errors",
        type=str,
        help="Path to the CSV file containing errors (required for histogram).",
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to save the generated plot."
    )

    args = parser.parse_args()

    if args.plot_type == "scatter":
        if not args.actual_values or not args.predicted_values:
            print(
                "Error: --actual_values and --predicted_values are required for scatter plots."
            )
            return
        generate_scatter_plot(args.actual_values, args.predicted_values, args.output)
    elif args.plot_type == "histogram":
        if not args.errors:
            print("Error: --errors is required for histograms.")
            return
        generate_histogram(args.errors, args.output)
    elif args.plot_type == "residual":
        if not args.actual_values or not args.predicted_values:
            print(
                "Error: --actual_values and --predicted_values are required for residual plots."
            )
            return
        generate_residual_plot(args.actual_values, args.predicted_values, args.output)


if __name__ == "__main__":
    main()