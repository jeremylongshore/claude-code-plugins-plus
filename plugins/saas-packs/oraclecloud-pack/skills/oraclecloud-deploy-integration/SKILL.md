---
name: oraclecloud-deploy-integration
description: 'Deploy containers to OCI using OKE (Kubernetes) or Container Instances.

  Use when deploying applications to Oracle Cloud, pushing images to OCIR, or configuring
  OKE clusters.

  Trigger with "oraclecloud deploy", "oci kubernetes", "oke deploy", "oci container
  instances", "oracle cloud deploy integration".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(kubectl:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Deploy Integration

## Overview

Deploy containerized applications to OCI using either OKE (Oracle Kubernetes Engine) or Container Instances. OKE provides full Kubernetes but requires 4x more config than EKS — you need a VCN, subnet, node pool, OCIR registry, and IAM policies before a single pod runs. Container Instances offer a simpler serverless alternative for workloads that don't need Kubernetes orchestration.

**Purpose:** Get containers running on OCI through both the full Kubernetes path (OKE) and the simpler Container Instances path, with working manifests and registry auth.

## Prerequisites

- **OCI tenancy** with an API signing key in `~/.oci/config`
- **Python 3.8+** with `pip install oci` for SDK-based provisioning
- **Docker** installed for building and pushing images
- **kubectl** installed for OKE cluster interaction
- **Compartment OCID** where resources will be created
- **VCN with subnets** — at least one public and one private subnet for OKE

## Instructions

### Step 1: Push Container Image to OCIR

Oracle Cloud Infrastructure Registry (OCIR) is OCI's Docker-compatible registry. Auth uses an OCI auth token, not your API key:

```bash
# Generate an auth token: Console > Profile > Auth Tokens > Generate Token
# Save the token — it's only shown once

# Login to OCIR (format: {region-key}.ocir.io/{namespace})
docker login us-ashburn-1.ocir.io
# Username: {tenancy-namespace}/oracleidentitycloudservice/{email}
# Password: your auth token

# Tag and push
docker tag myapp:latest us-ashburn-1.ocir.io/{namespace}/myapp:latest
docker push us-ashburn-1.ocir.io/{namespace}/myapp:latest
```

### Step 2: Create OKE Cluster via Python SDK

Use the OCI Python SDK to provision an OKE cluster programmatically:

```python
import oci

config = oci.config.from_file("~/.oci/config")
container_engine = oci.container_engine.ContainerEngineClient(config)

# Create cluster
create_cluster_response = container_engine.create_cluster(
    oci.container_engine.models.CreateClusterDetails(
        name="my-oke-cluster",
        compartment_id="ocid1.compartment.oc1..example",
        vcn_id="ocid1.vcn.oc1..example",
        kubernetes_version="v1.28.2",
        options=oci.container_engine.models.ClusterCreateOptions(
            service_lb_subnet_ids=["ocid1.subnet.oc1..example-public"],
            kubernetes_network_config=oci.container_engine.models.KubernetesNetworkConfig(
                pods_cidr="10.244.0.0/16",
                services_cidr="10.96.0.0/16"
            )
        )
    )
)
cluster_id = create_cluster_response.headers["opc-work-request-id"]
print(f"Cluster creation initiated: {cluster_id}")
```

### Step 3: Add a Node Pool

OKE clusters need at least one node pool to schedule workloads:

```python
container_engine.create_node_pool(
    oci.container_engine.models.CreateNodePoolDetails(
        compartment_id="ocid1.compartment.oc1..example",
        cluster_id="ocid1.cluster.oc1..example",
        name="pool-1",
        kubernetes_version="v1.28.2",
        node_shape="VM.Standard.E4.Flex",
        node_shape_config=oci.container_engine.models.CreateNodeShapeConfigDetails(
            ocpus=2.0,
            memory_in_gbs=16.0
        ),
        node_config_details=oci.container_engine.models.CreateNodePoolNodeConfigDetails(
            size=3,
            placement_configs=[
                oci.container_engine.models.NodePoolPlacementConfigDetails(
                    availability_domain="Uocm:US-ASHBURN-AD-1",
                    subnet_id="ocid1.subnet.oc1..example-private"
                )
            ]
        )
    )
)
```

