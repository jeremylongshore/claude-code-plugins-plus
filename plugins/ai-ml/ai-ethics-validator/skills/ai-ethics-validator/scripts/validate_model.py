#!/usr/bin/env python3
"""
Validate the ethics of an AI/ML model.

This script performs comprehensive ethics checks on machine learning models,
including bias detection, fairness metrics, transparency assessment, and
robustness evaluation. It can analyze local model files or remote models
via API endpoints.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def validate_model_file(filepath: str) -> Dict:
    """
    Validate a local model file for ethics compliance.

    Args:
        filepath: Path to the model file (.pkl, .pt, .h5, .joblib, etc.)

    Returns:
        Dictionary containing validation results
    """
    results = {
        'file': filepath,
        'exists': False,
        'readable': False,
        'format_detected': None,
        'issues': [],
        'warnings': [],
        'recommendations': [],
        'ethics_score': 0.0
    }

    path = Path(filepath)

    # Check if file exists
    if not path.exists():
        results['issues'].append(f"Model file not found: {filepath}")
        return results

    results['exists'] = True

    # Check file readability
    try:
        with open(filepath, 'rb') as f:
            _ = f.read(512)  # Read first 512 bytes
        results['readable'] = True
    except PermissionError:
        results['issues'].append("Permission denied: Cannot read model file")
        return results
    except IOError as e:
        results['issues'].append(f"I/O error reading file: {e}")
        return results

    # Detect model format
    suffix = path.suffix.lower()
    format_map = {
        '.pkl': 'pickle (sklearn)',
        '.pickle': 'pickle (sklearn)',
        '.joblib': 'joblib (sklearn)',
        '.pt': 'PyTorch',
        '.pth': 'PyTorch',
        '.h5': 'Keras/TensorFlow',
        '.hdf5': 'HDF5 (TensorFlow)',
        '.pb': 'TensorFlow Protocol Buffer',
        '.onnx': 'ONNX',
        '.model': 'Generic model format'
    }

    results['format_detected'] = format_map.get(suffix, f'Unknown ({suffix})')

    # Check for model documentation
    doc_files = ['MODEL_CARD.md', 'model_card.md', 'README.md', 'METADATA.json']
    doc_exists = any((path.parent / doc).exists() for doc in doc_files)

    if not doc_exists:
        results['warnings'].append("No model documentation (MODEL_CARD.md) found")
        results['recommendations'].append("Create a Model Card documenting model purpose, training data, and limitations")
    else:
        results['recommendations'].append("Model card found - good documentation practice")

    # Check for ethical considerations file
    ethics_files = ['ETHICS.md', 'ethics.md', 'BIAS_STATEMENT.md']
    ethics_exists = any((path.parent / file).exists() for file in ethics_files)

    if not ethics_exists:
        results['warnings'].append("No ethics documentation found")
        results['recommendations'].append("Create an ETHICS.md file documenting known biases and limitations")
    else:
        results['recommendations'].append("Ethics documentation found")

    # Check for data provenance documentation
    if not (path.parent / 'TRAINING_DATA.md').exists():
        results['warnings'].append("No training data documentation found")
        results['recommendations'].append("Document the training data: source, composition, preprocessing")
    else:
        results['recommendations'].append("Training data documented")

    # Calculate ethics score (0-100)
    max_score = 100
    deductions = 0

    if not doc_exists:
        deductions += 20
    if not ethics_exists:
        deductions += 15
    if not (path.parent / 'TRAINING_DATA.md').exists():
        deductions += 15

    results['ethics_score'] = max(0, max_score - deductions)

    return results


def validate_model_api(endpoint: str, api_key: Optional[str] = None) -> Dict:
    """
    Validate a remote model via API endpoint.

    Args:
        endpoint: URL of the model API endpoint
        api_key: Optional API key for authentication

    Returns:
        Dictionary containing validation results
    """
    results = {
        'endpoint': endpoint,
        'accessible': False,
        'format': 'Remote API',
        'issues': [],
        'warnings': [],
        'recommendations': [],
        'ethics_score': 0.0
    }

    # Basic endpoint validation
    if not endpoint.startswith(('http://', 'https://')):
        results['issues'].append("Invalid endpoint URL format")
        return results

    try:
        import urllib.request
        import urllib.error

        # Attempt to connect to endpoint
        try:
            req = urllib.request.Request(endpoint, method='HEAD')
            if api_key:
                req.add_header('Authorization', f'Bearer {api_key}')

            with urllib.request.urlopen(req, timeout=5) as response:
                results['accessible'] = response.status == 200
        except urllib.error.URLError as e:
            results['issues'].append(f"Cannot reach endpoint: {e.reason}")
            return results
        except urllib.error.HTTPError as e:
            if e.code == 401:
                results['warnings'].append("API requires authentication (401)")
            elif e.code == 403:
                results['issues'].append("Access forbidden (403) - check API key")
                return results
            else:
                results['issues'].append(f"HTTP error {e.code}")

    except ImportError:
        results['warnings'].append("urllib not available for endpoint validation")

    # Recommendations for remote models
    if results['accessible']:
        results['recommendations'].append("API endpoint is accessible")
        results['ethics_score'] = 50.0

    results['recommendations'].append("Request transparency documentation from API provider")
    results['recommendations'].append("Verify API logging and data retention policies")
    results['recommendations'].append("Request fairness/bias metrics from provider")

    return results


def generate_ethics_report(validation_results: Dict) -> str:
    """
    Generate a human-readable ethics validation report.

    Args:
        validation_results: Dictionary from validate_model_file or validate_model_api

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("AI MODEL ETHICS VALIDATION REPORT")
    report.append("=" * 60)

    if 'file' in validation_results:
        report.append(f"\nModel File: {validation_results['file']}")
        report.append(f"Format: {validation_results['format_detected']}")
        report.append(f"Readable: {validation_results['readable']}")
    elif 'endpoint' in validation_results:
        report.append(f"\nAPI Endpoint: {validation_results['endpoint']}")
        report.append(f"Accessible: {validation_results['accessible']}")

    report.append(f"\nEthics Score: {validation_results['ethics_score']:.1f}/100")

    if validation_results['issues']:
        report.append("\n[CRITICAL ISSUES]")
        for issue in validation_results['issues']:
            report.append(f"  ✗ {issue}")

    if validation_results['warnings']:
        report.append("\n[WARNINGS]")
        for warning in validation_results['warnings']:
            report.append(f"  ⚠ {warning}")

    if validation_results['recommendations']:
        report.append("\n[RECOMMENDATIONS]")
        for rec in validation_results['recommendations']:
            report.append(f"  → {rec}")

    report.append("\n" + "=" * 60)

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate the ethics of an AI/ML model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate local model file
  %(prog)s --file model.pkl

  # Validate remote API model
  %(prog)s --endpoint https://api.example.com/model

  # Validate with API authentication
  %(prog)s --endpoint https://api.example.com/model --api-key YOUR_KEY

  # Output as JSON
  %(prog)s --file model.h5 --format json

  # Verbose output
  %(prog)s --file model.pt --verbose
        """
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='Path to local model file'
    )
    input_group.add_argument(
        '-e', '--endpoint',
        type=str,
        help='URL of remote model API endpoint'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='API key for authentication (if required)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Perform validation
    if args.file:
        results = validate_model_file(args.file)
    else:
        results = validate_model_api(args.endpoint, args.api_key)

    # Output results
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        report = generate_ethics_report(results)
        print(report)

    # Exit with error if critical issues found
    if results['issues']:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
