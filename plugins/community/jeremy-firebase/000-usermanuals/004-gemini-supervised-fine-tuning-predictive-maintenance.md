# Supervised Fine-tuning Gemini 2.5 Flash for Predictive Maintenance

**Source:** `gemini/tuning/sft_gemini_predictive_maintenance.ipynb`
**Repository:** GoogleCloudPlatform/generative-ai
**Author:** Aniket Agrawal
**URL:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/tuning/sft_gemini_predictive_maintenance.ipynb

---

## Overview

This notebook demonstrates how to perform **supervised fine-tuning** on a Gemini model for a **predictive maintenance task** within an industrial infrastructure context. We use the `google-genai` SDK integrated with Vertex AI to train the model to **classify equipment status** based on simulated sensor readings.

### Use Case: Classifying Equipment Status from Sensor Data

Instead of predicting exact time-to-failure, we fine-tune Gemini to **classify the operational state of equipment** (e.g., "Normal", "Warning", "Critical") based on recent sensor trends. This simplifies the task into a **text-generation problem** suitable for LLM fine-tuning.

---

## Workflow

1. **Load/Generate Data**: Create simulated sensor readings and maintenance/failure logs
2. **Prepare Tuning Data (JSONL)**: Convert time-series data snippets and status labels into JSON Lines format
3. **Upload to GCS**: Store the formatted tuning data in Google Cloud Storage
4. **Launch Fine-tuning Job**: Use `google-genai` SDK (configured for Vertex AI) to start supervised tuning
5. **Monitor Job**: Track the progress of the fine-tuning job
6. **Evaluate Tuned Model**: Make predictions on new sensor data prompts using the fine-tuned model endpoint
7. **Integrate Gemini for Reporting**: Use a base Gemini model to summarize tuning job results

---

## Setup

### Install Required Packages

```bash
pip install --upgrade --user pandas numpy \
    google-cloud-aiplatform google-genai \
    google-cloud-storage gcsfs
```

**⚠️ Important:** Restart the kernel after installation.

---

## Authentication & Initialization

### Vertex AI Configuration

```python
import os
import vertexai
from google.genai import Client as VertexClient

# --- Vertex AI Configuration (Required for Fine-tuning Job) ---
PROJECT_ID = ""  # your-gcp-project-id
REGION = ""  # e.g., us-central1
BUCKET_NAME = ""  # your-gcs-bucket-name
BUCKET_URI = f"gs://{BUCKET_NAME}"

# --- Authentication (Colab/Workbench for Vertex AI) ---
if not PROJECT_ID or PROJECT_ID == "":
    try:
        from google.colab import auth
        auth.authenticate_user()
        import subprocess
        PROJECT_ID = (
            subprocess.check_output(["gcloud", "config", "get-value", "project"])
            .decode("utf-8")
            .strip()
        )
        print(f"Retrieved Project ID: {PROJECT_ID}")
    except Exception as e:
        print(f"Could not automatically retrieve Project ID. Please set it manually. Error: {e}")
```

### Create/Ensure GCS Bucket Exists

```python
# Ensure BUCKET_NAME is set, and attempt to create the bucket
if not BUCKET_NAME or BUCKET_NAME == "":
    if PROJECT_ID:
        BUCKET_NAME = f"{PROJECT_ID}-gemini-tuning-bucket"
        BUCKET_URI = f"gs://{BUCKET_NAME}"
        print(f"Bucket name not provided. Using default: {BUCKET_NAME}")
    else:
        raise ValueError("Please provide a valid GCS Bucket name or ensure PROJECT_ID is set")

print(f"Checking/Creating bucket: {BUCKET_URI}")

# Create bucket if it doesn't exist
creation_command = f"gsutil ls {BUCKET_URI} > /dev/null 2>&1 || gsutil mb -l {REGION} -p {PROJECT_ID} {BUCKET_URI}"
exit_code = os.system(creation_command)

if exit_code != 0:
    print(f"Warning: Bucket command finished with exit code {exit_code}. Check GCS permissions.")
else:
    print(f"Bucket {BUCKET_URI} ensured to exist.")
```

