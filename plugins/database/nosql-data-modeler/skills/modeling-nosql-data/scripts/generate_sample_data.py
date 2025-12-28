#!/usr/bin/env python3
"""
Generates sample data based on defined schema for testing purposes.

This script creates realistic sample data documents based on a NoSQL schema,
useful for testing queries, indexes, and application logic.
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Union
from uuid import uuid4


class SampleDataGenerator:
    """Generates sample data based on schema."""

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize generator.

        Args:
            schema: Schema definition dictionary
        """
        self.schema = schema
        self.generated_data = []

    @staticmethod
    def generate_value(field_def: Dict[str, Any]) -> Any:
        """
        Generate a sample value for a field.

        Args:
            field_def: Field definition with type and constraints

        Returns:
            Generated value
        """
        field_type = field_def.get("type", "string")

        if field_type == "string":
            if "enum" in field_def:
                return random.choice(field_def["enum"])
            elif "format" in field_def:
                format_type = field_def["format"]
                if format_type == "email":
                    return f"user{random.randint(1, 1000)}@example.com"
                elif format_type == "uuid":
                    return str(uuid4())
                elif format_type == "url":
                    return f"https://example.com/{random.randint(1, 100)}"
            else:
                return f"Sample {field_def.get('description', 'value')}"

        elif field_type == "number":
            min_val = field_def.get("minimum", 0)
            max_val = field_def.get("maximum", 1000)
            return random.uniform(min_val, max_val)

        elif field_type == "integer":
            min_val = field_def.get("minimum", 0)
            max_val = field_def.get("maximum", 100)
            return random.randint(min_val, max_val)

        elif field_type == "boolean":
            return random.choice([True, False])

        elif field_type == "date":
            days_ago = random.randint(0, 365)
            return (datetime.now() - timedelta(days=days_ago)).isoformat()

        elif field_type == "array":
            min_items = field_def.get("minItems", 1)
            max_items = field_def.get("maxItems", 5)
            count = random.randint(min_items, max_items)

            if "items" in field_def:
                return [
                    SampleDataGenerator.generate_value(field_def["items"])
                    for _ in range(count)
                ]
            else:
                return [f"item{i}" for i in range(count)]

        elif field_type == "object":
            obj = {}
            if "properties" in field_def:
                for prop_name, prop_def in field_def["properties"].items():
                    obj[prop_name] = SampleDataGenerator.generate_value(prop_def)
            return obj

        else:
            return None

    def generate_document(self) -> Dict[str, Any]:
        """
        Generate a complete sample document.

        Returns:
            Sample document dictionary
        """
        document = {}

        # Handle top-level properties
        if "properties" in self.schema:
            for field_name, field_def in self.schema["properties"].items():
                required = field_name in self.schema.get("required", [])

                if required or random.random() > 0.3:  # 70% chance for optional fields
                    document[field_name] = self.generate_value(field_def)

        # Handle root-level type definitions
        for field_name, field_def in self.schema.items():
            if field_name.startswith("$") or field_name in ["type", "properties", "required"]:
                continue

            if isinstance(field_def, dict) and "type" in field_def:
                document[field_name] = self.generate_value(field_def)

        return document

    def generate_documents(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate multiple sample documents.

        Args:
            count: Number of documents to generate

        Returns:
            List of sample documents
        """
        self.generated_data = [self.generate_document() for _ in range(count)]
        return self.generated_data

    def export_json(self, filepath: str) -> bool:
        """
        Export generated data as JSON.

        Args:
            filepath: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.generated_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting JSON: {e}", file=sys.stderr)
            return False

    def export_jsonl(self, filepath: str) -> bool:
        """
        Export generated data as JSONL (JSON Lines).

        Args:
            filepath: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                for doc in self.generated_data:
                    f.write(json.dumps(doc) + '\n')
            return True
        except Exception as e:
            print(f"Error exporting JSONL: {e}", file=sys.stderr)
            return False

    def export_csv(self, filepath: str) -> bool:
        """
        Export flattened sample data as CSV.

        Args:
            filepath: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            import csv

            if not self.generated_data:
                return False

            # Flatten documents and collect all keys
            flattened = []
            all_keys = set()

            for doc in self.generated_data:
                flat = self._flatten_dict(doc)
                flattened.append(flat)
                all_keys.update(flat.keys())

            all_keys = sorted(list(all_keys))

            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_keys)
                writer.writeheader()
                writer.writerows(flattened)

            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}", file=sys.stderr)
            return False

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """
        Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nesting
            sep: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = []

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))

        return dict(items)


def load_schema(filepath: str) -> Dict[str, Any]:
    """
    Load schema from JSON file.

    Args:
        filepath: Path to schema file

    Returns:
        Schema dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for sample data generation."""
    parser = argparse.ArgumentParser(
        description="Generate sample data based on NoSQL schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 documents as JSON
  %(prog)s --schema user-schema.json --count 10

  # Generate 100 documents as JSONL
  %(prog)s --schema order-schema.json --count 100 --format jsonl

  # Export as CSV for spreadsheet analysis
  %(prog)s --schema product-schema.json --count 50 --format csv --output products.csv

  # Print to stdout
  %(prog)s --schema schema.json --count 5 --print
        """
    )

    parser.add_argument(
        "--schema",
        required=True,
        help="Path to JSON schema file"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of sample documents to generate (default: 10)"
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "jsonl", "csv"],
        help="Output format"
    )
    parser.add_argument(
        "--output",
        help="Output file path"
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print generated data to stdout"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible data"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)

    try:
        # Load schema
        if args.verbose:
            print(f"Loading schema from {args.schema}...", file=sys.stderr)

        schema = load_schema(args.schema)

        # Generate data
        if args.verbose:
            print(f"Generating {args.count} sample documents...", file=sys.stderr)

        generator = SampleDataGenerator(schema)
        generator.generate_documents(args.count)

        # Print to stdout if requested
        if args.print:
            if args.format == "jsonl":
                for doc in generator.generated_data:
                    print(json.dumps(doc))
            else:
                print(json.dumps(generator.generated_data, indent=2))

        # Export to file
        if args.output:
            if args.verbose:
                print(f"Exporting to {args.output}...", file=sys.stderr)

            if args.format == "csv":
                success = generator.export_csv(args.output)
            elif args.format == "jsonl":
                success = generator.export_jsonl(args.output)
            else:  # json
                success = generator.export_json(args.output)

            if success:
                if args.verbose:
                    print(f"✓ Generated {args.count} documents", file=sys.stderr)
                    print(f"✓ Saved to {args.output}", file=sys.stderr)
                sys.exit(0)
            else:
                sys.exit(1)
        elif not args.print:
            # If no output file and not printing, export to default location
            default_file = f"sample_data.{args.format}"
            if args.format == "csv":
                generator.export_csv(default_file)
            elif args.format == "jsonl":
                generator.export_jsonl(default_file)
            else:
                generator.export_json(default_file)

            if args.verbose:
                print(f"✓ Data saved to {default_file}", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
