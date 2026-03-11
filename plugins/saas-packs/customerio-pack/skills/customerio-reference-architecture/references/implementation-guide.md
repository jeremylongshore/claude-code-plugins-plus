# Customer.io Reference Architecture - Implementation Guide

### Step 1: Core Service Layer
```typescript
// src/services/customerio/index.ts
import { TrackClient, APIClient, RegionUS } from '@customerio/track';
import { EventEmitter } from 'events';

export interface CustomerIOConfig {
  trackSiteId: string;
  trackApiKey: string;
  appApiKey: string;
  region: 'us' | 'eu';
  environment: 'development' | 'staging' | 'production';
}

export class CustomerIOService extends EventEmitter {
  private trackClient: TrackClient;
  private apiClient: APIClient;
  private config: CustomerIOConfig;

  constructor(config: CustomerIOConfig) {
    super();
    this.config = config;

    this.trackClient = new TrackClient(
      config.trackSiteId,
      config.trackApiKey,
      { region: config.region === 'eu' ? RegionEU : RegionUS }
    );

    this.apiClient = new APIClient(config.appApiKey, {
      region: config.region === 'eu' ? RegionEU : RegionUS
    });
  }

  // User management
  async identifyUser(userId: string, attributes: UserAttributes): Promise<void> {
    this.emit('identify:start', { userId, attributes });

    try {
      await this.trackClient.identify(userId, {
        ...attributes,
        _env: this.config.environment,
        _updated_at: Math.floor(Date.now() / 1000)
      });
      this.emit('identify:success', { userId });
    } catch (error) {
      this.emit('identify:error', { userId, error });
      throw error;
    }
  }

  // Event tracking
  async trackEvent(userId: string, event: EventPayload): Promise<void> {
    this.emit('track:start', { userId, event });

    try {
      await this.trackClient.track(userId, {
        name: event.name,
        data: {
          ...event.data,
          _env: this.config.environment
        }
      });
      this.emit('track:success', { userId, event: event.name });
    } catch (error) {
      this.emit('track:error', { userId, event: event.name, error });
      throw error;
    }
  }

  // Transactional messaging
  async sendTransactional(request: TransactionalRequest): Promise<void> {
    return this.apiClient.sendEmail(request);
  }
}
```

### Step 2: Event Bus Integration
```typescript
// src/services/customerio/event-bus.ts
import { Kafka, Producer, Consumer } from 'kafkajs';
import { CustomerIOService } from './index';

interface CustomerIOEvent {
  type: 'identify' | 'track' | 'transactional';
  userId: string;
  payload: any;
  timestamp: number;
  correlationId: string;
}

export class CustomerIOEventBus {
  private producer: Producer;
  private consumer: Consumer;
  private service: CustomerIOService;

  constructor(kafka: Kafka, service: CustomerIOService) {
    this.producer = kafka.producer();
    this.consumer = kafka.consumer({ groupId: 'customerio-worker' });
    this.service = service;
  }

  async start(): Promise<void> {
    await this.producer.connect();
    await this.consumer.connect();

    await this.consumer.subscribe({
      topics: ['customerio.identify', 'customerio.track', 'customerio.transactional']
    });

    await this.consumer.run({
      eachMessage: async ({ topic, message }) => {
        const event: CustomerIOEvent = JSON.parse(message.value!.toString());
        await this.processEvent(topic, event);
      }
    });
  }

  private async processEvent(topic: string, event: CustomerIOEvent): Promise<void> {
    const startTime = Date.now();

    try {
      switch (event.type) {
        case 'identify':
          await this.service.identifyUser(event.userId, event.payload);
          break;
        case 'track':
          await this.service.trackEvent(event.userId, event.payload);
          break;
        case 'transactional':
          await this.service.sendTransactional(event.payload);
          break;
      }

      // Emit success metrics
      await this.producer.send({
        topic: 'customerio.processed',
        messages: [{
          key: event.correlationId,
          value: JSON.stringify({
            ...event,
            status: 'success',
            processingTime: Date.now() - startTime
          })
        }]
      });
    } catch (error) {
      // Dead letter queue for failed events
      await this.producer.send({
        topic: 'customerio.dlq',
        messages: [{
          key: event.correlationId,
          value: JSON.stringify({
            ...event,
            status: 'failed',
            error: error.message,
            processingTime: Date.now() - startTime
          })
        }]
      });
    }
  }

  // Publish events to be processed
  async publish(event: CustomerIOEvent): Promise<void> {
    await this.producer.send({
      topic: `customerio.${event.type}`,
      messages: [{
        key: event.userId,
        value: JSON.stringify(event)
      }]
    });
  }
}
```