### Step 4: Configure kubectl for OKE

```bash
# Install the OCI CLI and set up kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id ocid1.cluster.oc1..example \
  --file ~/.kube/config \
  --region us-ashburn-1 \
  --token-version 2.0.0

# Verify connectivity
kubectl get nodes
```

### Step 5: Deploy to OKE

Create a Kubernetes deployment manifest with OCIR image pull secret:

```bash
# Create OCIR pull secret
kubectl create secret docker-registry ocir-secret \
  --docker-server=us-ashburn-1.ocir.io \
  --docker-username='{namespace}/oracleidentitycloudservice/{email}' \
  --docker-password='{auth-token}' \
  --docker-email='{email}'
```

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      imagePullSecrets:
        - name: ocir-secret
      containers:
        - name: myapp
          image: us-ashburn-1.ocir.io/{namespace}/myapp:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
```

### Step 6: Container Instances (Simpler Alternative)

For workloads that don't need Kubernetes, Container Instances provide a serverless option:

```python
import oci

config = oci.config.from_file("~/.oci/config")
ci_client = oci.container_instances.ContainerInstanceClient(config)

ci_client.create_container_instance(
    oci.container_instances.models.CreateContainerInstanceDetails(
        compartment_id="ocid1.compartment.oc1..example",
        display_name="myapp-instance",
        availability_domain="Uocm:US-ASHBURN-AD-1",
        shape="CI.Standard.E4.Flex",
        shape_config=oci.container_instances.models.CreateContainerInstanceShapeConfigDetails(
            ocpus=1.0,
            memory_in_gbs=4.0
        ),
        containers=[
            oci.container_instances.models.CreateContainerDetails(
                image_url="us-ashburn-1.ocir.io/{namespace}/myapp:latest",
                display_name="myapp"
            )
        ],
        vnics=[
            oci.container_instances.models.CreateContainerVnicDetails(
                subnet_id="ocid1.subnet.oc1..example"
            )
        ]
    )
)
print("Container Instance created")
```

## Output

Successful completion produces:
- A container image pushed to OCIR with proper authentication
- Either an OKE cluster with node pool, kubeconfig, and running deployment, or a Container Instance running your application
- OCIR pull secret configured in the Kubernetes cluster
- A load-balanced service exposing your application

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad auth token for OCIR or wrong API key | Regenerate auth token in Console > Profile > Auth Tokens |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy for container engine | Add policy: `Allow group Developers to manage cluster-family in compartment X` |
| TooManyRequests | 429 | Rate limited on cluster operations | Wait and retry — OKE control plane ops are rate-limited |
| ImagePullBackOff | N/A | Wrong OCIR secret or image path | Verify `docker-server`, namespace, and image tag in pull secret |
| InternalError | 500 | OCI service issue | Check [OCI Status](https://ocistatus.oraclecloud.com) and retry |
| Node pool stuck CREATING | N/A | Insufficient capacity in AD | Try a different availability domain or shape |

## Examples

**Quick Container Instance deploy with OCI CLI:**

```bash
# List running container instances
oci container-instances container-instance list \
  --compartment-id ocid1.compartment.oc1..example

# Get cluster kubeconfig in one command
oci ce cluster create-kubeconfig \
  --cluster-id ocid1.cluster.oc1..example \
  --file ~/.kube/config \
  --region us-ashburn-1 \
  --token-version 2.0.0 && kubectl get pods
```

**Verify OCIR image exists:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
artifacts = oci.artifacts.ArtifactsClient(config)
images = artifacts.list_container_images(
    compartment_id="ocid1.compartment.oc1..example",
    repository_name="myapp"
).data
for img in images.items:
    print(f"{img.display_name} — {img.time_created}")
```

## Resources

- [OCI Container Engine (OKE)](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm) — Kubernetes service documentation
- [OCI Container Registry (OCIR)](https://docs.oracle.com/en-us/iaas/Content/Registry/home.htm) — Docker registry docs
- [OCI Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/home.htm) — serverless containers
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — SDK reference
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — IaC for all OCI resources

## Next Steps

After deployment is working, proceed to `oraclecloud-observability` to set up monitoring and alerting for your running workloads, or see `oraclecloud-performance-tuning` to optimize your shape and storage choices.
