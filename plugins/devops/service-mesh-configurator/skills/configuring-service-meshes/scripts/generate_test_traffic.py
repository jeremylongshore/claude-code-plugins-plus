#!/usr/bin/env python3
"""
Test traffic generator for service mesh verification.

Generates test traffic to verify service mesh configuration including:
- HTTP requests to services
- Traffic distribution verification
- Load balancing testing
- Failure injection testing
- Latency measurement
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import subprocess
import time
import random
from datetime import datetime


class TestTrafficGenerator:
    """Generates test traffic for service mesh verification."""

    KUBECTL_CMD = 'kubectl'

    def __init__(self, namespace: str = 'default', context: str = ''):
        """
        Initialize traffic generator.

        Args:
            namespace: Kubernetes namespace
            context: Kubernetes context
        """
        self.namespace = namespace
        self.context = context
        self.results = []
        self.metrics = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'avg_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0,
        }

    def _run_kubectl(self, command: List[str]) -> Tuple[bool, str, str]:
        """
        Run kubectl command.

        Args:
            command: Kubectl command parts

        Returns:
            Tuple of (success, stdout, stderr)
        """
        cmd = [self.KUBECTL_CMD]

        if self.context:
            cmd.extend(['--context', self.context])

        cmd.extend(['-n', self.namespace])
        cmd.extend(command)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, '', 'Command timeout'
        except Exception as e:
            return False, '', str(e)

    def get_services(self) -> List[Dict[str, str]]:
        """
        Get list of services in namespace.

        Returns:
            List of service information
        """
        success, stdout, _ = self._run_kubectl(['get', 'svc', '-o', 'json'])

        if not success:
            return []

        try:
            data = json.loads(stdout)
            services = []
            for item in data.get('items', []):
                metadata = item.get('metadata', {})
                spec = item.get('spec', {})
                services.append({
                    'name': metadata.get('name'),
                    'namespace': metadata.get('namespace'),
                    'type': spec.get('type'),
                    'cluster_ip': spec.get('clusterIP'),
                    'ports': [p.get('port') for p in spec.get('ports', [])],
                })
            return services
        except json.JSONDecodeError:
            return []

    def generate_http_traffic(
        self,
        service_url: str,
        num_requests: int = 10,
        concurrency: int = 1,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Generate HTTP traffic to service.

        Args:
            service_url: URL of service
            num_requests: Number of requests
            concurrency: Concurrent requests
            timeout: Request timeout in seconds

        Returns:
            Traffic generation results
        """
        results = {
            'service_url': service_url,
            'num_requests': num_requests,
            'concurrency': concurrency,
            'requests': [],
            'summary': {},
        }

        latencies = []
        success_count = 0
        failed_count = 0

        # Try to use curl via kubectl exec or direct access
        for i in range(num_requests):
            request_result = {
                'request_num': i + 1,
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'latency_ms': None,
                'success': False,
                'error': None,
            }

            try:
                start_time = time.time()

                # Try using curl
                cmd = [
                    'run', 'traffic-test', '--rm', '-i', '--image=curlimages/curl',
                    '--restart=Never', '--',
                    'curl', '-s', '-w', '%{http_code}\\n', '-m', str(timeout),
                    service_url
                ]

                success, stdout, stderr = self._run_kubectl(cmd)
                latency_ms = (time.time() - start_time) * 1000

                if success and stdout:
                    # Parse response
                    lines = stdout.strip().split('\n')
                    if lines:
                        try:
                            status_code = int(lines[-1])
                            request_result['status_code'] = status_code
                            request_result['latency_ms'] = round(latency_ms, 2)
                            request_result['success'] = 200 <= status_code < 300
                        except ValueError:
                            request_result['error'] = 'Invalid status code'
                else:
                    request_result['error'] = stderr or 'Connection failed'

            except Exception as e:
                request_result['error'] = str(e)

            # Update metrics
            if request_result['success']:
                success_count += 1
                if request_result['latency_ms']:
                    latencies.append(request_result['latency_ms'])
            else:
                failed_count += 1

            results['requests'].append(request_result)

            # Respect concurrency
            if (i + 1) % concurrency == 0:
                time.sleep(0.1)

        # Calculate summary
        results['summary'] = {
            'total_requests': num_requests,
            'successful': success_count,
            'failed': failed_count,
            'success_rate': round((success_count / num_requests * 100) if num_requests > 0 else 0, 2),
        }

        if latencies:
            results['summary']['avg_latency_ms'] = round(sum(latencies) / len(latencies), 2)
            results['summary']['min_latency_ms'] = round(min(latencies), 2)
            results['summary']['max_latency_ms'] = round(max(latencies), 2)

        self.results.append(results)
        return results

    def test_service_connectivity(self, service_name: str) -> Dict[str, Any]:
        """
        Test connectivity to service.

        Args:
            service_name: Name of service

        Returns:
            Connectivity test results
        """
        result = {
            'service': service_name,
            'namespace': self.namespace,
            'timestamp': datetime.now().isoformat(),
            'tests': {},
        }

        # Get service info
        success, stdout, _ = self._run_kubectl(['get', 'svc', service_name, '-o', 'json'])

        if not success:
            result['error'] = f"Service not found: {service_name}"
            return result

        try:
            svc_data = json.loads(stdout)
            cluster_ip = svc_data.get('spec', {}).get('clusterIP')
            ports = svc_data.get('spec', {}).get('ports', [])

            # Test DNS resolution
            result['tests']['dns_resolution'] = self._test_dns(service_name)

            # Test connectivity to each port
            for port_info in ports:
                port = port_info.get('port')
                if cluster_ip and port:
                    url = f"http://{cluster_ip}:{port}/"
                    result['tests'][f'port_{port}'] = self.generate_http_traffic(url, num_requests=3)

        except json.JSONDecodeError:
            result['error'] = 'Failed to parse service info'

        return result

    def _test_dns(self, service_name: str) -> Dict[str, Any]:
        """Test DNS resolution."""
        fqdn = f"{service_name}.{self.namespace}.svc.cluster.local"
        cmd = ['run', 'dns-test', '--rm', '-i', '--image=busybox',
               '--restart=Never', '--', 'nslookup', fqdn]

        success, stdout, stderr = self._run_kubectl(cmd)

        return {
            'fqdn': fqdn,
            'resolvable': success,
            'response': stdout if success else stderr,
        }

    def generate_traffic_pattern(
        self,
        service_name: str,
        pattern: str = 'constant',
        duration: int = 60,
        rate: int = 10
    ) -> Dict[str, Any]:
        """
        Generate specific traffic pattern.

        Args:
            service_name: Target service name
            pattern: Traffic pattern (constant, spike, wave, random)
            duration: Duration in seconds
            rate: Base request rate per second

        Returns:
            Pattern generation results
        """
        result = {
            'service': service_name,
            'pattern': pattern,
            'duration': duration,
            'base_rate': rate,
            'start_time': datetime.now().isoformat(),
            'requests_sent': 0,
        }

        # Get service URL
        services = self.get_services()
        service = next((s for s in services if s['name'] == service_name), None)

        if not service:
            result['error'] = f"Service not found: {service_name}"
            return result

        # Build URL
        if service['ports']:
            url = f"http://{service['cluster_ip']}:{service['ports'][0]}/"
        else:
            result['error'] = 'Service has no ports'
            return result

        # Generate traffic according to pattern
        start_time = time.time()
        requests_sent = 0

        while time.time() - start_time < duration:
            # Calculate request rate based on pattern
            if pattern == 'constant':
                current_rate = rate
            elif pattern == 'spike':
                elapsed = time.time() - start_time
                # Spike every 15 seconds
                if int(elapsed) % 15 < 5:
                    current_rate = rate * 5
                else:
                    current_rate = rate
            elif pattern == 'wave':
                elapsed = time.time() - start_time
                # Sinusoidal wave
                import math
                current_rate = int(rate + rate * math.sin(elapsed / 10))
            elif pattern == 'random':
                current_rate = random.randint(rate // 2, rate * 2)
            else:
                current_rate = rate

            # Send requests
            interval = 1.0 / current_rate if current_rate > 0 else 1
            self.generate_http_traffic(url, num_requests=1, timeout=5)
            requests_sent += 1

            time.sleep(interval)

        result['end_time'] = datetime.now().isoformat()
        result['requests_sent'] = requests_sent

        return result

    def get_report(self) -> Dict[str, Any]:
        """Get test traffic report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'namespace': self.namespace,
            'results': self.results,
            'summary': self._calculate_summary(),
        }

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        summary = {
            'total_tests': len(self.results),
            'total_requests': 0,
            'total_success': 0,
            'total_failed': 0,
        }

        latencies = []

        for result in self.results:
            if 'summary' in result:
                summary['total_requests'] += result['summary'].get('total_requests', 0)
                summary['total_success'] += result['summary'].get('successful', 0)
                summary['total_failed'] += result['summary'].get('failed', 0)

                if 'avg_latency_ms' in result['summary']:
                    latencies.append(result['summary']['avg_latency_ms'])

        if summary['total_requests'] > 0:
            summary['overall_success_rate'] = round(
                (summary['total_success'] / summary['total_requests']) * 100, 2
            )

        if latencies:
            summary['avg_latency_ms'] = round(sum(latencies) / len(latencies), 2)

        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate test traffic to verify service mesh configuration'
    )
    parser.add_argument(
        '-n', '--namespace',
        default='default',
        help='Kubernetes namespace'
    )
    parser.add_argument(
        '-c', '--context',
        help='Kubernetes context'
    )
    parser.add_argument(
        '--service',
        help='Specific service to test'
    )
    parser.add_argument(
        '--url',
        help='Specific URL to test (for debugging)'
    )
    parser.add_argument(
        '-r', '--requests',
        type=int,
        default=10,
        help='Number of requests per test'
    )
    parser.add_argument(
        '--pattern',
        choices=['constant', 'spike', 'wave', 'random'],
        default='constant',
        help='Traffic pattern'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=60,
        help='Duration for pattern generation (seconds)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Save report to JSON file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed output'
    )

    args = parser.parse_args()

    try:
        generator = TestTrafficGenerator(namespace=args.namespace, context=args.context or '')

        if args.url:
            # Test specific URL
            result = generator.generate_http_traffic(args.url, num_requests=args.requests)
            if args.verbose:
                print(json.dumps(result, indent=2))

        elif args.service:
            # Test specific service
            result = generator.test_service_connectivity(args.service)
            if args.verbose:
                print(json.dumps(result, indent=2))

        else:
            # Test all services
            services = generator.get_services()
            for service in services:
                generator.test_service_connectivity(service['name'])
                if args.verbose:
                    print(f"Tested service: {service['name']}")

        # Generate report
        report = generator.get_report()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")

        print(json.dumps(report['summary'], indent=2))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
