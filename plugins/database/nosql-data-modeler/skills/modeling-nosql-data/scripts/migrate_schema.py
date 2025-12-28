#!/usr/bin/env python3
"""
Migrates schema from one NoSQL database type to another.

This script converts schema definitions between different NoSQL database formats
(MongoDB, DynamoDB, Firebase, Firestore, etc.) while preserving semantics.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class SchemaTransformer:
    """Transforms schemas between NoSQL database types."""

    # Database schema patterns
    DB_PATTERNS = {
        "mongodb": {
            "name": "MongoDB",
            "root": "properties",
            "type_mapping": {
                "string": "string",
                "number": "double",
                "integer": "int",
                "boolean": "boolean",
                "date": "date",
                "object": "object",
                "array": "array",
                "null": "null"
            }
        },
        "dynamodb": {
            "name": "DynamoDB",
            "root": "AttributeDefinitions",
            "type_mapping": {
                "string": "S",
                "number": "N",
                "integer": "N",
                "boolean": "BOOL",
                "date": "S",
                "object": "M",
                "array": "L",
                "binary": "B"
            }
        },
        "firestore": {
            "name": "Firestore",
            "root": "fields",
            "type_mapping": {
                "string": "stringValue",
                "number": "doubleValue",
                "integer": "integerValue",
                "boolean": "booleanValue",
                "date": "timestampValue",
                "object": "mapValue",
                "array": "arrayValue",
                "null": "nullValue"
            }
        },
        "cosmosdb": {
            "name": "Azure Cosmos DB",
            "root": "properties",
            "type_mapping": {
                "string": "string",
                "number": "number",
                "integer": "integer",
                "boolean": "boolean",
                "date": "date",
                "object": "object",
                "array": "array"
            }
        }
    }

    def __init__(self, source_type: str, target_type: str):
        """
        Initialize transformer.

        Args:
            source_type: Source database type
            target_type: Target database type

        Raises:
            ValueError: If database types are not supported
        """
        if source_type not in self.DB_PATTERNS:
            raise ValueError(f"Unsupported source type: {source_type}")
        if target_type not in self.DB_PATTERNS:
            raise ValueError(f"Unsupported target type: {target_type}")

        self.source_type = source_type
        self.target_type = target_type
        self.warnings = []

    def transform(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform schema from source to target format.

        Args:
            schema: Schema in source format

        Returns:
            Schema in target format
        """
        self.warnings = []

        # Parse source schema
        parsed = self._parse_source_schema(schema)

        # Transform to target format
        transformed = self._transform_to_target(parsed)

        return transformed

    def _parse_source_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse source schema into normalized format.

        Args:
            schema: Source schema

        Returns:
            Normalized schema representation
        """
        parsed = {
            "name": schema.get("$id", schema.get("title", "Schema")),
            "description": schema.get("description", ""),
            "fields": {}
        }

        # Extract fields based on source type
        if self.source_type == "mongodb":
            if "properties" in schema:
                parsed["fields"] = self._extract_mongodb_fields(schema["properties"])

        elif self.source_type == "dynamodb":
            parsed["fields"] = self._extract_dynamodb_fields(schema)

        elif self.source_type == "firestore":
            parsed["fields"] = self._extract_firestore_fields(schema)

        elif self.source_type == "cosmosdb":
            if "properties" in schema:
                parsed["fields"] = self._extract_mongodb_fields(schema["properties"])

        return parsed

    def _extract_mongodb_fields(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from MongoDB schema."""
        fields = {}

        for field_name, field_def in properties.items():
            fields[field_name] = {
                "type": field_def.get("type", "string"),
                "description": field_def.get("description", ""),
                "required": "required" in str(field_def),
                "indexed": field_def.get("indexed", False)
            }

        return fields

    def _extract_dynamodb_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from DynamoDB schema."""
        fields = {}

        # DynamoDB representation varies; handle common patterns
        if "AttributeDefinitions" in schema:
            for attr in schema["AttributeDefinitions"]:
                fields[attr["AttributeName"]] = {
                    "type": self._map_dynamodb_type(attr["AttributeType"]),
                    "required": attr["AttributeName"] in schema.get("KeySchema", [])
                }

        return fields

    def _extract_firestore_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from Firestore schema."""
        fields = {}

        if "fields" in schema:
            for field_name, field_def in schema["fields"].items():
                field_type = self._extract_firestore_type(field_def)
                fields[field_name] = {
                    "type": field_type,
                    "indexed": field_def.get("indexed", False)
                }

        return fields

    def _transform_to_target(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Transform parsed schema to target format."""
        if self.target_type == "mongodb":
            return self._transform_to_mongodb(parsed)
        elif self.target_type == "dynamodb":
            return self._transform_to_dynamodb(parsed)
        elif self.target_type == "firestore":
            return self._transform_to_firestore(parsed)
        elif self.target_type == "cosmosdb":
            return self._transform_to_cosmosdb(parsed)

        return parsed

    def _transform_to_mongodb(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to MongoDB schema format."""
        properties = {}

        for field_name, field_info in parsed["fields"].items():
            properties[field_name] = {
                "type": field_info.get("type", "string"),
                "description": field_info.get("description", "")
            }

            if field_info.get("indexed"):
                properties[field_name]["indexed"] = True

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": parsed["name"],
            "title": parsed["name"],
            "type": "object",
            "properties": properties
        }

        return schema

    def _transform_to_dynamodb(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to DynamoDB schema format."""
        attributes = []

        for field_name, field_info in parsed["fields"].items():
            field_type = field_info.get("type", "string")
            dynamo_type = self._map_type_to_dynamodb(field_type)

            attributes.append({
                "AttributeName": field_name,
                "AttributeType": dynamo_type
            })

        schema = {
            "TableName": parsed["name"],
            "AttributeDefinitions": attributes,
            "KeySchema": [
                {"AttributeName": "id", "KeyType": "HASH"}
            ],
            "BillingMode": "PAY_PER_REQUEST"
        }

        return schema

    def _transform_to_firestore(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Firestore schema format."""
        fields = {}

        for field_name, field_info in parsed["fields"].items():
            field_type = field_info.get("type", "string")

            fields[field_name] = {
                field_type + "Value": self._get_firestore_default(field_type)
            }

            if field_info.get("indexed"):
                fields[field_name]["indexed"] = True

        schema = {
            "name": f"projects/PROJECT_ID/databases/(default)/documents/{parsed['name']}",
            "fields": fields
        }

        return schema

    def _transform_to_cosmosdb(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Cosmos DB schema format (similar to MongoDB)."""
        return self._transform_to_mongodb(parsed)

    def _map_type_to_dynamodb(self, source_type: str) -> str:
        """Map source type to DynamoDB type."""
        type_map = {
            "string": "S",
            "number": "N",
            "integer": "N",
            "boolean": "BOOL",
            "date": "S",
            "object": "M",
            "array": "L"
        }
        return type_map.get(source_type, "S")

    def _map_dynamodb_type(self, dynamo_type: str) -> str:
        """Map DynamoDB type to normalized type."""
        type_map = {
            "S": "string",
            "N": "number",
            "B": "binary",
            "SS": "string",
            "NS": "number",
            "BS": "binary",
            "M": "object",
            "L": "array",
            "BOOL": "boolean"
        }
        return type_map.get(dynamo_type, "string")

    def _extract_firestore_type(self, field_def: Dict) -> str:
        """Extract type from Firestore field definition."""
        for key in field_def:
            if key.endswith("Value"):
                type_name = key.replace("Value", "")
                type_map = {
                    "string": "string",
                    "double": "number",
                    "integer": "integer",
                    "boolean": "boolean",
                    "timestamp": "date",
                    "map": "object",
                    "array": "array"
                }
                return type_map.get(type_name, "string")

        return "string"

    def _get_firestore_default(self, field_type: str) -> Any:
        """Get default value for Firestore field type."""
        defaults = {
            "string": "",
            "number": 0,
            "integer": 0,
            "boolean": False,
            "date": "",
            "object": {},
            "array": []
        }
        return defaults.get(field_type)


def load_schema(filepath: str) -> Dict[str, Any]:
    """Load schema from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def get_supported_databases() -> List[str]:
    """Get list of supported database types."""
    return list(SchemaTransformer.DB_PATTERNS.keys())


def main():
    """Main entry point for schema migration."""
    parser = argparse.ArgumentParser(
        description="Migrate NoSQL schema between database types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported database types: {', '.join(get_supported_databases())}

Examples:
  # MongoDB to DynamoDB
  %(prog)s --from mongodb --to dynamodb --schema user.json

  # DynamoDB to Firestore
  %(prog)s --from dynamodb --to firestore --schema product.json --output firestore-schema.json

  # Firestore to MongoDB
  %(prog)s --from firestore --to mongodb --schema order.json

  # List supported types
  %(prog)s --list-types
        """
    )

    parser.add_argument(
        "--from",
        dest="source_type",
        help="Source database type"
    )
    parser.add_argument(
        "--to",
        dest="target_type",
        help="Target database type"
    )
    parser.add_argument(
        "--schema",
        help="Path to source schema file"
    )
    parser.add_argument(
        "--output",
        help="Output file for migrated schema"
    )
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List supported database types"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    if args.list_types:
        print("Supported database types:")
        for db_type, info in SchemaTransformer.DB_PATTERNS.items():
            print(f"  - {db_type}: {info['name']}")
        sys.exit(0)

    # Validate required arguments
    if not args.source_type or not args.target_type or not args.schema:
        parser.error("--from, --to, and --schema are required")

    try:
        if args.verbose:
            print(f"Migrating schema from {args.source_type} to {args.target_type}...", file=sys.stderr)

        # Load source schema
        schema = load_schema(args.schema)

        # Create transformer
        transformer = SchemaTransformer(args.source_type, args.target_type)

        # Transform schema
        migrated = transformer.transform(schema)

        # Output
        output_json = json.dumps(migrated, indent=2)
        print(output_json)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)

            if args.verbose:
                print(f"✓ Schema migrated successfully", file=sys.stderr)
                print(f"✓ Saved to {args.output}", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
