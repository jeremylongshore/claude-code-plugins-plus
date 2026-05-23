---
title: "Terraform for AI Infrastructure: Complete Learning Guide from Zero to Production"
description: "Comprehensive Terraform learning resource covering core concepts, best practices, state management, modules, and real-world examples for AI and cloud infrastructure deployment."
date: "2025-10-07"
tags: ["terraform", "infrastructure-as-code", "devops", "cloud", "gcp", "aws", "azure"]
featured: false
---
# Terraform for AI Infrastructure: Complete Learning Guide

**TL;DR**: Learn Infrastructure as Code with Terraform from beginner to advanced. Covers core concepts, state management, modules, best practices, and production deployment patterns for AI infrastructure.

## What is Terraform?

Terraform is an **Infrastructure as Code (IaC)** tool that lets you define and provision cloud infrastructure using declarative configuration files instead of manual clicking in web consoles.

### Key Benefits

- **Declarative Configuration**: Describe *what* you want, not *how* to get there
- **Plan Before Apply**: Preview all changes before execution
- **Version Control**: Track infrastructure changes in Git
- **Multi-Cloud**: Works with AWS, GCP, Azure, and 100+ providers
- **Idempotent**: Safe to run multiple times without side effects

### How It Works

```
1. Write Configuration (.tf files)
   ↓
2. terraform init (Download providers)
   ↓
3. terraform plan (Preview changes)
   ↓
4. terraform apply (Execute changes)
   ↓
5. Infrastructure Created/Updated
```

## Core Concepts

### 1. Providers

Providers are plugins that interact with cloud platform APIs:

```hcl
# Configure the Google Cloud Provider
provider "google" {
  project = "my-ai-project"
  region  = "us-central1"
}

# Configure AWS Provider
provider "aws" {
  region = "us-west-2"
}
```

### 2. Resources

Resources describe infrastructure objects:

```hcl
# Create a Cloud Storage bucket for ML models
resource "google_storage_bucket" "ml_models" {
  name     = "my-ai-project-models"
  location = "US"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90  # Delete old models after 90 days
    }
  }
}

# Create Compute Instance for training
resource "google_compute_instance" "training_vm" {
  name         = "ml-training-vm"
  machine_type = "n1-standard-8"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "deeplearning-platform-release/tf2-gpu-2-11-cu113"
      size  = 100
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }
}
```

### 3. Variables

Make configurations reusable:

```hcl
# variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "ml_model_bucket" {
  description = "Bucket for ML models"
  type        = string
  default     = "ml-models"
}

# Use variables
resource "google_storage_bucket" "models" {
  name     = "${var.project_id}-${var.environment}-${var.ml_model_bucket}"
  location = "US"
}
```

### 4. Outputs

Expose information about your infrastructure:

```hcl
# outputs.tf
output "bucket_url" {
  description = "URL of ML models bucket"
  value       = google_storage_bucket.models.url
}

output "training_vm_ip" {
  description = "Public IP of training VM"
  value       = google_compute_instance.training_vm.network_interface[0].access_config[0].nat_ip
}
```

### 5. Data Sources

Query existing infrastructure:

```hcl
# Get current project info
data "google_project" "current" {}

# Get latest GPU-enabled image
data "google_compute_image" "gpu_image" {
  family  = "pytorch-latest-gpu"
  project = "deeplearning-platform-release"
}

# Use in resource
resource "google_compute_instance" "gpu_vm" {
  name         = "gpu-training"
  machine_type = "n1-standard-8"

  boot_disk {
    initialize_params {
      image = data.google_compute_image.gpu_image.self_link
    }
  }
}
```

## State Management

Terraform tracks infrastructure state in a `.tfstate` file.

### Local State (Development)

```hcl
# Default: state stored locally
# terraform.tfstate in current directory
```

### Remote State (Production)

**Google Cloud Storage:**

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "ai-infrastructure/state"
  }
}
```

**AWS S3:**

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "ai-infra/terraform.tfstate"
    region = "us-west-2"

    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

### State Management Commands

```bash
# View state
terraform show

# List resources in state
terraform state list

# Remove resource from state (doesn't delete resource)
terraform state rm google_storage_bucket.example

# Move resource in state (rename)
terraform state mv google_storage_bucket.old google_storage_bucket.new

