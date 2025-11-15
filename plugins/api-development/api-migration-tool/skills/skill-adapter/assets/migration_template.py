#!/usr/bin/env python3

"""
Template for creating API migration scripts.

This module provides a template for creating scripts to migrate APIs
between different versions while maintaining backward compatibility.
It includes functions for loading data, transforming data, and saving data
in the new format, along with error handling and logging.
"""

import argparse
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MigrationError(Exception):
    """Custom exception for migration-related errors."""

    pass


def load_data(input_file):
    """
    Loads data from a JSON file.

    Args:
        input_file (str): Path to the input JSON file.

    Returns:
        dict: The loaded data as a dictionary.

    Raises:
        MigrationError: If the file cannot be opened or parsed.
    """
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise MigrationError(f"Input file not found: {input_file}")
    except json.JSONDecodeError:
        raise MigrationError(f"Invalid JSON format in file: {input_file}")
    except Exception as e:
        raise MigrationError(f"Error loading data from {input_file}: {e}")


def transform_data(data):
    """
    Transforms the data from the old format to the new format.

    This is where the core migration logic should be implemented.

    Args:
        data (dict): The data in the old format.

    Returns:
        dict: The data in the new format.

    Raises:
        MigrationError: If there is an error during the transformation.
    """
    try:
        # Example transformation: Add a version field
        transformed_data = data.copy()
        transformed_data["version"] = "2.0"  # Example version
        # Add your transformation logic here
        return transformed_data
    except Exception as e:
        raise MigrationError(f"Error transforming data: {e}")


def save_data(data, output_file):
    """
    Saves the transformed data to a JSON file.

    Args:
        data (dict): The transformed data.
        output_file (str): Path to the output JSON file.

    Raises:
        MigrationError: If the file cannot be written to.
    """
    try:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        raise MigrationError(f"Error saving data to {output_file}: {e}")


def migrate_api(input_file, output_file):
    """
    Migrates the API data from the old format to the new format.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output JSON file.
    """
    try:
        logging.info(f"Loading data from {input_file}...")
        data = load_data(input_file)

        logging.info("Transforming data...")
        transformed_data = transform_data(data)

        logging.info(f"Saving data to {output_file}...")
        save_data(transformed_data, output_file)

        logging.info("API migration completed successfully.")

    except MigrationError as e:
        logging.error(f"API migration failed: {e}")
        sys.exit(1)


def main():
    """
    Main function to parse arguments and run the migration.
    """
    parser = argparse.ArgumentParser(
        description="Migrate API data between versions."
    )
    parser.add_argument(
        "input_file", help="Path to the input JSON file (old format)."
    )
    parser.add_argument(
        "output_file", help="Path to the output JSON file (new format)."
    )

    args = parser.parse_args()
    migrate_api(args.input_file, args.output_file)


if __name__ == "__main__":
    # Example usage:
    # Create a dummy input file
    if not os.path.exists("input.json"):
        with open("input.json", "w") as f:
            json.dump({"name": "Example API", "version": "1.0"}, f, indent=4)

    # Run the migration
    try:
        main()
    except SystemExit:
        # Handle argparse exit (e.g., when -h is used)
        pass
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)