### Initialize Vertex AI SDK

```python
if PROJECT_ID:
    print(f"Initializing Vertex AI for project: {PROJECT_ID} in {REGION} using bucket {BUCKET_URI}")

    # Initialize Vertex AI SDK (needed for launching the tuning job)
    vertexai.init(project=PROJECT_ID, location=REGION, staging_bucket=BUCKET_URI)

    # Initialize the genai client specifically for Vertex AI operations (like tuning)
    vertex_client = VertexClient(vertexai=True, project=PROJECT_ID, location=REGION)

    print("Vertex AI SDK Initialized.")
else:
    raise ValueError("PROJECT_ID must be set for Vertex AI operations.")
```

---

## Imports and Global Configuration

```python
import json
import random
import time
import warnings
from typing import Any

import numpy as np
import pandas as pd
from google.genai import types as genai_types

# --- Global Settings ---
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
np.random.seed(42)
random.seed(42)

# --- Constants ---
BASE_MODEL_ID = "gemini-2.5-flash"  # Tunable model ID on Vertex AI
TUNED_MODEL_DISPLAY_NAME = f"pred-maint-gemini-tuned-{int(time.time())}"
DATA_DIR_GCS = f"{BUCKET_URI}/pred_maint_tuning_data"
TRAIN_JSONL_GCS_URI = f"{DATA_DIR_GCS}/train_data.jsonl"
VALIDATION_JSONL_GCS_URI = f"{DATA_DIR_GCS}/validation_data.jsonl"
TEST_JSONL_GCS_URI = f"{DATA_DIR_GCS}/test_data.jsonl"

SEQUENCE_LENGTH = 12  # Use 12 hours of data for context
FAILURE_PREDICTION_HORIZON_HOURS = 24
WARNING_HORIZON_HOURS = 72  # Issue warning if failure is within 72 hours

print(f"Base model for tuning: {BASE_MODEL_ID}")
print(f"Tuning data GCS path: {DATA_DIR_GCS}")
```

---

## Step 1: Generate Simulated Data

