#!/usr/bin/env python3

"""
This script provides a template for visualizing regression model results.

It includes functionalities for plotting predicted vs. actual values,
residual plots, and other visualizations to assess model performance.
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score
from typing import Optional


def plot_predicted_vs_actual(
    y_true: np.ndarray, y_pred: np.ndarray, title: str = "Predicted vs. Actual"
) -> None:
    """
    Plots predicted values against actual values.

    Args:
        y_true (np.ndarray): Array of actual values.
        y_pred (np.ndarray): Array of predicted values.
        title (str, optional): Title of the plot. Defaults to "Predicted vs. Actual".
    """
    try:
        plt.figure(figsize=(8, 6))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.xlabel("Actual Values")
        plt.ylabel("Predicted Values")
        plt.title(title)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], "k--", lw=2)
        plt.show()
    except Exception as e:
        print(f"Error plotting predicted vs. actual: {e}")


def plot_residuals(
    y_true: np.ndarray, y_pred: np.ndarray, title: str = "Residual Plot"
) -> None:
    """
    Plots the residuals (errors) of the regression model.

    Args:
        y_true (np.ndarray): Array of actual values.
        y_pred (np.ndarray): Array of predicted values.
        title (str, optional): Title of the plot. Defaults to "Residual Plot".
    """
    try:
        residuals = y_true - y_pred
        plt.figure(figsize=(8, 6))
        plt.scatter(y_pred, residuals, alpha=0.5)
        plt.xlabel("Predicted Values")
        plt.ylabel("Residuals")
        plt.title(title)
        plt.axhline(y=0, color="k", linestyle="--")  # Add a horizontal line at y=0
        plt.show()
    except Exception as e:
        print(f"Error plotting residuals: {e}")


def visualize_regression_results(
    y_true: np.ndarray, y_pred: np.ndarray, model_name: str = "Regression Model"
) -> None:
    """
    Visualizes the regression results, including predicted vs. actual and residual plots.

    Args:
        y_true (np.ndarray): Array of actual values.
        y_pred (np.ndarray): Array of predicted values.
        model_name (str, optional): Name of the regression model. Defaults to "Regression Model".
    """
    try:
        plot_predicted_vs_actual(
            y_true, y_pred, title=f"{model_name}: Predicted vs. Actual"
        )
        plot_residuals(y_true, y_pred, title=f"{model_name}: Residual Plot")

        # Calculate and print metrics
        mse = mean_squared_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        print(f"{model_name} - Mean Squared Error: {mse:.4f}")
        print(f"{model_name} - R-squared: {r2:.4f}")

    except Exception as e:
        print(f"Error visualizing regression results: {e}")


def main(
    actual_values_file: str, predicted_values_file: str, model_name: str = "Regression Model"
) -> None:
    """
    Main function to load data and visualize regression results.

    Args:
        actual_values_file (str): Path to the CSV file containing actual values.
        predicted_values_file (str): Path to the CSV file containing predicted values.
        model_name (str, optional): Name of the regression model. Defaults to "Regression Model".
    """
    try:
        # Load data from CSV files
        actual_df = pd.read_csv(actual_values_file)
        predicted_df = pd.read_csv(predicted_values_file)

        # Assuming the CSVs have a single column with the values
        y_true = actual_df.iloc[:, 0].values
        y_pred = predicted_df.iloc[:, 0].values

        visualize_regression_results(y_true, y_pred, model_name=model_name)

    except FileNotFoundError:
        print("Error: One or both of the input files were not found.")
    except pd.errors.EmptyDataError:
        print("Error: One or both of the input files are empty.")
    except KeyError:
        print("Error: The specified column does not exist in the input file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visualize regression model results from CSV files."
    )
    parser.add_argument(
        "--actual",
        type=str,
        required=True,
        help="Path to the CSV file containing actual values.",
    )
    parser.add_argument(
        "--predicted",
        type=str,
        required=True,
        help="Path to the CSV file containing predicted values.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="Regression Model",
        help="Name of the regression model (optional).",
    )

    args = parser.parse_args()

    # Create dummy data files for example usage
    example_actual_data = pd.DataFrame({"actual": np.random.rand(100)})
    example_predicted_data = pd.DataFrame({"predicted": example_actual_data["actual"] + np.random.normal(0, 0.1, 100)})
    example_actual_data.to_csv("actual_values.csv", index=False)
    example_predicted_data.to_csv("predicted_values.csv", index=False)

    # Example usage with command-line arguments
    main(args.actual, args.predicted, args.model_name)
    # Clean up dummy data files
    import os
    os.remove("actual_values.csv")
    os.remove("predicted_values.csv")