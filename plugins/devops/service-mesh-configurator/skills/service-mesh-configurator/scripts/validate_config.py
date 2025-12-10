#!/usr/bin/env python3
"""
Service mesh configuration validator.

Validates service mesh configuration against best practices including:
- Kubernetes manifest syntax
- Istio/Linkerd resource definitions
- Traffic policies and rules
- Security policies
- Common misconfigurations
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import yaml


class ServiceMeshValidator:
    """Validates service mesh configurations."""

    SUPPORTED_MESHES = ['istio', 'linkerd', 'consul', 'osm']

    ISTIO_RESOURCES = {
        'VirtualService', 'DestinationRule', 'Gateway', 'ServiceEntry',
        'RequestAuthentication', 'AuthorizationPolicy', 'Sidecar',
        'PeerAuthentication', 'Telemetry'
    }

    LINKERD_RESOURCES = {
        'TrafficPolicy', 'ServiceProfile', 'AuthorizationPolicy',
        'ExternalWorkload', 'Server'
    }

    def __init__(self, mesh_type: str = 'istio'):
        """
        Initialize validator.

        Args:
            mesh_type: Type of service mesh
        """
        if mesh_type not in self.SUPPORTED_MESHES:
            raise ValueError(f"Unsupported mesh type: {mesh_type}")
        self.mesh_type = mesh_type
        self.errors = []
        self.warnings = []
        self.resources_found = []

    def validate_file(self, file_path: str) -> bool:
        """
        Validate configuration file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.errors.append(f"File not found: {file_path}")
                return False

            if path.suffix.lower() not in ['.yaml', '.yml']:
                self.errors.append(f"Expected YAML file, got: {path.suffix}")
                return False

            with open(file_path, 'r') as f:
                configs = yaml.safe_load_all(f)
                for config in configs:
                    if config:
                        self._validate_resource(config)

            return len(self.errors) == 0

        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return False

    def _validate_resource(self, resource: Dict[str, Any]) -> None:
        """Validate individual resource."""
        # Check required fields
        required = ['apiVersion', 'kind', 'metadata']
        for field in required:
            if field not in resource:
                self.errors.append(f"Missing required field: {field}")
                return

        kind = resource.get('kind', '')
        metadata = resource.get('metadata', {})

        # Check metadata
        if 'name' not in metadata:
            self.errors.append(f"Resource {kind}: missing metadata.name")

        # Check namespace (recommended)
        if 'namespace' not in metadata:
            self.warnings.append(f"Resource {kind}: no namespace specified")

        # Mesh-specific validation
        if self.mesh_type == 'istio':
            self._validate_istio_resource(resource)
        elif self.mesh_type == 'linkerd':
            self._validate_linkerd_resource(resource)

        self.resources_found.append({
            'kind': kind,
            'name': metadata.get('name'),
            'namespace': metadata.get('namespace'),
        })

    def _validate_istio_resource(self, resource: Dict[str, Any]) -> None:
        """Validate Istio-specific resource."""
        kind = resource.get('kind', '')

        if kind == 'VirtualService':
            self._validate_virtual_service(resource)
        elif kind == 'DestinationRule':
            self._validate_destination_rule(resource)
        elif kind == 'Gateway':
            self._validate_gateway(resource)
        elif kind == 'AuthorizationPolicy':
            self._validate_auth_policy(resource)

    def _validate_virtual_service(self, resource: Dict[str, Any]) -> None:
        """Validate VirtualService resource."""
        spec = resource.get('spec', {})

        # Check hosts
        if 'hosts' not in spec:
            self.errors.append("VirtualService: missing spec.hosts")

        # Check http routes
        http_routes = spec.get('http', [])
        if not http_routes and not spec.get('tcp', []) and not spec.get('tls', []):
            self.warnings.append("VirtualService: no routes defined")

        for idx, route in enumerate(http_routes):
            if 'route' not in route:
                self.errors.append(f"VirtualService http[{idx}]: missing route")

    def _validate_destination_rule(self, resource: Dict[str, Any]) -> None:
        """Validate DestinationRule resource."""
        spec = resource.get('spec', {})

        # Check host
        if 'host' not in spec:
            self.errors.append("DestinationRule: missing spec.host")

        # Check for security settings
        if 'trafficPolicy' not in spec:
            self.warnings.append("DestinationRule: no traffic policy specified")

    def _validate_gateway(self, resource: Dict[str, Any]) -> None:
        """Validate Gateway resource."""
        spec = resource.get('spec', {})

        # Check selector
        if 'selector' not in spec:
            self.errors.append("Gateway: missing spec.selector")

        # Check servers
        servers = spec.get('servers', [])
        if not servers:
            self.errors.append("Gateway: no servers defined")

        for idx, server in enumerate(servers):
            if 'port' not in server:
                self.errors.append(f"Gateway server[{idx}]: missing port")
            if 'hosts' not in server:
                self.errors.append(f"Gateway server[{idx}]: missing hosts")

    def _validate_auth_policy(self, resource: Dict[str, Any]) -> None:
        """Validate AuthorizationPolicy resource."""
        spec = resource.get('spec', {})

        # Check for at least one rule or default action
        if not spec.get('rules', []) and 'action' not in spec:
            self.warnings.append("AuthorizationPolicy: no rules or action defined")

    def _validate_linkerd_resource(self, resource: Dict[str, Any]) -> None:
        """Validate Linkerd-specific resource."""
        kind = resource.get('kind', '')

        if kind == 'TrafficPolicy':
            self._validate_traffic_policy(resource)
        elif kind == 'AuthorizationPolicy':
            self._validate_linkerd_auth_policy(resource)

    def _validate_traffic_policy(self, resource: Dict[str, Any]) -> None:
        """Validate TrafficPolicy resource."""
        spec = resource.get('spec', {})

        if 'targetRef' not in spec:
            self.errors.append("TrafficPolicy: missing spec.targetRef")

    def _validate_linkerd_auth_policy(self, resource: Dict[str, Any]) -> None:
        """Validate Linkerd AuthorizationPolicy resource."""
        spec = resource.get('spec', {})

        if 'targetRef' not in spec:
            self.errors.append("AuthorizationPolicy: missing spec.targetRef")

    def check_best_practices(self) -> None:
        """Check against best practices."""
        if self.mesh_type == 'istio':
            # Check for sidecar injection
            has_sidecar = any(r['kind'] == 'Sidecar' for r in self.resources_found)
            if not has_sidecar:
                self.warnings.append(
                    "Best practice: Consider explicitly defining Sidecar resources"
                )

            # Check for PeerAuthentication
            has_peer_auth = any(r['kind'] == 'PeerAuthentication' for r in self.resources_found)
            if not has_peer_auth:
                self.warnings.append(
                    "Security: Consider defining PeerAuthentication for mTLS"
                )

    def get_report(self) -> Dict[str, Any]:
        """Get validation report."""
        return {
            'valid': len(self.errors) == 0,
            'mesh_type': self.mesh_type,
            'resources_found': self.resources_found,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'resource_count': len(self.resources_found),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate service mesh configuration against best practices'
    )
    parser.add_argument(
        'config_file',
        help='Path to service mesh configuration file (YAML)'
    )
    parser.add_argument(
        '-m', '--mesh',
        choices=['istio', 'linkerd', 'consul', 'osm'],
        default='istio',
        help='Type of service mesh'
    )
    parser.add_argument(
        '-o', '--output',
        help='Save validation report to JSON file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed validation report'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )

    args = parser.parse_args()

    try:
        validator = ServiceMeshValidator(mesh_type=args.mesh)
        is_valid = validator.validate_file(args.config_file)
        validator.check_best_practices()
        report = validator.get_report()

        # Check strict mode
        if args.strict and report['warning_count'] > 0:
            is_valid = False

        # Output report
        if args.verbose or not is_valid:
            print(json.dumps(report, indent=2))

        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Validation report saved to: {args.output}")

        sys.exit(0 if is_valid else 1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
