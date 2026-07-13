# Assets

Template files for kubernetes-deployment-creator skill

## Core Templates

- [x] deployment_template.yaml: Kubernetes Deployment with resource limits, probes, and rolling updates
- [x] service_template.yaml: Service types (ClusterIP, NodePort, LoadBalancer) with ports configuration
- [x] ingress_template.yaml: Ingress with TLS, annotations, and path-based routing

## Scaling & Availability

- [x] hpa_template.yaml: HorizontalPodAutoscaler with CPU/memory metrics
- [x] pdb_template.yaml: PodDisruptionBudget for voluntary disruption protection
- [x] statefulset_template.yaml: StatefulSet for databases and stateful workloads

## Configuration

- [x] configmap_template.yaml: ConfigMap for non-sensitive configuration
- [x] secret_template.yaml: Secret for credentials and sensitive data

## Security

- [x] networkpolicy_template.yaml: NetworkPolicy for ingress/egress traffic control
