# Terraform configuration file for deploying infrastructure.
# This is a basic template that can be customized to fit your specific needs.
#
# For detailed documentation, refer to: https://www.terraform.io/docs/

terraform {
  required_providers {
    # Specify the cloud provider you intend to use.
    # Example: google, aws, azure
    <PROVIDER_NAME> = {
      source  = "<PROVIDER_SOURCE>"
      version = "<PROVIDER_VERSION>"
    }
  }

  required_version = ">= 1.0" # Specify the minimum Terraform version
}

# Configure the provider. Replace with your actual credentials and region.
provider "<PROVIDER_NAME>" {
  #  Provide authentication details here.
  #  For example, for AWS:
  #  region = "us-west-2"
  #  access_key = "YOUR_ACCESS_KEY"
  #  secret_key = "YOUR_SECRET_KEY"

  #  For Google Cloud:
  #  project = "YOUR_PROJECT_ID"
  #  region  = "us-central1"
}

# Define variables to make the configuration reusable.
variable "resource_name_prefix" {
  type        = string
  description = "A prefix to apply to all resource names for easy identification."
  default     = "research-to-deploy" # Change this for each deployment
}

# Example resource: A simple compute instance.
# Customize this resource to match the infrastructure requirements identified by the research.
resource "<PROVIDER_NAME>_<RESOURCE_TYPE>" "<RESOURCE_NAME>" {
  name = "${var.resource_name_prefix}-<RESOURCE_IDENTIFIER>" # e.g., instance, container
  # Add other configuration options as needed.
  # Example (for Google Cloud Compute Instance):
  # machine_type = "e2-medium"
  # zone         = "us-central1-a"
  # boot_disk {
  #   initialize_params {
  #     image = "debian-cloud/debian-11"
  #   }
  # }
}

# Example output: Export the public IP address of the instance (if applicable).
# Customize based on the resources deployed.
output "<OUTPUT_NAME>" {
  description = "The <DESCRIPTION> of the resource."
  value       = "<RESOURCE_ATTRIBUTE>" # e.g., <PROVIDER_NAME>_<RESOURCE_TYPE>.<RESOURCE_NAME>.public_ip_address
}