```python
def generate_maintenance_data(
    filename="equipment_sensor_data.csv",
    log_filename="maintenance_failure_logs.csv",
    num_rows=2000,
    equipment_id="EQ-001",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generates or loads simulated sensor data and maintenance/failure logs."""

    if os.path.exists(filename) and os.path.exists(log_filename):
        print(f"Data files '{filename}' and '{log_filename}' already exist. Loading data.")
        sensor_df = pd.read_csv(filename, parse_dates=["timestamp"])
        log_df = pd.read_csv(log_filename, parse_dates=["timestamp"])
        return sensor_df, log_df

    print("Generating new sensor and maintenance log data...")

    # Generate timestamps with timezone awareness
    timestamps = pd.date_range(
        end=pd.Timestamp.now(tz="UTC"), periods=num_rows, freq="h"
    )

    data = {"timestamp": timestamps, "equipment_id": equipment_id}

    # Generate sensor readings with trends
    data["temperature_c"] = np.random.normal(
        loc=60, scale=5, size=num_rows
    ) + np.linspace(0, 15, num_rows)

    data["vibration_hz"] = np.random.normal(
        loc=50, scale=2, size=num_rows
    ) + np.random.normal(0, np.linspace(0, 5, num_rows))

    data["pressure_psi"] = np.random.normal(
        loc=100, scale=10, size=num_rows
    ) - np.linspace(0, 5, num_rows)

    sensor_df = pd.DataFrame(data)

    # Generate maintenance logs
    log_data = []
    maintenance_indices = np.random.choice(num_rows, size=num_rows // 50, replace=False)

    for idx in maintenance_indices:
        if idx < len(timestamps):
            log_data.append({
                "timestamp": timestamps[idx],
                "equipment_id": equipment_id,
                "event_type": "Maintenance",
                "details": "Routine Check",
            })

    # Generate failure events
    failure_indices = np.linspace(num_rows * 0.9, num_rows - 1, num=5).astype(int)

    for idx in failure_indices:
        if idx < len(timestamps):
            log_data.append({
                "timestamp": timestamps[idx],
                "equipment_id": equipment_id,
                "event_type": "Failure",
                "details": "Component Failure",
            })

            # Introduce anomalies around failures
            start_anomaly = max(0, idx - 10)
            end_anomaly = min(num_rows, idx + 2)
            anomaly_size = (end_anomaly - start_anomaly, 2)

            if start_anomaly < end_anomaly and anomaly_size[0] > 0:
                sensor_df.loc[
                    start_anomaly : end_anomaly - 1, ["temperature_c", "vibration_hz"]
                ] *= np.random.uniform(1.05, 1.25, size=anomaly_size)

    log_df = pd.DataFrame(log_data)

    # Ensure UTC timestamps
    if "timestamp" in log_df.columns and not log_df.empty:
        if log_df["timestamp"].dt.tz is None:
            log_df["timestamp"] = log_df["timestamp"].dt.tz_localize("UTC")
        else:
            log_df["timestamp"] = log_df["timestamp"].dt.tz_convert("UTC")
        log_df = log_df.sort_values("timestamp").reset_index(drop=True)

    if sensor_df["timestamp"].dt.tz is None:
        sensor_df["timestamp"] = sensor_df["timestamp"].dt.tz_localize("UTC")
    else:
        sensor_df["timestamp"] = sensor_df["timestamp"].dt.tz_convert("UTC")

    sensor_df.to_csv(filename, index=False)
    log_df.to_csv(log_filename, index=False)

    print(f"Generated {len(sensor_df)} sensor records to '{filename}'.")
    print(f"Generated {len(log_df)} log entries to '{log_filename}'.")

    return sensor_df, log_df

# Load or generate data
sensor_data_df, log_data_df = generate_maintenance_data()
```

---

## Step 2: Prepare Tuning Data (JSONL Format)

Convert raw data into sequences and format as JSON Lines for Gemini supervised tuning.

