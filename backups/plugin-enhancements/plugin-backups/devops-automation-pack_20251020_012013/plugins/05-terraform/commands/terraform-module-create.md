---
description: Generate reusable Terraform modules with best practices
shortcut: tm
category: devops
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Simplifies Terraform module creation -->
<!-- Modules are core to DRY Terraform but developers struggle with structure
     (variables, outputs, README, validation). This command generates production-ready
     modules following HashiCorp standards with documentation and examples. -->

<!-- VALIDATION: Tested with -->
<!--  AWS VPC module with subnets, NAT, routing -->
<!--  GCP Compute instance module -->
<!--  Azure Resource Group module -->

# Terraform Module Generator

Generates production-ready, reusable Terraform modules with proper structure, documentation, variable validation, and usage examples.

## When to Use This

-  Creating reusable infrastructure components
-  Need standardized module structure
-  Want validated inputs and comprehensive outputs
-  Building infrastructure library for team
-  One-off infrastructure (use root module)
-  Simple single-resource creation

## How It Works

You are a Terraform module expert. When user runs `/terraform-module-create` or `/tm`:

1. **Identify module purpose:**
   - What resource/pattern? (VPC, compute, database, etc.)
   - Cloud provider? (AWS, GCP, Azure)
   - Required vs optional features?

2. **Generate module structure:**
   ```
   modules/module-name/
   ├── main.tf          # Resource definitions
   ├── variables.tf     # Input variables with validation
   ├── outputs.tf       # Output values
   ├── versions.tf      # Terraform and provider versions
   ├── README.md        # Documentation
   └── examples/        # Usage examples
       └── complete/
           ├── main.tf
           └── README.md
   ```

3. **Apply best practices:**
   - Input validation rules
   - Sensible defaults for optional vars
   - Comprehensive outputs
   - Consistent naming conventions
   - Tags/labels support

4. **Provide documentation:**
   - Usage examples
   - Input/output reference
   - Dependencies and requirements

## Output Format

```
# Complete module directory structure
# Ready to use and publish
```

```markdown
## Usage Example

```hcl
module "example" {
  source = "./modules/module-name"

  [example configuration]
}
```
```

## Examples

### Example 1: AWS VPC Module

**User:** `/tm`

**Questions:**
- Module type? → AWS VPC
- Features? → Public/private subnets, NAT gateway, Internet gateway
- Availability zones? → Configurable (default 3)

**Output:**

```hcl
# modules/aws-vpc/versions.tf
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# modules/aws-vpc/variables.tf
variable "vpc_name" {
  description = "Name of the VPC"
  type        = string

  validation {
    condition     = length(var.vpc_name) > 0
    error_message = "VPC name cannot be empty."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones required for high availability."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT gateway (cost savings) instead of one per AZ"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

# modules/aws-vpc/main.tf
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    {
      Name = var.vpc_name
    },
    var.tags
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = "${var.vpc_name}-igw"
    },
    var.tags
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    {
      Name = "${var.vpc_name}-public-${var.availability_zones[count.index]}"
      Type = "public"
    },
    var.tags
  )
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    {
      Name = "${var.vpc_name}-private-${var.availability_zones[count.index]}"
      Type = "private"
    },
    var.tags
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0

  domain = "vpc"

  tags = merge(
    {
      Name = "${var.vpc_name}-nat-eip-${count.index + 1}"
    },
    var.tags
  )

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    {
      Name = "${var.vpc_name}-nat-${count.index + 1}"
    },
    var.tags
  )

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    {
      Name = "${var.vpc_name}-public-rt"
    },
    var.tags
  )
}

# Public Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(var.public_subnet_cidrs)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 1

  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
    }
  }

  tags = merge(
    {
      Name = "${var.vpc_name}-private-rt-${count.index + 1}"
    },
    var.tags
  )
}

# Private Route Table Associations
resource "aws_route_table_association" "private" {
  count = length(var.private_subnet_cidrs)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index].id
}

# modules/aws-vpc/outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = var.enable_nat_gateway ? aws_nat_gateway.main[*].id : []
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}
```

```markdown
# modules/aws-vpc/README.md

# AWS VPC Terraform Module

Production-ready VPC module with public/private subnets, NAT gateways, and Internet gateway.

## Features

-  VPC with configurable CIDR
-  Public and private subnets across multiple AZs
-  Internet Gateway for public subnets
-  NAT Gateway(s) for private subnet internet access
-  Route tables with proper associations
-  Configurable: single NAT (cost savings) or per-AZ (HA)

## Usage

```hcl
module "vpc" {
  source = "./modules/aws-vpc"

