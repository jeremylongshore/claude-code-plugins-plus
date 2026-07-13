# Architecture Patterns

## Architecture Patterns

### Pattern 1: Simple Queue-Based

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   API GW    │───▶│  Job Queue  │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                   ┌─────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│                    Worker Pool                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │Worker 1 │  │Worker 2 │  │Worker N │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
└───────┼────────────┼────────────┼───────────────────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
              ┌─────────────┐    ┌─────────────┐
              │  Kling AI   │───▶│   Storage   │
              │    API      │    │   (S3/GCS)  │
              └─────────────┘    └─────────────┘
```

Best for: Small to medium workloads, simple requirements

### Pattern 2: Event-Driven Microservices

```
┌───────────────────────────────────────────────────────────────┐
│                         Event Bus (Kafka/SNS)                  │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│   │ video.  │  │ video.  │  │ video.  │  │ video.  │         │
│   │ request │  │ started │  │complete │  │ failed  │         │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
└────────┼────────────┼────────────┼────────────┼───────────────┘
         │            │            │            │
    ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
    │ Request │  │Generator│  │ Storage │  │  Alert  │
    │ Service │  │ Service │  │ Service │  │ Service │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

Best for: Complex workflows, high scalability needs

### Pattern 3: Serverless

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  API GW/    │───▶│   Lambda/   │───▶│  Step       │
│  Cloud Run  │    │   Cloud Fn  │    │  Functions  │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                   ┌─────────────────────────┘
                   ▼
           ┌─────────────┐
           │   Submit    │──┐
           │   Job       │  │
           └─────────────┘  │
                            │
           ┌─────────────┐  │     ┌─────────────┐
           │   Wait for  │◀─┘     │  Kling AI   │
           │   Complete  │───────▶│    API      │
           └──────┬──────┘        └─────────────┘
                  │
           ┌──────┴──────┐
           ▼             ▼
    ┌─────────────┐  ┌─────────────┐
    │   Store     │  │   Notify    │
    │   Video     │  │   User      │
    └─────────────┘  └─────────────┘
```

Best for: Variable workloads, cost optimization