# Refresh state from real infrastructure
terraform refresh
```

## Modules: Reusable Infrastructure Components

### Module Structure

```
terraform/
├── modules/
│   └── ml-training-vm/
│       ├── main.tf       # Resources
│       ├── variables.tf  # Input variables
│       └── outputs.tf    # Output values
└── environments/
    ├── dev/
    │   └── main.tf      # Uses modules
    └── prod/
        └── main.tf
```

### Creating a Module

**modules/ml-training-vm/main.tf:**

```hcl
resource "google_compute_instance" "training_vm" {
  name         = "${var.name_prefix}-training-vm"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = var.disk_size_gb
    }
  }

  network_interface {
    network = var.network
    access_config {}
  }

  metadata = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
```

**modules/ml-training-vm/variables.tf:**

```hcl
variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "machine_type" {
  description = "Machine type for VM"
  type        = string
  default     = "n1-standard-8"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name"
  type        = string
}
```

### Using a Module

**environments/prod/main.tf:**

```hcl
module "training_vm" {
  source = "../../modules/ml-training-vm"

  name_prefix  = "prod-ml"
  machine_type = "n1-highmem-16"
  zone         = "us-central1-a"
  environment  = "production"
}

# Access module outputs
output "training_vm_ip" {
  value = module.training_vm.instance_ip
}
```

## Best Practices

### 1. Project Structure

```
terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   └── prod/
├── modules/
│   ├── compute/
│   ├── networking/
│   └── storage/
└── shared/
    ├── providers.tf
    └── versions.tf
```

### 2. Naming Conventions

```hcl
# Resource naming: project-environment-service-resource
resource "google_storage_bucket" "ml_models" {
  name = "${var.project_id}-${var.environment}-ml-models"
}

# Variable naming: descriptive and clear
variable "ml_training_instance_tier" {
  description = "Machine tier for ML training instance"
  type        = string
  default     = "n1-standard-8"
}
```

### 3. Version Constraints

```hcl
# versions.tf
terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### 4. Resource Tagging/Labeling

```hcl
# Consistent labeling across all resources
locals {
  common_labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
    team        = var.team_name
    cost_center = var.cost_center
  }
}

resource "google_storage_bucket" "ml_models" {
  name   = var.bucket_name
  labels = local.common_labels
}

resource "google_compute_instance" "training" {
  name   = var.instance_name
  labels = local.common_labels
}
```

### 5. Secrets Management

```hcl
# Don't store secrets in .tf files!
variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true  # Marks as sensitive in outputs
}

# Use random provider for generated secrets
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}
```

## Advanced Topics

### 1. Terraform Workspaces

Manage multiple environments with one configuration:

```bash
# Create workspace
terraform workspace new staging

# List workspaces
terraform workspace list

# Switch workspace
terraform workspace select prod

# Current workspace
terraform workspace show
```

**Use in configuration:**

```hcl
locals {
  environment = terraform.workspace

  machine_types = {
    dev     = "n1-standard-2"
    staging = "n1-standard-4"
    prod    = "n1-standard-8"
  }

  machine_type = local.machine_types[terraform.workspace]
}

resource "google_compute_instance" "app" {
  name         = "${terraform.workspace}-app-server"
  machine_type = local.machine_type
}
```

### 2. Dependencies

**Implicit dependency (recommended):**

```hcl
resource "google_storage_bucket" "ml_data" {
  name = "ml-training-data"
}

resource "google_storage_bucket_object" "dataset" {
  bucket = google_storage_bucket.ml_data.name  # Implicit dependency
  name   = "dataset.csv"
  source = "data/dataset.csv"
}
```

**Explicit dependency:**

```hcl
resource "google_compute_instance" "training_vm" {
  name = "training-vm"

  depends_on = [
    google_storage_bucket.ml_data,
    google_storage_bucket.ml_models
  ]
}
```

### 3. Import Existing Infrastructure

```bash
# Import existing bucket
terraform import google_storage_bucket.existing my-existing-bucket

# Then write configuration to match
resource "google_storage_bucket" "existing" {
  name     = "my-existing-bucket"
  location = "US"
}

# Verify import
terraform plan  # Should show no changes
```

## Real-World Example: ML Training Infrastructure

Complete setup for machine learning training:

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "ml-infrastructure/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Locals for common values
locals {
  common_labels = {
    environment = var.environment
    project     = "ml-training"
    managed_by  = "terraform"
  }
}

# Storage buckets
resource "google_storage_bucket" "training_data" {
  name          = "${var.project_id}-${var.environment}-training-data"
  location      = var.region
  force_destroy = false

  labels = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90
    }
  }
}