```python
def create_tuning_jsonl(
    sensor_df: pd.DataFrame,
    log_df: pd.DataFrame,
    sequence_length: int,
    failure_horizon_h: int,
    warning_horizon_h: int,
) -> list[dict[str, Any]]:
    """Creates JSONL data for Gemini supervised tuning."""

    print("\n--- Preparing JSONL Tuning Data ---")
    df = sensor_df.copy()

    # Get failure times
    if log_df.empty or "timestamp" not in log_df.columns:
        print("Warning: Log DataFrame is empty or missing 'timestamp'.")
        failure_times = pd.Series(dtype="datetime64[ns, UTC]")
    else:
        if log_df["timestamp"].dt.tz is None:
            log_df["timestamp"] = log_df["timestamp"].dt.tz_localize("UTC")
        else:
            log_df["timestamp"] = log_df["timestamp"].dt.tz_convert("UTC")
        failure_times = log_df[log_df["event_type"] == "Failure"]["timestamp"]

    # Define Status based on proximity to failure
    df["status"] = "Status: Normal"
    fail_horizon = pd.Timedelta(hours=failure_horizon_h)
    warn_horizon = pd.Timedelta(hours=warning_horizon_h)

    # Ensure df timestamps are UTC
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    for f_time in failure_times:
        if f_time.tzinfo is None:
            f_time = f_time.tz_localize("UTC")

        # Critical within failure horizon
        crit_mask = (df["timestamp"] >= f_time - fail_horizon) & (
            df["timestamp"] < f_time
        )
        df.loc[crit_mask, "status"] = "Status: Critical - Failure imminent"

        # Warning within warning horizon (but not critical)
        warn_mask = (df["timestamp"] >= f_time - warn_horizon) & (
            df["timestamp"] < f_time - fail_horizon
        )
        df.loc[warn_mask, "status"] = "Status: Warning - Elevated risk detected"

    print(f"Status distribution:\n{df['status'].value_counts()}")

    feature_columns = ["temperature_c", "vibration_hz", "pressure_psi"]

    jsonl_data = []

    # Iterate through possible end points for sequences
    for i in range(sequence_length, len(df)):
        sequence_df = df.iloc[i - sequence_length : i]

        if sequence_df.isnull().values.any() or sequence_df.empty:
            continue

        target_status = df.iloc[i]["status"]
        current_equipment_id = df.iloc[i]["equipment_id"]

        # Create a text prompt summarizing the sequence
        prompt = f"Equipment {current_equipment_id} sensor data for the last {sequence_length} hours:\n"

        for col in feature_columns:
            mean_val = sequence_df[col].mean()
            std_val = sequence_df[col].std()
            diff_mean = sequence_df[col].diff().mean()
            trend = (
                "stable"
                if pd.isna(diff_mean) or abs(diff_mean) < 0.1
                else ("rising" if diff_mean > 0 else "falling")
            )
            prompt += f"- {col}: Average {mean_val:.1f}, StdDev {std_val:.1f}, Trend {trend}\n"

        prompt += "\nClassify the equipment status based on this data (Normal, Warning, or Critical)."

        # Format according to Gemini tuning requirements
        instance = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]},
                {"role": "model", "parts": [{"text": target_status}]},
            ]
        }
        jsonl_data.append(instance)

    print(f"Generated {len(jsonl_data)} JSONL instances.")
    return jsonl_data

# Create JSONL data
tuning_data_jsonl = create_tuning_jsonl(
    sensor_data_df,
    log_data_df,
    sequence_length=SEQUENCE_LENGTH,
    failure_horizon_h=FAILURE_PREDICTION_HORIZON_HOURS,
    warning_horizon_h=WARNING_HORIZON_HOURS,
)
```

### Shuffle and Split Data

```python
if tuning_data_jsonl:
    random.shuffle(tuning_data_jsonl)

    split_idx_val = int(len(tuning_data_jsonl) * 0.8)  # 80% train
    split_idx_test = int(len(tuning_data_jsonl) * 0.9)  # 10% validation, 10% test

    train_split = tuning_data_jsonl[:split_idx_val]
    validation_split = tuning_data_jsonl[split_idx_val:split_idx_test]
    test_split = tuning_data_jsonl[split_idx_test:]

    print(f"Split sizes: Train={len(train_split)}, Validation={len(validation_split)}, Test={len(test_split)}")

    # Display a sample
    print("\n--- Sample JSONL Instance ---")
    print(json.dumps(train_split[0], indent=2))
else:
    print("Warning: No tuning data generated.")
    train_split, validation_split, test_split = [], [], []
```

---

## Step 3: Upload Tuning Data to GCS

The fine-tuning service reads data directly from Google Cloud Storage.

```python
import google.auth

def save_jsonl_to_gcs(instances: list[dict[str, Any]], gcs_uri: str):
    """Saves a list of dictionaries as a JSONL file to GCS using Pandas."""

    if not instances:
        print(f"No instances to upload to {gcs_uri}. Skipping upload.")
        return

    print(f"Uploading {len(instances)} instances to {gcs_uri}...")

    try:
        # Get the application default credentials
        credentials, _ = google.auth.default()

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(instances)

        # Save DataFrame to GCS as JSONL
        storage_options = {"project": PROJECT_ID, "token": credentials}

        df.to_json(
            gcs_uri, orient="records", lines=True, storage_options=storage_options
        )

        print("Upload complete.")
    except Exception as e:
        print(f"ERROR during GCS upload to {gcs_uri}: {e}")
        print("Please ensure your GCS bucket is accessible and pandas has GCS permissions (installed via gcsfs).")

# Save splits to GCS
save_jsonl_to_gcs(train_split, TRAIN_JSONL_GCS_URI)
save_jsonl_to_gcs(validation_split, VALIDATION_JSONL_GCS_URI)
save_jsonl_to_gcs(test_split, TEST_JSONL_GCS_URI)
```

