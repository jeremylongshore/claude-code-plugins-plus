# Get started with Agent Engine Terraform Deployment

**Source:** `agents/agent_engine/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb`
**Repository:** GoogleCloudPlatform/generative-ai
**Authors:** Ivan Nardini, Luca Prete, Yee Sian Ng
**URL:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb

---

## Overview

Deploying AI agents on **Vertex AI Agent Engine** through **Terraform** provides a powerful **infrastructure-as-code (IaC)** approach to manage your agent deployments. Instead of clicking through the UI or writing custom API calls, you can define your entire Agent Engine deployment in configuration files that are version-controlled, repeatable, and easily automated.

### Vertex AI Agent Engine

**Fully managed, serverless platform** for deploying and hosting AI agents. You can build agents using:
- Custom Python classes following the Agent Engine template pattern
- Agent Developer Kit (ADK)
- LangChain
- LlamaIndex

The platform handles:
- Scaling
- Infrastructure management
- Enterprise-grade security
- Monitoring

### Vertex AI Reasoning Engine Terraform Resource

The [Vertex AI Reasoning Engine Terraform resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_reasoning_engine) simplifies deploying AI agents by providing a declarative configuration interface. With Terraform, you can:
- Package your agent code
- Manage dependencies
- Configure compute resources
- Maintain consistent deployments across environments

All through simple configuration files.

---

## What You Will Learn

- Set up Terraform for Vertex AI Agent Engine deployments
- Create custom agents according to the Vertex AI Agent Engine pattern
- Package your Python agent code using cloudpickle
- Deploy your first agent using Terraform
- Handle dependencies and requirements
- Deploy ADK (Agent Development Kit) agents with function calling
- Clean up resources efficiently

---

## Prerequisites

Before you begin, ensure you have:

1. **Google Cloud project** with billing enabled
2. **Vertex AI API** enabled
3. **Sufficient IAM permissions** (Vertex AI Administrator or Editor role)
4. **Cloud Storage bucket** for storing agent artifacts

---

## Installation & Setup

### Install Required Packages

```bash
pip install --upgrade 'google-cloud-aiplatform[agent_engines]>=1.120.0' \
    'google-adk>=1.15.1' \
    'cloudpickle>=3.0.0'
```

### Install Terraform

```bash
# For Linux distributions
wget https://releases.hashicorp.com/terraform/1.13.3/terraform_1.13.3_linux_amd64.zip
unzip terraform_1.13.3_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform version
```

Download Terraform from: https://www.terraform.io/downloads

### Authenticate (Colab Only)

```python
import sys

if "google.colab" in sys.modules:
    from google.colab import auth
    auth.authenticate_user()
```

### Set Google Cloud Project Information

```python
import os

PROJECT_ID = "[your-project-id]"
LOCATION = "us-central1"
BUCKET_NAME = "[your-bucket-name]"  # For storing agent artifacts

# Enable APIs
!gcloud services enable run.googleapis.com aiplatform.googleapis.com \
    artifactregistry.googleapis.com cloudbuild.googleapis.com \
    --project="{PROJECT_ID}"
```

### Initialize Vertex AI Client

```python
import vertexai

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
```

---

## Understanding Agent Engine Deployment

### Agent Engine Workflow

1. **Build**: Create your agent as a Python class with `__init__()`, `set_up()`, and `query()` methods
2. **Package**: Serialize your agent instance with cloudpickle (must be pickle-able) and store in Cloud Storage
3. **Deploy**: Use Terraform to create a Reasoning Engine resource that references your packaged agent
4. **Query**: Invoke your agent's `query()` method via API or SDK

### Key Benefits

- **Code-first approach**: Build agents using familiar Python frameworks
- **Serverless**: No infrastructure management required
- **Scalable**: Automatic scaling based on demand
- **Integrated**: Works seamlessly with Vertex AI services
- **Secure**: Enterprise-grade security and access controls

---

## Part 1: Deploy a Custom Agent

### Step 1: Create Terraform Workspace

```bash
mkdir ./agent-engine-terraform
```

### Step 2: Create the Agent Code

```bash
mkdir -p ./agent-engine-terraform/01-basic-agent/agent
```

**`agent/simple_agent.py`:**