### Step 3: Repository Pattern
```typescript
// src/repositories/user-messaging.ts
import { CustomerIOService } from '../services/customerio';
import { UserRepository } from './user';

export interface MessagingPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
}

export class UserMessagingRepository {
  constructor(
    private cio: CustomerIOService,
    private users: UserRepository
  ) {}

  async syncUser(userId: string): Promise<void> {
    const user = await this.users.findById(userId);
    if (!user) throw new Error(`User ${userId} not found`);

    const preferences = await this.getPreferences(userId);

    await this.cio.identifyUser(userId, {
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName,
      created_at: Math.floor(user.createdAt.getTime() / 1000),
      plan: user.subscription?.plan || 'free',
      // Preferences
      email_opt_in: preferences.email,
      push_opt_in: preferences.push,
      sms_opt_in: preferences.sms
    });
  }

  async getPreferences(userId: string): Promise<MessagingPreferences> {
    // Load from your preferences store
    return {
      email: true,
      push: false,
      sms: false,
      inApp: true
    };
  }

  async updatePreferences(
    userId: string,
    preferences: Partial<MessagingPreferences>
  ): Promise<void> {
    // Update local store
    await this.savePreferences(userId, preferences);

    // Sync to Customer.io
    await this.cio.identifyUser(userId, {
      email_opt_in: preferences.email,
      push_opt_in: preferences.push,
      sms_opt_in: preferences.sms
    });
  }
}
```

### Step 4: Webhook Handler
```typescript
// src/webhooks/customerio.ts
import { Router } from 'express';
import { EventEmitter } from 'events';

export class CustomerIOWebhooks extends EventEmitter {
  private router: Router;
  private signingSecret: string;

  constructor(signingSecret: string) {
    super();
    this.signingSecret = signingSecret;
    this.router = Router();
    this.setupRoutes();
  }

  private setupRoutes(): void {
    this.router.post('/', async (req, res) => {
      // Verify signature
      if (!this.verifySignature(req)) {
        return res.status(401).send('Invalid signature');
      }

      // Process events
      const events = req.body.events || [];

      for (const event of events) {
        this.emit(event.metric, event);
        this.emit('*', event);
      }

      res.status(200).json({ received: events.length });
    });
  }

  getRouter(): Router {
    return this.router;
  }
}

// Usage
const webhooks = new CustomerIOWebhooks(process.env.WEBHOOK_SECRET!);

webhooks.on('email_delivered', (event) => {
  // Update delivery status
});

webhooks.on('email_bounced', async (event) => {
  // Handle bounce - suppress user
  await cio.suppress(event.data.customer_id);
});

webhooks.on('*', (event) => {
  // Stream all events to data warehouse
  await streamToDataWarehouse(event);
});

app.use('/webhooks/customerio', webhooks.getRouter());
```

### Step 5: Infrastructure as Code
```hcl
# terraform/customerio.tf
resource "google_secret_manager_secret" "customerio_site_id" {
  secret_id = "customerio-site-id"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "customerio_api_key" {
  secret_id = "customerio-api-key"

  replication {
    auto {}
  }
}

resource "google_cloud_run_service" "customerio_worker" {
  name     = "customerio-worker"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project}/customerio-worker:latest"

        env {
          name = "CUSTOMERIO_SITE_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.customerio_site_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "CUSTOMERIO_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.customerio_api_key.secret_id
              key  = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_pubsub_topic" "customerio_events" {
  name = "customerio-events"
}

resource "google_bigquery_dataset" "customerio" {
  dataset_id = "customerio_events"
  location   = var.region
}

resource "google_bigquery_table" "delivery_events" {
  dataset_id = google_bigquery_dataset.customerio.dataset_id
  table_id   = "delivery_events"

  schema = file("${path.module}/schemas/delivery_events.json")

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
}
```

## Architecture Principles

1. **Separation of Concerns**: Track API, App API, and Webhooks are handled by separate services
2. **Event-Driven**: Use message queues for reliable async processing
3. **Idempotency**: All operations can be safely retried
4. **Observability**: Events are emitted for monitoring and debugging
5. **Infrastructure as Code**: All resources defined in Terraform
