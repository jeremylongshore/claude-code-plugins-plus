#!/usr/bin/env python3

"""
visualization_template.py

This module provides functions for visualizing time series data and forecasts.
It includes functionalities for plotting historical data, forecasts,
confidence intervals, and residuals.

Example:
    To use this module, import it and call the desired visualization functions.
    For example:

    >>> import visualization_template as vt
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> # Assume 'data' is a pandas DataFrame with a 'time' column and a 'value' column
    >>> # Assume 'forecast' is a pandas DataFrame with a 'time' column and a 'forecast' column
    >>> vt.plot_time_series(data, forecast, title="Time Series Forecast")
    >>> plt.show()
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from typing import Optional, Tuple, List


def plot_time_series(
    data: pd.DataFrame,
    forecast: Optional[pd.DataFrame] = None,
    confidence_interval: Optional[Tuple[float, float]] = None,
    title: str = "Time Series Data and Forecast",
    xlabel: str = "Time",
    ylabel: str = "Value",
    figsize: Tuple[int, int] = (12, 6),
    data_color: str = 'blue',
    forecast_color: str = 'red',
    confidence_color: str = 'lightgray'
) -> None:
    """
    Plots the time series data and, optionally, a forecast with confidence intervals.

    Args:
        data (pd.DataFrame): DataFrame containing the time series data.
                              Must have a column named 'time' and a column with the time series values.
        forecast (pd.DataFrame, optional): DataFrame containing the forecast. Defaults to None.
                                          Must have a column named 'time' and a column with the forecast values (e.g., 'forecast').
        confidence_interval (Tuple[float, float], optional): Tuple containing the lower and upper bounds of the confidence interval. Defaults to None.
                                                            If provided, `forecast` DataFrame must have columns for lower and upper bounds (e.g., 'lower', 'upper').
        title (str, optional): Title of the plot. Defaults to "Time Series Data and Forecast".
        xlabel (str, optional): Label for the x-axis. Defaults to "Time".
        ylabel (str, optional): Label for the y-axis. Defaults to "Value".
        figsize (Tuple[int, int], optional): Figure size (width, height). Defaults to (12, 6).
        data_color (str, optional): Color of the historical data line. Defaults to 'blue'.
        forecast_color (str, optional): Color of the forecast line. Defaults to 'red'.
        confidence_color (str, optional): Color of the confidence interval shading. Defaults to 'lightgray'.

    Raises:
        ValueError: If `data` does not have a 'time' column.
        ValueError: If `data` does not have a column with the time series values.
        ValueError: If `forecast` is provided but does not have a 'time' column.
        ValueError: If `forecast` is provided but does not have a column with the forecast values.
        ValueError: If `confidence_interval` is provided but `forecast` does not have 'lower' and 'upper' columns.
    """

    if 'time' not in data.columns:
        raise ValueError("Data DataFrame must have a 'time' column.")

    value_column = next((col for col in data.columns if col != 'time'), None)
    if value_column is None:
        raise ValueError("Data DataFrame must have a column with the time series values.")

    plt.figure(figsize=figsize)
    plt.plot(data['time'], data[value_column], label="Historical Data", color=data_color)

    if forecast is not None:
        if 'time' not in forecast.columns:
            raise ValueError("Forecast DataFrame must have a 'time' column.")
        forecast_column = next((col for col in forecast.columns if col != 'time'), None)
        if forecast_column is None:
            raise ValueError("Forecast DataFrame must have a column with the forecast values.")

        plt.plot(forecast['time'], forecast[forecast_column], label="Forecast", color=forecast_color)

        if confidence_interval is not None:
            if 'lower' not in forecast.columns or 'upper' not in forecast.columns:
                raise ValueError("Forecast DataFrame must have 'lower' and 'upper' columns for confidence intervals.")
            plt.fill_between(forecast['time'], forecast['lower'], forecast['upper'], color=confidence_color, alpha=0.5, label="Confidence Interval")

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()


def plot_residuals(
    residuals: pd.Series,
    title: str = "Residual Plot",
    xlabel: str = "Time",
    ylabel: str = "Residuals",
    figsize: Tuple[int, int] = (12, 6)
) -> None:
    """
    Plots the residuals of a time series forecast.

    Args:
        residuals (pd.Series): Pandas Series containing the residuals.
        title (str, optional): Title of the plot. Defaults to "Residual Plot".
        xlabel (str, optional): Label for the x-axis. Defaults to "Time".
        ylabel (str, optional): Label for the y-axis. Defaults to "Residuals".
        figsize (Tuple[int, int], optional): Figure size (width, height). Defaults to (12, 6).

    Raises:
        TypeError: If `residuals` is not a pandas Series.
    """

    if not isinstance(residuals, pd.Series):
        raise TypeError("Residuals must be a pandas Series.")

    plt.figure(figsize=figsize)
    plt.plot(residuals.index, residuals.values, marker='o', linestyle='-', label="Residuals")
    plt.axhline(y=0, color='r', linestyle='--', label="Zero Line")  # Add a horizontal line at y=0
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()


def plot_acf(
    data: pd.Series,
    lags: int = 40,
    title: str = "Autocorrelation Function (ACF)",
    figsize: Tuple[int, int] = (12, 6)
) -> None:
    """
    Plots the Autocorrelation Function (ACF) of a time series.

    Args:
        data (pd.Series): Pandas Series containing the time series data.
        lags (int, optional): Number of lags to plot. Defaults to 40.
        title (str, optional): Title of the plot. Defaults to "Autocorrelation Function (ACF)".
        figsize (Tuple[int, int], optional): Figure size (width, height). Defaults to (12, 6).

    Raises:
        TypeError: If `data` is not a pandas Series.
        ValueError: If `lags` is not a positive integer.
    """
    from statsmodels.graphics.tsaplots import plot_acf as sm_plot_acf

    if not isinstance(data, pd.Series):
        raise TypeError("Data must be a pandas Series.")
    if not isinstance(lags, int) or lags <= 0:
        raise ValueError("Lags must be a positive integer.")

    fig, ax = plt.subplots(figsize=figsize)
    sm_plot_acf(data, lags=lags, ax=ax, title=title)
    plt.tight_layout()


def plot_pacf(
    data: pd.Series,
    lags: int = 40,
    title: str = "Partial Autocorrelation Function (PACF)",
    figsize: Tuple[int, int] = (12, 6)
) -> None:
    """
    Plots the Partial Autocorrelation Function (PACF) of a time series.

    Args:
        data (pd.Series): Pandas Series containing the time series data.
        lags (int, optional): Number of lags to plot. Defaults to 40.
        title (str, optional): Title of the plot. Defaults to "Partial Autocorrelation Function (PACF)".
        figsize (Tuple[int, int], optional): Figure size (width, height). Defaults to (12, 6).

    Raises:
        TypeError: If `data` is not a pandas Series.
        ValueError: If `lags` is not a positive integer.
    """
    from statsmodels.graphics.tsaplots import plot_pacf as sm_plot_pacf

    if not isinstance(data, pd.Series):
        raise TypeError("Data must be a pandas Series.")
    if not isinstance(lags, int) or lags <= 0:
        raise ValueError("Lags must be a positive integer.")

    fig, ax = plt.subplots(figsize=figsize)
    sm_plot_pacf(data, lags=lags, ax=ax, title=title)
    plt.tight_layout()


if __name__ == '__main__':
    # Example Usage
    try:
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        values = np.random.randn(100).cumsum()
        data = pd.DataFrame({'time': dates, 'value': values})

        # Create sample forecast
        forecast_dates = pd.date_range(start='2023-04-11', periods=30, freq='D')
        forecast_values = np.random.randn(30).cumsum() + values[-1]
        lower_bound = forecast_values - np.abs(np.random.randn(30).cumsum())
        upper_bound = forecast_values + np.abs(np.random.randn(30).cumsum())
        forecast = pd.DataFrame({'time': forecast_dates, 'forecast': forecast_values, 'lower': lower_bound, 'upper': upper_bound})

        # Plot time series and forecast
        plot_time_series(data, forecast, confidence_interval=(0.05, 0.95), title="Example Time Series Forecast")
        plt.show()

        # Create sample residuals
        residuals = pd.Series(np.random.randn(100), index=dates)

        # Plot residuals
        plot_residuals(residuals, title="Example Residual Plot")
        plt.show()

        # Plot ACF
        plot_acf(data['value'], lags=20, title="Example ACF Plot")
        plt.show()

        # Plot PACF
        plot_pacf(data['value'], lags=20, title="Example PACF Plot")
        plt.show()

    except ValueError as e:
        print(f"ValueError: {e}")
    except TypeError as e:
        print(f"TypeError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")