```python
from typing import Dict

class SimpleAgent:
    def __init__(
        self,
        model: str,
        project: str,
        location: str,
    ):
        self.model_name = model
        self.project = project
        self.location = location

    def set_up(self):
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=self.project, location=self.location)
        self.model = GenerativeModel(self.model_name)

    def query(self, input: str) -> Dict:
        '''Simple agent that uses Gemini to respond to queries.

        Args:
            input: The user's query string

        Returns:
            A dictionary containing the agent's response
        '''
        response = self.model.generate_content(
            f"You are a helpful AI assistant. Respond to: {input}"
        )
        return {"output": response.text}
```

### Agent Template Pattern

Agent templates are defined as Python classes with three key methods:

1. **`__init__()`**: For agent configuration parameters (must be pickle-able)
2. **`set_up()`**: For initialization logic like establishing connections or importing packages
3. **`query()`**: To return the complete response as a single result

### Step 3: Create the Pickle File

**`serialize_agent.py`:**

```python
import cloudpickle
from agent.simple_agent import SimpleAgent

# Create and initialize agent instance
agent = SimpleAgent(
    model="gemini-2.5-flash",
    project="{PROJECT_ID}",
    location="{LOCATION}",
)

agent.set_up()

# Serialize the agent instance
pickle_file = "./agent.pkl"
with open(pickle_file, "wb") as f:
    cloudpickle.dump(agent, f)
```

```bash
cd ./agent-engine-terraform/01-basic-agent && python serialize_agent.py
```

### Step 4: Package Dependencies

**`requirements.txt`:**

```
google-cloud-aiplatform[agent_engines]>=1.120.0
google-adk>=1.15.1
cloudpickle==3.0.0
```

**Create dependencies tarball:**

```bash
cd ./agent-engine-terraform/01-basic-agent/
tar -czf dependencies.tar.gz agent
```

### Step 5: Write Terraform Configuration

**`main.tf`:**

```hcl
# Configure the Terraform provider
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.6.0"
    }
  }
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Define variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "Cloud Storage bucket name"
  type        = string
}

# Define the class methods (operations) that the agent supports
locals {
    class_methods = [
      {
        api_mode = ""
        name     = "query"
        description = "Queries the agent with the given input"
        parameters = {
          type     = "object"
          required = ["input"]
          properties = {
            input = {
              type = "string"
            }
          }
        }
      }
    ]
  }

# Define resources
resource "google_storage_bucket" "bucket" {
  name                        = var.gcs_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket_object" "bucket_obj_requirements_txt" {
  name    = "requirements.txt"
  bucket  = google_storage_bucket.bucket.id
  source  = "./requirements.txt"
}

resource "google_storage_bucket_object" "bucket_obj_pickle_pkl" {
  name    = "agent.pkl"
  bucket  = google_storage_bucket.bucket.id
  source  = "./agent.pkl"
}

resource "google_storage_bucket_object" "bucket_obj_dependencies_tar_gz" {
  name    = "dependencies.tar.gz"
  bucket  = google_storage_bucket.bucket.id
  source  = "./dependencies.tar.gz"
}

# Deploy agent to Vertex AI Agent Engine
resource "google_vertex_ai_reasoning_engine" "reasoning_engine" {
  display_name = "simple_agent"
  description  = "A simple agent deployed with Terraform"
  region       = var.region

  spec {
    class_methods   = jsonencode(local.class_methods)
    package_spec {
      dependency_files_gcs_uri = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_dependencies_tar_gz.name}"
      pickle_object_gcs_uri    = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_pickle_pkl.name}"
      python_version           = "3.12"
      requirements_gcs_uri     = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_requirements_txt.name}"
    }
  }
}

# Output the reasoning engine information
output "reasoning_engine_id" {
  description = "The ID of the deployed reasoning engine"
  value       = google_vertex_ai_reasoning_engine.reasoning_engine.name
}

output "reasoning_engine_resource" {
  description = "The full resource name"
  value       = google_vertex_ai_reasoning_engine.reasoning_engine.id
}
```

### Important: Define Class Methods

It is important you define the **class methods (operations)** that the agent supports. In this case, we register just the `query` which allows you to query the agent with the given input and config.

### Step 6: Create Variables File

**`terraform.tfvars`:**

```hcl
project_id = "{PROJECT_ID}"
region     = "{LOCATION}"
gcs_bucket_name = "{BUCKET_NAME}-custom-agent"
```

### Step 7: Deploy with Terraform

