#!/usr/bin/env python3
"""
Data preprocessing pipeline orchestrator.

Orchestrates the entire data preprocessing pipeline including:
- Data loading and validation
- Data transformation
- Error handling and recovery
- Pipeline execution and monitoring
- Report generation
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import subprocess


class PreprocessingPipeline:
    """Orchestrates data preprocessing pipeline."""

    def __init__(self, config_file: Optional[str] = None, verbose: bool = False):
        """
        Initialize pipeline.

        Args:
            config_file: Path to configuration file (JSON)
            verbose: Enable verbose output
        """
        self.config = {}
        self.verbose = verbose
        self.steps = []
        self.execution_log = []
        self.start_time = None
        self.end_time = None

        if config_file:
            self._load_config(config_file)

    def _load_config(self, config_file: str) -> None:
        """Load pipeline configuration."""
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            if self.verbose:
                print(f"Loaded configuration from {config_file}")
        except Exception as e:
            raise IOError(f"Failed to load config: {str(e)}")

    def _run_step(self, step_name: str, command: List[str]) -> bool:
        """
        Run a pipeline step.

        Args:
            step_name: Name of the step
            command: Command to execute

        Returns:
            True if successful, False otherwise
        """
        step_log = {
            'name': step_name,
            'timestamp': datetime.now().isoformat(),
            'command': ' '.join(command),
            'status': 'pending',
            'duration': 0,
        }

        start = datetime.now()
        try:
            if self.verbose:
                print(f"\nExecuting: {step_name}")
                print(f"Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )

            duration = (datetime.now() - start).total_seconds()
            step_log['duration'] = duration
            step_log['returncode'] = result.returncode

            if result.returncode == 0:
                step_log['status'] = 'success'
                if self.verbose and result.stdout:
                    print(f"Output: {result.stdout}")
            else:
                step_log['status'] = 'failed'
                step_log['stderr'] = result.stderr
                if self.verbose:
                    print(f"Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            step_log['status'] = 'timeout'
            step_log['error'] = "Step execution timed out"
        except Exception as e:
            step_log['status'] = 'error'
            step_log['error'] = str(e)
            if self.verbose:
                print(f"Exception: {str(e)}")

        self.execution_log.append(step_log)
        return step_log['status'] == 'success'

    def add_validation_step(
        self,
        data_file: str,
        schema_file: Optional[str] = None
    ) -> None:
        """
        Add data validation step.

        Args:
            data_file: Path to data file
            schema_file: Path to schema file (optional)
        """
        command = ['python3', 'validate_data.py', data_file]
        if schema_file:
            command.extend(['-s', schema_file])

        self.steps.append({
            'name': 'validate_data',
            'command': command,
            'data_file': data_file,
            'schema_file': schema_file,
        })

    def add_transformation_step(
        self,
        input_file: str,
        output_file: str,
        transformations: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add data transformation step.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            transformations: Transformation configuration
        """
        command = ['python3', 'transform_data.py', input_file, '-o', output_file]

        if transformations:
            if 'normalize' in transformations:
                for field, method in transformations['normalize']:
                    command.extend(['-n', field, method])

            if 'encode' in transformations:
                for field, method in transformations['encode']:
                    command.extend(['-e', field, method])

            if 'impute' in transformations:
                for field, method in transformations['impute']:
                    command.extend(['-i', field, method])

        self.steps.append({
            'name': 'transform_data',
            'command': command,
            'input_file': input_file,
            'output_file': output_file,
            'transformations': transformations or {},
        })

    def add_error_handling_step(
        self,
        data_file: str,
        log_file: str,
        report_file: str
    ) -> None:
        """
        Add error handling step.

        Args:
            data_file: Path to data file for integrity check
            log_file: Path to error log file
            report_file: Path to error report file
        """
        command = [
            'python3', 'handle_errors.py', 'analyze',
            '-d', data_file,
            '-l', log_file,
            '-o', report_file,
        ]

        self.steps.append({
            'name': 'error_handling',
            'command': command,
            'data_file': data_file,
            'log_file': log_file,
            'report_file': report_file,
        })

    def execute(self, stop_on_error: bool = False) -> bool:
        """
        Execute pipeline.

        Args:
            stop_on_error: Stop execution on first error

        Returns:
            True if all steps successful, False otherwise
        """
        self.start_time = datetime.now()

        if self.verbose:
            print("\n" + "=" * 60)
            print("DATA PREPROCESSING PIPELINE")
            print("=" * 60)
            print(f"Total steps: {len(self.steps)}")

        all_successful = True

        for idx, step in enumerate(self.steps, 1):
            if self.verbose:
                print(f"\n[{idx}/{len(self.steps)}] {step['name']}")

            success = self._run_step(step['name'], step['command'])

            if not success:
                all_successful = False
                if stop_on_error:
                    if self.verbose:
                        print(f"Pipeline aborted due to failure in {step['name']}")
                    break

        self.end_time = datetime.now()

        return all_successful

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        total_duration = 0
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()

        successful_steps = sum(1 for log in self.execution_log if log['status'] == 'success')
        failed_steps = sum(1 for log in self.execution_log if log['status'] in ('failed', 'error', 'timeout'))

        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': total_duration,
            'total_steps': len(self.steps),
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'execution_log': self.execution_log,
        }

    def save_report(self, output_file: str) -> None:
        """
        Save pipeline execution report.

        Args:
            output_file: Output file path
        """
        try:
            report = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'pipeline_config': self.config,
                },
                'summary': self.get_summary(),
            }

            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            if self.verbose:
                print(f"\nReport saved to: {output_file}")

        except Exception as e:
            print(f"Failed to save report: {str(e)}", file=sys.stderr)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Orchestrate data preprocessing pipeline'
    )
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file (JSON)',
        default=None
    )
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to input data file'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to output data file'
    )
    parser.add_argument(
        '-s', '--schema',
        help='Path to schema file for validation'
    )
    parser.add_argument(
        '-n', '--normalize',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Normalize field'
    )
    parser.add_argument(
        '-e', '--encode',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Encode categorical field'
    )
    parser.add_argument(
        '-i-impute', '--impute',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Impute missing values'
    )
    parser.add_argument(
        '--report',
        help='Save pipeline report to file'
    )
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop pipeline on first error'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed execution information'
    )

    args = parser.parse_args()

    try:
        # Create pipeline
        pipeline = PreprocessingPipeline(config_file=args.config, verbose=args.verbose)

        # Add validation step
        pipeline.add_validation_step(args.input, schema_file=args.schema)

        # Add transformation step
        transformations = {}
        if args.normalize:
            transformations['normalize'] = args.normalize
        if args.encode:
            transformations['encode'] = args.encode
        if args.impute:
            transformations['impute'] = args.impute

        pipeline.add_transformation_step(args.input, args.output, transformations)

        # Add error handling step
        log_file = args.output.replace('.', '_errors.')
        report_file = args.output.replace('.', '_report.')
        pipeline.add_error_handling_step(args.output, log_file, report_file)

        # Execute pipeline
        success = pipeline.execute(stop_on_error=args.stop_on_error)

        # Save report if requested
        if args.report:
            pipeline.save_report(args.report)

        # Print summary
        summary = pipeline.get_summary()
        if args.verbose:
            print("\n" + "=" * 60)
            print("PIPELINE SUMMARY")
            print("=" * 60)
            print(f"Duration: {summary['total_duration']:.2f} seconds")
            print(f"Successful: {summary['successful_steps']}/{summary['total_steps']}")
            print(f"Failed: {summary['failed_steps']}/{summary['total_steps']}")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
