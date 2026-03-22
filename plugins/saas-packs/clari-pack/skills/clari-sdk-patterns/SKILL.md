---
name: clari-sdk-patterns
description: |
  Production-ready Clari API client patterns in Python and TypeScript.
  Use when building reusable Clari clients, implementing export pipelines,
  or wrapping the Clari v4 API for team use.
  Trigger with phrases like "clari API patterns", "clari client wrapper",
  "clari Python client", "clari TypeScript client".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari SDK Patterns

## Overview

Clari has no official SDK -- build typed wrappers around the v4 REST API. These patterns cover the Export API for forecasts, job polling, and data transformation pipelines.

## Prerequisites

- Completed `clari-install-auth` setup
- Python 3.10+ (primary) or TypeScript 5+

## Instructions

### Step 1: Python Client

```python
# clari_client.py
import os
import time
import requests
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ClariConfig:
    api_key: str
    base_url: str = "https://api.clari.com/v4"
    poll_interval: int = 5
    max_poll_attempts: int = 60

class ClariClient:
    def __init__(self, config: Optional[ClariConfig] = None):
        self.config = config or ClariConfig(
            api_key=os.environ["CLARI_API_KEY"]
        )
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.config.api_key,
            "Content-Type": "text/plain",
        })

    def list_forecasts(self) -> list[dict]:
        resp = self.session.get(f"{self.config.base_url}/export/forecast/list")
        resp.raise_for_status()
        return resp.json()["forecasts"]

    def export_forecast(
        self,
        forecast_name: str,
        time_period: str,
        types: list[str] = None,
        currency: str = "USD",
        export_format: str = "JSON",
    ) -> dict:
        payload = {
            "timePeriod": time_period,
            "typesToExport": types or [
                "forecast", "quota", "forecast_updated",
                "adjustment", "crm_total", "crm_closed"
            ],
            "currency": currency,
            "schedule": "NONE",
            "includeHistorical": False,
            "exportFormat": export_format,
        }

        resp = self.session.post(
            f"{self.config.base_url}/export/forecast/{forecast_name}",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_job(self, job_id: str) -> dict:
        for attempt in range(self.config.max_poll_attempts):
            resp = self.session.get(
                f"{self.config.base_url}/export/jobs/{job_id}",
            )
            resp.raise_for_status()
            status = resp.json()

            if status["status"] == "COMPLETED":
                return status
            if status["status"] == "FAILED":
                raise ClariExportError(f"Job {job_id} failed: {status}")

            time.sleep(self.config.poll_interval)

        raise ClariExportError(f"Job {job_id} timed out after {self.config.max_poll_attempts} attempts")

    def download_export(self, download_url: str) -> dict:
        resp = requests.get(download_url)
        resp.raise_for_status()
        return resp.json()

    def export_and_download(
        self, forecast_name: str, time_period: str
    ) -> dict:
        job = self.export_forecast(forecast_name, time_period)
        completed = self.wait_for_job(job["jobId"])
        return self.download_export(completed["downloadUrl"])

class ClariExportError(Exception):
    pass
```

### Step 2: TypeScript Client

```typescript
// clari-client.ts
interface ClariConfig {
  apiKey: string;
  baseUrl?: string;
  pollIntervalMs?: number;
  maxPollAttempts?: number;
}

interface ForecastExport {
  entries: ForecastEntry[];
}

interface ForecastEntry {
  ownerName: string;
  ownerEmail: string;
  forecastAmount: number;
  quotaAmount: number;
  crmTotal: number;
  crmClosed: number;
  adjustmentAmount: number;
  timePeriod: string;
}

class ClariClient {
  private apiKey: string;
  private baseUrl: string;
  private pollIntervalMs: number;
  private maxPollAttempts: number;

  constructor(config: ClariConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl ?? "https://api.clari.com/v4";
    this.pollIntervalMs = config.pollIntervalMs ?? 5000;
    this.maxPollAttempts = config.maxPollAttempts ?? 60;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        apikey: this.apiKey,
        "Content-Type": "text/plain",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Clari API ${response.status}: ${await response.text()}`);
    }

    return response.json();
  }

  async listForecasts(): Promise<{ forecasts: any[] }> {
    return this.request("/export/forecast/list");
  }

  async exportForecast(forecastName: string, timePeriod: string): Promise<any> {
    return this.request(`/export/forecast/${forecastName}`, {
      method: "POST",
      body: JSON.stringify({
        timePeriod,
        typesToExport: ["forecast", "quota", "crm_total", "crm_closed"],
        currency: "USD",
        schedule: "NONE",
        includeHistorical: false,
        exportFormat: "JSON",
      }),
    });
  }

  async exportAndDownload(
    forecastName: string,
    timePeriod: string
  ): Promise<ForecastExport> {
    const job = await this.exportForecast(forecastName, timePeriod);
    const completed = await this.waitForJob(job.jobId);
    const resp = await fetch(completed.downloadUrl);
    return resp.json();
  }

  private async waitForJob(jobId: string): Promise<any> {
    for (let i = 0; i < this.maxPollAttempts; i++) {
      const status = await this.request(`/export/jobs/${jobId}`);
      if (status.status === "COMPLETED") return status;
      if (status.status === "FAILED") throw new Error(`Job failed: ${jobId}`);
      await new Promise((r) => setTimeout(r, this.pollIntervalMs));
    }
    throw new Error(`Job ${jobId} timed out`);
  }
}
```

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Invalid API key | Regenerate token |
| 403 | Insufficient permissions | Admin must grant API access |
| 404 | Wrong forecast name | List forecasts first |
| 429 | Rate limited | Back off and retry |

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [Clari Community API Guide](https://community.clari.com/product-q-a-6/clari-api-all-you-need-to-know-556)

## Next Steps

Apply patterns in `clari-core-workflow-a` for forecast export pipelines.