```bash
cd ./agent-engine-terraform/01-basic-agent

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration (will prompt for confirmation)
terraform apply
```

**Note:** The deployment typically takes around **5 minutes**. Terraform will show you the planned changes and ask for confirmation.

### Step 8: Verify the Deployment

```bash
cd ./agent-engine-terraform/01-basic-agent
terraform output
```

### Step 9: Test Your Deployed Agent

```python
agent_engine_resource_name = "[your-agent-engine-resource-name]"

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
)

agent = client.agent_engines.get(name=agent_engine_resource_name)

response = agent.query(input="What is artificial intelligence?")
print(f"\nAgent response:\n{response['output']}")
```

---

## Part 2: Deploy an ADK Agent with Tools

This example deploys an **ADK (Agent Development Kit) agent** with **function calling capabilities**.

### Step 1: Create the ADK Agent

```bash
mkdir -p ./agent-engine-terraform/02-adk-agent/currency_agent
```

**`currency_agent/agent.py`:**

```python
from google.adk.agents import LlmAgent

def get_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "EUR",
    currency_date: str = "latest",
):
    '''Retrieves the exchange rate between two currencies on a specified date.

    Uses the Frankfurter API (https://api.frankfurter.app/) to obtain
    exchange rate data.

    Args:
        currency_from: The base currency (3-letter currency code).
            Defaults to "USD" (US Dollar).
        currency_to: The target currency (3-letter currency code).
            Defaults to "EUR" (Euro).
        currency_date: The date for which to retrieve the exchange rate.
            Defaults to "latest" for the most recent exchange rate data.
            Can be specified in YYYY-MM-DD format for historical rates.

    Returns:
        dict: A dictionary containing the exchange rate information.
            Example: {"amount": 1.0, "base": "USD", "date": "2023-11-24",
                "rates": {"EUR": 0.95534}}
    '''
    import requests
    response = requests.get(
        f"https://api.frankfurter.app/{currency_date}",
        params={"from": currency_from, "to": currency_to},
    )
    return response.json()

# Create ADK agent with tools
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant",
    name='currency_exchange_agent',
    tools=[get_exchange_rate],
)
```

**`currency_agent/__init__.py`:**

```python
from .agent import root_agent
```

### Step 2: Pickle and Upload the ADK Agent

**`serialize_agent.py`:**

```python
import cloudpickle
from currency_agent.agent import root_agent
import vertexai
from vertexai.agent_engines import AdkApp

# Initialize Vertex AI
vertexai.init(project="{PROJECT_ID}", location="{LOCATION}")

# Initialize agent instance
agent = AdkApp(agent=root_agent)

# Serialize the agent instance
pickle_file = "./agent.pkl"
with open(pickle_file, "wb") as f:
    cloudpickle.dump(agent, f)
```

```bash
cd ./agent-engine-terraform/02-adk-agent && python serialize_agent.py
```

### Step 3: Create Requirements for ADK

**`requirements.txt`:**

```
google-cloud-aiplatform[agent_engines]>=1.120.0
google-adk>=1.15.1
cloudpickle==3.0.0
```

**Create dependencies tarball:**

```bash
cd ./agent-engine-terraform/02-adk-agent/
tar -czf dependencies.tar.gz currency_agent
```

### Step 4: Write Terraform Configuration for ADK Agent

**Key Difference:** We add `agent_framework = "google-adk"` to the spec and define ADK-specific operations.

**`main.tf`:**