---

## Step 4: Launch Fine-tuning Job

Use the `google-genai` client **configured for Vertex AI** to start the supervised tuning job.

```python
TUNING_JOB_NAME = None  # Initialize

if not train_split or not validation_split:
    print("Skipping fine-tuning job launch as training or validation data is empty.")
else:
    print(f"Starting supervised fine-tuning job for model: {BASE_MODEL_ID}")
    print(f"Tuned model display name: {TUNED_MODEL_DISPLAY_NAME}")

    training_dataset = {
        "gcs_uri": TRAIN_JSONL_GCS_URI,
    }

    validation_dataset = genai_types.TuningValidationDataset(
        gcs_uri=VALIDATION_JSONL_GCS_URI
    )

    try:
        # Use the vertex_client configured specifically for Vertex AI operations
        sft_tuning_job = vertex_client.tunings.tune(
            base_model=BASE_MODEL_ID,
            training_dataset=training_dataset,
            config=genai_types.CreateTuningJobConfig(
                adapter_size="ADAPTER_SIZE_FOUR",  # Smaller adapter for faster tuning
                epoch_count=3,  # Keep low for demonstration
                tuned_model_display_name=TUNED_MODEL_DISPLAY_NAME,
                validation_dataset=validation_dataset,
            ),
        )

        print("\nTuning job created:")
        print(sft_tuning_job)
        TUNING_JOB_NAME = sft_tuning_job.name  # Save for monitoring

    except Exception as e:
        print(f"ERROR starting tuning job: {e}")
```

**Note:** Fine-tuning can take a significant amount of time (potentially **30 minutes to several hours** depending on dataset size, base model, and adapter size).

---

## Step 5: Monitor Job

```python
TUNED_MODEL_ENDPOINT = None  # Initialize

if TUNING_JOB_NAME:
    print(f"Monitoring tuning job: {TUNING_JOB_NAME}")

    running_states = {
        genai_types.JobState.JOB_STATE_PENDING,
        genai_types.JobState.JOB_STATE_RUNNING,
    }

    tuning_job = vertex_client.tunings.get(name=TUNING_JOB_NAME)

    while tuning_job.state in running_states:
        current_state_name = str(tuning_job.state).split(".")[-1]
        print(f"  Current state: {current_state_name}...")
        time.sleep(60)  # Check every minute

        try:
            tuning_job = vertex_client.tunings.get(name=TUNING_JOB_NAME)
        except Exception as e:
            print(f"Error polling tuning job status: {e}")
            time.sleep(120)

    final_state_name = str(tuning_job.state).split(".")[-1]
    print(f"\nTuning job finished with state: {final_state_name}")

    if tuning_job.state == genai_types.JobState.JOB_STATE_SUCCEEDED:
        if (
            hasattr(tuning_job, "tuned_model")
            and tuning_job.tuned_model
            and hasattr(tuning_job.tuned_model, "endpoint")
        ):
            TUNED_MODEL_ENDPOINT = tuning_job.tuned_model.endpoint
            print(f"Tuned model endpoint ready: {TUNED_MODEL_ENDPOINT}")
        else:
            print("Tuning job succeeded, but tuned model endpoint information is missing.")
    else:
        print("Tuning job did not succeed.")
        job_error = getattr(tuning_job, "error", None)
        if job_error:
            print(f"Error details: {job_error}")
else:
    print("Skipping monitoring as tuning job name is not set.")
```

---

## Step 6: Evaluate Tuned Model (Qualitative)