  vpc_name           = "myapp-vpc"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false  # One NAT per AZ for high availability

  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| vpc_name | Name of the VPC | string | - | yes |
| vpc_cidr | CIDR block for VPC | string | "10.0.0.0/16" | no |
| availability_zones | List of AZs | list(string) | - | yes |
| public_subnet_cidrs | Public subnet CIDRs | list(string) | - | yes |
| private_subnet_cidrs | Private subnet CIDRs | list(string) | - | yes |
| enable_nat_gateway | Enable NAT Gateway | bool | true | no |
| single_nat_gateway | Use single NAT (cost savings) | bool | false | no |
| tags | Additional tags | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | VPC ID |
| vpc_cidr | VPC CIDR block |
| public_subnet_ids | Public subnet IDs |
| private_subnet_ids | Private subnet IDs |
| nat_gateway_ids | NAT Gateway IDs |
| internet_gateway_id | Internet Gateway ID |

## Requirements

- Terraform >= 1.5.0
- AWS Provider >= 5.0

## Cost Optimization

Use `single_nat_gateway = true` for development environments to reduce NAT Gateway costs (from $0.045/hour × 3 AZs to $0.045/hour × 1).

## High Availability

For production, use `single_nat_gateway = false` to deploy one NAT Gateway per availability zone, ensuring redundancy if an AZ fails.
```

### Example 2: GCP Compute Instance Module

**User:** `/tm`

**Module:** GCP Compute Engine instance with optional features

**Output:**

```hcl
# modules/gcp-compute/variables.tf
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "instance_name" {
  description = "Name of the instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z][-a-z0-9]*$", var.instance_name))
    error_message = "Instance name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "machine_type" {
  description = "Machine type"
  type        = string
  default     = "e2-medium"

  validation {
    condition     = can(regex("^[a-z]+-[a-z0-9]+$", var.machine_type))
    error_message = "Invalid machine type format."
  }
}

variable "boot_disk_image" {
  description = "Boot disk image"
  type        = string
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "boot_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.boot_disk_size >= 10 && var.boot_disk_size <= 65536
    error_message = "Boot disk size must be between 10 GB and 65536 GB."
  }
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "VPC subnetwork name"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Network tags for firewall rules"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Resource labels"
  type        = map(string)
  default     = {}
}

# modules/gcp-compute/main.tf
resource "google_compute_instance" "main" {
  project      = var.project_id
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags   = var.tags
  labels = var.labels

  boot_disk {
    initialize_params {
      image = var.boot_disk_image
      size  = var.boot_disk_size
      type  = "pd-balanced"  # Balanced persistent disk
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork != "" ? var.subnetwork : null

    access_config {
      # Ephemeral public IP
    }
  }

  metadata = {
    enable-oslogin = "TRUE"  # Use OS Login for SSH
  }

  service_account {
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  # Allow Terraform to destroy with graceful shutdown
  allow_stopping_for_update = true

  lifecycle {
    ignore_changes = [
      metadata["ssh-keys"]  # Don't overwrite manual SSH keys
    ]
  }
}

# modules/gcp-compute/outputs.tf
output "instance_id" {
  description = "Instance ID"
  value       = google_compute_instance.main.instance_id
}

output "instance_name" {
  description = "Instance name"
  value       = google_compute_instance.main.name
}

output "internal_ip" {
  description = "Internal IP address"
  value       = google_compute_instance.main.network_interface[0].network_ip
}

output "external_ip" {
  description = "External IP address"
  value       = google_compute_instance.main.network_interface[0].access_config[0].nat_ip
}

output "self_link" {
  description = "Instance self link"
  value       = google_compute_instance.main.self_link
}
```

## Pro Tips

 **Always validate inputs (prevent invalid configurations)**
 **Provide sensible defaults for optional variables**
 **Use tags/labels parameters for user customization**
 **Document outputs clearly (what they represent)**
 **Include usage examples in README**

## Module Publishing

To publish module to Terraform Registry:

```bash
# 1. Tag version
git tag v1.0.0
git push --tags

# 2. Module URL format
source = "github.com/username/terraform-aws-vpc?ref=v1.0.0"

# 3. Or publish to Terraform Registry
# https://registry.terraform.io/publish/module
```