```hcl
# ... (provider and variable definitions same as before) ...

# Define the class methods (operations) that the ADK agent supports
# ADK agents support multiple async operations for streaming queries, sessions, and memory
locals {
  class_methods = [
    {
      api_mode = "async_stream"
      name     = "async_stream_query"
      description = "Streams responses asynchronously from the ADK application"
      parameters = {
        type     = "object"
        required = ["message", "user_id"]
        properties = {
          message = {
            type        = "string"
            description = "The message to stream responses for"
          }
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
          session_id = {
            type        = "string"
            description = "The ID of the session. If not provided, a new session will be created"
          }
          run_config = {
            type        = "object"
            description = "The run config to use for the query"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_create_session"
      description = "Creates a new session for the user"
      parameters = {
        type     = "object"
        required = ["user_id"]
        properties = {
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_list_sessions"
      description = "Lists all sessions for the user"
      parameters = {
        type     = "object"
        required = ["user_id"]
        properties = {
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_get_session"
      description = "Retrieves a specific session"
      parameters = {
        type     = "object"
        required = ["user_id", "session_id"]
        properties = {
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
          session_id = {
            type        = "string"
            description = "The ID of the session to retrieve"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_delete_session"
      description = "Deletes a specific session"
      parameters = {
        type     = "object"
        required = ["user_id", "session_id"]
        properties = {
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
          session_id = {
            type        = "string"
            description = "The ID of the session to delete"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_add_session_to_memory"
      description = "Generates memories from a session"
      parameters = {
        type     = "object"
        required = ["session"]
        properties = {
          session = {
            type        = "object"
            description = "The session dictionary to add to memory"
          }
        }
      }
    },
    {
      api_mode = "async"
      name     = "async_search_memory"
      description = "Searches and retrieves memories for the user"
      parameters = {
        type     = "object"
        required = ["user_id", "query"]
        properties = {
          user_id = {
            type        = "string"
            description = "The ID of the user"
          }
          query = {
            type        = "string"
            description = "The query to search memories for"
          }
        }
      }
    }
  ]
}

# ... (storage resources same as before) ...

# Deploy agent to Vertex AI Agent Engine
resource "google_vertex_ai_reasoning_engine" "reasoning_engine" {
  display_name = "simple_adk_agent"
  description  = "A simple ADK agent deployed with Terraform"
  region       = var.region

  spec {
    agent_framework = "google-adk"  # ← ADK-specific parameter
    class_methods   = jsonencode(local.class_methods)
    package_spec {
      dependency_files_gcs_uri = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_dependencies_tar_gz.name}"
      pickle_object_gcs_uri    = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_pickle_pkl.name}"
      python_version           = "3.12"
      requirements_gcs_uri     = "${google_storage_bucket.bucket.url}/${google_storage_bucket_object.bucket_obj_requirements_txt.name}"
    }
  }
}

# ... (outputs same as before) ...
```

### ADK-Specific Parameters

In this scenario, we have an additional parameter in the spec:
- **`agent_framework = "google-adk"`**: Indicates we are deploying an ADK agent