Test the tuned model with samples from the test set (data the model hasn't seen during tuning).

```python
def evaluate_qualitatively(
    tuned_endpoint: str, test_data: list[dict[str, Any]], num_samples: int = 3
):
    """Makes predictions with the tuned model and prints comparisons."""

    if not tuned_endpoint:
        print("Tuned model endpoint not available. Skipping evaluation.")
        return

    if not test_data:
        print("No test data available for evaluation.")
        return

    print(f"\n--- Qualitative Evaluation of Tuned Model ({tuned_endpoint}) ---")

    # Select random samples from the test set
    samples = random.sample(test_data, min(num_samples, len(test_data)))

    for i, sample in enumerate(samples):
        print(f"\n--- Sample {i + 1} ---")

        try:
            user_prompt = sample["contents"][0]["parts"][0]["text"]
            expected_output = sample["contents"][1]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            print(f"Skipping sample due to unexpected format: {e}")
            continue

        print(f"Input Prompt:\n{user_prompt}")
        print(f"\nExpected Output: {expected_output}")

        try:
            # Prepare contents for prediction (only user part)
            prediction_contents = [{"role": "user", "parts": [{"text": user_prompt}]}]

            # Use the vertex_client for predictions against the tuned endpoint
            response = vertex_client.models.generate_content(
                model=tuned_endpoint,
                contents=prediction_contents,
                config={
                    "temperature": 0.1,  # Low temperature for deterministic output
                    "max_output_tokens": 50,
                },
            )

            # Safely access predicted text
            predicted_output = "(No text generated)"
            if response and hasattr(response, "text"):
                predicted_output = response.text.strip()
            elif response and hasattr(response, "candidates") and response.candidates:
                first_candidate = response.candidates[0]
                finish_reason = getattr(first_candidate, "finish_reason", None)

                if (
                    finish_reason == genai_types.FinishReason.STOP
                    and hasattr(first_candidate, "content")
                    and first_candidate.content.parts
                ):
                    predicted_output = first_candidate.content.parts[0].text.strip()
                else:
                    predicted_output = f"(Generation stopped: {finish_reason})"

            print(f"Predicted Output: {predicted_output}")

            # Simple comparison
            if predicted_output == expected_output:
                print("Result: MATCH")
            else:
                print("Result: MISMATCH")

        except Exception as e:
            print(f"ERROR during prediction for sample {i + 1}: {e}")

# Run qualitative evaluation
evaluate_qualitatively(TUNED_MODEL_ENDPOINT, test_split)
```

---

## Step 7: Integrate Gemini for Reporting (Base Model)

Use a base Gemini model to summarize the fine-tuning job results.

```python
def generate_tuning_summary_with_gemini(tuning_job_details: Any):
    """Generates a summary of the tuning job using the Gemini API."""

    print("\n--- Generating Tuning Job Summary with Gemini ---")

    if not tuning_job_details:
        print("No tuning job details provided. Skipping summary.")
        return

    model_name_for_vertex_ai = "gemini-2.5-flash"

    try:
        from vertexai.preview.generative_models import GenerativeModel
        reporting_client = GenerativeModel(model_name_for_vertex_ai)
        print(f"Using Vertex AI model ({model_name_for_vertex_ai}) for reporting.")
    except Exception as e:
        print(f"Failed to initialize Vertex AI client for reporting: {e}")
        return

    try:
        # Extract relevant details
        job_name = getattr(tuning_job_details, "name", "N/A")
        job_state_enum = getattr(tuning_job_details, "state", genai_types.JobState.JOB_STATE_UNSPECIFIED)
        job_state = str(job_state_enum).split(".")[-1]
        base_model = getattr(tuning_job_details, "base_model", "N/A")
        tuned_model_obj = getattr(tuning_job_details, "tuned_model", None)
        tuned_endpoint = (
            getattr(tuned_model_obj, "endpoint", "N/A") if tuned_model_obj else "N/A"
        )
        error_obj = getattr(tuning_job_details, "error", None)
        error_message = str(error_obj) if error_obj else "None"
        config_obj = getattr(tuning_job_details, "config", None)
        display_name = (
            getattr(config_obj, "tuned_model_display_name", "N/A")
            if config_obj
            else "N/A"
        )

        prompt = f"""Generate a brief status report for a Gemini model fine-tuning job.
        Job Name: {job_name}
        Base Model: {base_model}
        Tuned Model Display Name: {display_name}
        Final Status: {job_state}
        Tuned Model Endpoint: {tuned_endpoint}
        Error (if any): {error_message}

        Summarize the outcome of this tuning job in 1-2 sentences."""

        print("\nSending request to Gemini...")
        response = reporting_client.generate_content(prompt)

        print("\n--- Gemini Tuning Job Summary ---")
        response_text = "(No text content found in response)"

        try:
            if hasattr(response, "text"):
                response_text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                first_candidate = response.candidates[0]
                finish_reason = getattr(first_candidate, "finish_reason", None)

                if (
                    finish_reason in [genai_types.FinishReason.STOP, genai_types.FinishReason.MAX_TOKENS]
                    and hasattr(first_candidate, "content")
                    and first_candidate.content.parts
                ):
                    response_text = first_candidate.content.parts[0].text
                else:
                    response_text = f"(Generation stopped: {finish_reason})"
        except Exception as resp_e:
            print(f"Error extracting text from response: {resp_e}")

        print(response_text)
        print("---------------------------------")

    except Exception as e:
        print(f"\nERROR: Failed to generate Gemini summary: {e}")

# Get the final job details and generate summary
final_tuning_job = None
if TUNING_JOB_NAME:
    try:
        final_tuning_job = vertex_client.tunings.get(name=TUNING_JOB_NAME)
    except Exception as e:
        print(f"Error retrieving final tuning job details: {e}")

generate_tuning_summary_with_gemini(final_tuning_job)
```

---

## Key Concepts Summary

### Supervised Fine-Tuning Workflow

1. **Data Preparation**
   - Generate/load time-series sensor data
   - Label data with equipment status (Normal, Warning, Critical)
   - Convert to JSONL format with user/model conversation pairs

2. **Training Dataset Format**
   - Each JSONL instance contains a prompt (sensor summary) and expected completion (status)
   - Format: `{"contents": [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}]}`

3. **Fine-Tuning Configuration**
   - Base model: `gemini-2.5-flash`
   - Adapter size: `ADAPTER_SIZE_FOUR` (smaller = faster)
   - Epoch count: 3 (for demonstration)
   - Validation dataset for monitoring

4. **Deployment**
   - Tuned model deployed to Vertex AI endpoint
   - Access via `vertex_client.models.generate_content()`

5. **Evaluation**
   - Qualitative comparison of predictions vs. expected outputs
   - Test on unseen data from test split

### Equipment Status Classification

- **Normal**: No issues detected
- **Warning**: Elevated risk detected (within 72 hours of failure)
- **Critical**: Failure imminent (within 24 hours)

### Key Parameters

- `SEQUENCE_LENGTH = 12` - Use 12 hours of sensor data for context
- `FAILURE_PREDICTION_HORIZON_HOURS = 24` - Critical status window
- `WARNING_HORIZON_HOURS = 72` - Warning status window

---

## Related Plugins

This tutorial is relevant to:

- **jeremy-vertex-engine** - Vertex AI Agent Engine deployment and management
- **jeremy-vertex-validator** - Production readiness validation for Vertex AI
- **jeremy-genkit-pro** - Firebase Genkit integration with Gemini models
- **jeremy-firebase** - Firebase platform operations with Vertex AI integration
- **jeremy-vertex-terraform** - Terraform infrastructure for Vertex AI services

---

## References

* [Vertex AI Gemini Fine-tuning Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-tuning)
* [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/)
* [Supervised Fine-Tuning Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning)
* [JSONL Format Requirements](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-tuning-format)

---

**Tutorial Type:** Jupyter Notebook (Supervised Fine-Tuning)
**Difficulty:** Advanced
**Prerequisites:** GCP Project, Vertex AI API enabled, GCS bucket, sensor data understanding
**Estimated Time:** 2-4 hours (including fine-tuning job)
**Focus:** Domain-specific model adaptation for industrial predictive maintenance