resource "google_storage_bucket" "ml_models" {
  name          = "${var.project_id}-${var.environment}-models"
  location      = var.region
  force_destroy = false

  labels = local.common_labels

  versioning {
    enabled = true
  }
}

# Training VM with GPU
resource "google_compute_instance" "gpu_training" {
  name         = "${var.environment}-gpu-training"
  machine_type = var.gpu_machine_type
  zone         = var.zone

  labels = local.common_labels

  boot_disk {
    initialize_params {
      image = "deeplearning-platform-release/pytorch-latest-gpu"
      size  = 100
      type  = "pd-ssd"
    }
  }

  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = 1
  }

  scheduling {
    on_host_maintenance = "TERMINATE"  # Required for GPU instances
  }

  network_interface {
    network = "default"
    access_config {}
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = file("${path.module}/scripts/startup.sh")
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "ml_analytics" {
  dataset_id = "${var.environment}_ml_analytics"
  location   = var.region

  labels = local.common_labels

  access {
    role          = "OWNER"
    user_by_email = var.admin_email
  }
}

# Outputs
output "training_data_bucket" {
  value = google_storage_bucket.training_data.name
}

output "models_bucket" {
  value = google_storage_bucket.ml_models.name
}

output "gpu_vm_ip" {
  value = google_compute_instance.gpu_training.network_interface[0].access_config[0].nat_ip
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.ml_analytics.dataset_id
}
```

**variables.tf:**

```hcl
variable "project_id" {
  description = "GCP Project ID"
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

variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod"
  }
}

variable "gpu_machine_type" {
  description = "Machine type for GPU training"
  type        = string
  default     = "n1-standard-8"
}

variable "admin_email" {
  description = "Admin email for BigQuery access"
  type        = string
}
```

**terraform.tfvars:**

```hcl
project_id       = "my-ai-project"
region           = "us-central1"
zone             = "us-central1-a"
environment      = "prod"
gpu_machine_type = "n1-standard-8"
admin_email      = "admin@example.com"
```

## Common Pitfalls & Solutions

### 1. State File Conflicts

**Problem**: Multiple team members modifying infrastructure simultaneously

**Solution**: Use remote state with locking

```hcl
terraform {
  backend "gcs" {
    bucket = "terraform-state"
    prefix = "prod"
  }
}
```

### 2. Hardcoded Values

**Problem**: Credentials and secrets in code

**Solution**: Use variables and secret management

```hcl
# Bad
resource "google_sql_database_instance" "db" {
  root_password = "hardcoded-password-123"
}

# Good
resource "google_sql_database_instance" "db" {
  root_password = var.db_password  # From env var or secret manager
}
```

### 3. No Version Constraints

**Problem**: Provider updates break infrastructure

**Solution**: Pin provider versions

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"  # Allow 5.x updates, not 6.0
    }
  }
}
```

## Essential Commands

```bash
# Initialize working directory
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Preview changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Import existing resource
terraform import <resource_type>.<name> <id>

# Refresh state
terraform refresh

# Output values
terraform output
```

## Learning Resources

### Official Documentation

- [Terraform Documentation](https://www.terraform.io/docs)
- [Terraform Registry](https://registry.terraform.io/)
- [Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### Best Practices

- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Google Cloud Architecture Center](https://cloud.google.com/architecture)

### Tutorials

- [HashiCorp Learn](https://learn.hashicorp.com/terraform)
- [Google Cloud Terraform Tutorials](https://cloud.google.com/docs/terraform)

## Key Takeaways

1. **Infrastructure as Code** - Treat infrastructure like software
2. **State Management** - Always use remote state in production
3. **Modules** - Build reusable components
4. **Version Control** - Track all infrastructure changes in Git
5. **Plan First** - Always review `terraform plan` before applying
6. **Security** - Never commit secrets, use Secret Manager
7. **Consistency** - Use naming conventions and labels

## What's Next

1. Set up remote state backend
2. Create reusable modules for common patterns
3. Implement CI/CD for infrastructure changes
4. Add automated testing with `terraform validate` and `tflint`
5. Explore advanced features like `for_each` and dynamic blocks

**Questions or feedback**: [jeremy@intentsolutions.io](mailto:jeremy@intentsolutions.io)
**GitHub**: [@jeremylongshore](https://github.com/jeremylongshore)

*Educational resource from Intent Solutions for AI infrastructure and DevOps practitioners.*