Also, we define the **supported operations** as described in the [ADK documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/use/adk#supported-operations):

- `async_stream_query` - Stream responses asynchronously
- `async_create_session` - Create new session
- `async_list_sessions` - List all user sessions
- `async_get_session` - Get specific session
- `async_delete_session` - Delete session
- `async_add_session_to_memory` - Generate memories from session
- `async_search_memory` - Search and retrieve memories

### Step 5: Create Variables File

**`terraform.tfvars`:**

```hcl
project_id = "{PROJECT_ID}"
region     = "{LOCATION}"
gcs_bucket_name = "{BUCKET_NAME}-adk-agent"
```

### Step 6: Deploy the ADK Agent

```bash
cd ./agent-engine-terraform/02-adk-agent
terraform init
terraform plan
terraform apply -auto-approve
```

**Background deployment:**

```bash
nohup bash -c "cd ./agent-engine-terraform/02-adk-agent && \
    terraform init && \
    terraform plan && \
    terraform apply -auto-approve" > ./agent-engine-terraform/02-adk-agent/terraform.log 2>&1 &
```

**Monitor deployment:**

```bash
tail -f ./agent-engine-terraform/02-adk-agent/terraform.log
```

### Step 7: Verify the Deployment

```bash
cd ./agent-engine-terraform/02-adk-agent
terraform output
```

### Step 8: Test Your Deployed ADK Agent

```python
agent_engine_resource_name = "[your-agent-engine-resource-name]"

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
)

agent = client.agent_engines.get(name=agent_engine_resource_name)

# Stream query responses
async for event in agent.async_stream_query(
    user_id="user_123",
    message="What is the exchange rate from US dollars to SEK today?",
):
    print(event)
```

---

## Cleaning Up Resources

### Destroy Specific Deployment

```bash
cd ./agent-engine-terraform/01-basic-agent
terraform destroy
```

### Destroy All Agent Deployments

```python
import os

def list_subfolders(folder_path):
    """Lists all subfolders in a given folder path."""
    return [
        os.path.join(folder_path, d)
        for d in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, d))
    ]

# Get all deployment folders
folder_to_check = "./agent-engine-terraform"
subfolders = list_subfolders(folder_to_check)

# Destroy each deployment
for folder in subfolders:
    print(f"Destroying agent in {folder}...")
    !cd {folder} && terraform destroy -auto-approve
    print(f"Destroyed agent in {folder}!\n")
```

---

## Key Concepts Summary

### Agent Engine Deployment Workflow

1. **Build Agent**
   - Custom Python class with `__init__()`, `set_up()`, `query()` methods
   - OR use ADK's `LlmAgent` class

2. **Package Agent**
   - Serialize with cloudpickle (`agent.pkl`)
   - Create `requirements.txt`
   - Create `dependencies.tar.gz` (if needed)

3. **Upload to Cloud Storage**
   - Store pickle file, requirements, and dependencies

4. **Deploy with Terraform**
   - Define `google_vertex_ai_reasoning_engine` resource
   - Specify class methods (operations)
   - Reference Cloud Storage artifacts

5. **Query Agent**
   - Use Vertex AI SDK
   - Call supported operations (`query`, `async_stream_query`, etc.)

### Terraform Resource Structure

```hcl
resource "google_vertex_ai_reasoning_engine" "reasoning_engine" {
  display_name = "agent_name"
  description  = "Agent description"
  region       = var.region

  spec {
    agent_framework = "google-adk"  # Optional: for ADK agents
    class_methods   = jsonencode(local.class_methods)
    package_spec {
      dependency_files_gcs_uri = "gs://bucket/dependencies.tar.gz"
      pickle_object_gcs_uri    = "gs://bucket/agent.pkl"
      python_version           = "3.12"
      requirements_gcs_uri     = "gs://bucket/requirements.txt"
    }
  }
}
```

### Custom Agent vs ADK Agent

| Feature | Custom Agent | ADK Agent |
|---------|--------------|-----------|
| **Agent Class** | Custom Python class | `LlmAgent` or other ADK classes |
| **Required Methods** | `__init__()`, `set_up()`, `query()` | None (handled by ADK) |
| **Function Calling** | Manual implementation | Built-in with `tools` parameter |
| **Operations** | `query` | `async_stream_query`, sessions, memory ops |
| **Terraform Spec** | `agent_framework` not set | `agent_framework = "google-adk"` |

---

## Best Practices

1. **Version Control**: Store Terraform configurations in Git
2. **Environment Separation**: Use different `tfvars` files for dev/staging/prod
3. **State Management**: Use remote state (Cloud Storage backend) for team collaboration
4. **Agent Testing**: Test locally with cloudpickle before deploying
5. **Dependency Management**: Pin package versions in `requirements.txt`
6. **Resource Naming**: Use consistent naming conventions for agents and buckets
7. **Clean Up**: Always destroy unused agents to avoid costs

---

## Troubleshooting

### Common Issues

**Pickle Serialization Errors:**
- Ensure agent class is pickle-able
- Avoid unpicklable objects in `__init__()` (connections, file handles)
- Move initialization to `set_up()` method

**Terraform Deployment Failures:**
- Verify APIs are enabled (Vertex AI, Cloud Storage)
- Check IAM permissions
- Ensure Cloud Storage bucket exists and is accessible

**Agent Query Errors:**
- Verify agent deployed successfully (`terraform output`)
- Check agent resource name format
- Review agent logs in Cloud Console

---

## Related Plugins

This tutorial is relevant to:

- **jeremy-vertex-terraform** - Terraform infrastructure for Vertex AI services
- **jeremy-adk-terraform** - Terraform for ADK Agent Engine deployment
- **jeremy-vertex-engine** - Agent Engine inspection and deployment
- **jeremy-adk-orchestrator** - ADK supervisory orchestration
- **jeremy-vertex-validator** - Production readiness validation

---

## References

* [Vertex AI Reasoning Engine Terraform Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_reasoning_engine)
* [Vertex AI Agent Engine Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
* [Agent Development Kit (ADK) Documentation](https://google.github.io/adk-docs/)
* [ADK Supported Operations](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/use/adk#supported-operations)
* [Terraform Official Documentation](https://www.terraform.io/docs)

---

**Tutorial Type:** Jupyter Notebook (Infrastructure as Code - IaC)
**Difficulty:** Intermediate to Advanced
**Prerequisites:** GCP Project, Terraform installed, Vertex AI API enabled
**Estimated Time:** 60-90 minutes
**Focus:** Production-grade agent deployment with Terraform
