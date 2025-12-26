---
name: implement-events
description: Implement event-driven API architecture
shortcut: even
---
# Implement Event-Driven API

Build production-grade event-driven APIs with message queues, event streaming, and async communication patterns. This command generates event publishers, subscribers, message brokers integration, and event-driven architectures for microservices and distributed systems.

## Design Decisions

**Why event-driven architecture:**
- **Decoupling**: Services communicate without direct dependencies
- **Scalability**: Process events asynchronously, handle traffic spikes
- **Resilience**: Failed events can be retried, dead-letter queues prevent data loss
- **Auditability**: Event logs provide complete system activity history
- **Flexibility**: Add new consumers without modifying publishers

**Alternatives considered:**
- **Synchronous REST APIs**: Simpler but couples services, no retry capability
- **Direct database sharing**: Fastest but creates tight coupling and data ownership issues
- **GraphQL subscriptions**: Good for client-server, less suited for service-to-service
- **Webhooks**: Simple but lacks delivery guarantees and ordering

**This approach balances**: Loose coupling, reliability, scalability, and operational complexity.

## When to Use

Use event-driven architecture when:
- Building microservices that need to communicate asynchronously
- Handling high-volume, bursty workloads (user signups, order processing)
- Implementing CQRS (Command Query Responsibility Segregation)
- Creating audit logs or event sourcing systems
- Integrating multiple services that need eventual consistency
- Building real-time notification systems

Don't use when:
- Building simple CRUD applications with low traffic
- You need immediate, synchronous responses (use REST/GraphQL instead)
- Team lacks experience with message queues and async patterns
- Debugging and monitoring infrastructure isn't in place
- Strong consistency is required (use synchronous transactions)

## Prerequisites

- Message broker installed (RabbitMQ, Apache Kafka, AWS SQS/SNS, or Redis)
- Node.js 16+ or Python 3.8+ for examples
- Understanding of async/await patterns and promises
- Basic knowledge of pub/sub and message queue concepts
- (Optional) Event schema registry (Confluent Schema Registry, AWS Glue)
- (Optional) Monitoring tools (Prometheus, Grafana, CloudWatch)

## Process

1. **Choose Message Broker**
   - RabbitMQ: Flexible routing, mature, good for task queues
   - Apache Kafka: High throughput, event streaming, log retention
   - AWS SQS/SNS: Managed service, serverless, simpler operations
   - Redis Streams: Lightweight, in-memory, good for caching + events

2. **Define Event Schemas**
   - Use JSON Schema, Avro, or Protobuf for validation
   - Include metadata (event ID, timestamp, version, source)
   - Design for backward compatibility (add optional fields)

3. **Implement Publishers**
   - Publish events after successful operations (user created, order placed)
   - Use transactional outbox pattern for consistency
   - Add retry logic and dead-letter queues

4. **Build Subscribers**
   - Subscribe to relevant events (send email on user created)
   - Implement idempotent handlers (deduplicate using event ID)
   - Handle failures gracefully with retries and DLQs

5. **Add Event Patterns**
   - Event notification: Fire-and-forget notifications
   - Event-carried state transfer: Include full state in events
   - Event sourcing: Store events as source of truth
   - CQRS: Separate read/write models with events

## Output Format

### RabbitMQ Publisher (Node.js)

```javascript
// events/EventPublisher.js
const amqp = require('amqplib');
const { v4: uuidv4 } = require('uuid');

class EventPublisher {
  constructor(connectionUrl) {
    this.connectionUrl = connectionUrl;
    this.connection = null;
    this.channel = null;
  }

  async connect() {
    this.connection = await amqp.connect(this.connectionUrl);
    this.channel = await this.connection.createChannel();

    // Declare exchange for fanout (pub/sub)
    await this.channel.assertExchange('events', 'topic', { durable: true });

    console.log('Event publisher connected to RabbitMQ');
  }

  async publish(eventName, payload) {
    if (!this.channel) {
      throw new Error('Publisher not connected');
    }

    const event = {
      id: uuidv4(),
      name: eventName,
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      data: payload
    };

    const routingKey = eventName;
    const message = Buffer.from(JSON.stringify(event));

    const published = this.channel.publish(
      'events',
      routingKey,
      message,
      {
        persistent: true, // Survive broker restart
        contentType: 'application/json',
        messageId: event.id,
        timestamp: Date.now()
      }
    );

    if (!published) {
      throw new Error('Failed to publish event to exchange buffer');
    }

    console.log(`Published event: ${eventName}`, event.id);
    return event.id;
  }

  async close() {
    await this.channel?.close();
    await this.connection?.close();
  }
}

module.exports = EventPublisher;

// Usage in API route
const publisher = new EventPublisher('amqp://localhost');
await publisher.connect();

router.post('/users', async (req, res) => {
  try {
    const user = await createUser(req.body);

    // Publish event after successful creation
    await publisher.publish('user.created', {
      userId: user.id,
      email: user.email,
      name: user.name
    });

    res.status(201).json(user);
  } catch (error) {
    next(error);
  }
});
```

### RabbitMQ Subscriber (Node.js)

```javascript
// events/EventSubscriber.js
const amqp = require('amqplib');

class EventSubscriber {
  constructor(connectionUrl, queueName) {
    this.connectionUrl = connectionUrl;
    this.queueName = queueName;
    this.handlers = new Map();
  }

  async connect() {
    this.connection = await amqp.connect(this.connectionUrl);
    this.channel = await this.connection.createChannel();

    // Declare exchange
    await this.channel.assertExchange('events', 'topic', { durable: true });

    // Declare queue with dead-letter exchange
    await this.channel.assertQueue(this.queueName, {
      durable: true,
      deadLetterExchange: 'events.dlx',
      deadLetterRoutingKey: 'dead-letter'
    });

    console.log(`Subscriber ${this.queueName} connected`);
  }

  on(eventName, handler) {
    this.handlers.set(eventName, handler);

    // Bind queue to routing key
    this.channel.bindQueue(this.queueName, 'events', eventName);
    console.log(`Subscribed to event: ${eventName}`);
  }

  async start() {
    this.channel.prefetch(1); // Process one message at a time

    this.channel.consume(this.queueName, async (message) => {
      if (!message) return;

      const content = message.content.toString();
      const event = JSON.parse(content);

      console.log(`Received event: ${event.name}`, event.id);

      const handler = this.handlers.get(event.name);
      if (!handler) {
        console.warn(`No handler for event: ${event.name}`);
        this.channel.ack(message); // Acknowledge to prevent reprocessing
        return;
      }

      try {
        // Idempotency: Check if already processed
        const alreadyProcessed = await checkEventProcessed(event.id);
        if (alreadyProcessed) {
          console.log(`Event already processed: ${event.id}`);
          this.channel.ack(message);
          return;
        }

        // Process event
        await handler(event.data, event);

        // Mark as processed
        await markEventProcessed(event.id);

        // Acknowledge successful processing
        this.channel.ack(message);
      } catch (error) {
        console.error(`Error processing event ${event.name}:`, error);

        // Reject and requeue (will go to DLQ after max retries)
        this.channel.nack(message, false, false);
      }
    });

    console.log(`Subscriber ${this.queueName} started`);
  }
}

// Usage
const subscriber = new EventSubscriber('amqp://localhost', 'email-service');
await subscriber.connect();

subscriber.on('user.created', async (data, event) => {
  await sendWelcomeEmail(data.email, data.name);
  console.log(`Welcome email sent to ${data.email}`);
});

subscriber.on('order.placed', async (data, event) => {
  await sendOrderConfirmation(data.orderId, data.email);
  console.log(`Order confirmation sent for ${data.orderId}`);
});

await subscriber.start();
```

### Kafka Producer (Python)

```python
# events/kafka_producer.py
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import uuid
from datetime import datetime
from typing import Dict, Any

class EventProducer:
    def __init__(self, bootstrap_servers: str):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1  # Preserve order
        )

    def publish(self, topic: str, event_name: str, payload: Dict[str, Any]) -> str:
        event_id = str(uuid.uuid4())

        event = {
            'id': event_id,
            'name': event_name,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'data': payload
        }

        future = self.producer.send(
            topic,
            value=event,
            key=event_id.encode('utf-8')  # Partition by event ID
        )

        try:
            # Block for synchronous send (optional)
            record_metadata = future.get(timeout=10)
            print(f"Published {event_name} to {record_metadata.topic} "
                  f"partition {record_metadata.partition} offset {record_metadata.offset}")
            return event_id
        except KafkaError as e:
            print(f"Failed to publish event: {e}")
            raise

    def close(self):
        self.producer.flush()
        self.producer.close()

# Usage
producer = EventProducer('localhost:9092')

def create_user_endpoint(request):
    user = create_user(request.data)

    # Publish event
    producer.publish(
        topic='user-events',
        event_name='user.created',
        payload={
            'user_id': user.id,
            'email': user.email,
            'name': user.name
        }
    )

    return {'user': user.to_dict()}, 201
```

## Example Usage

### Example 1: Event Sourcing Pattern

```javascript
// Event sourcing: Store events as source of truth
class OrderEventStore {
  constructor(publisher) {
    this.publisher = publisher;
  }

  async placeOrder(orderId, items, customerId) {
    // Publish event (this is the source of truth)
    await this.publisher.publish('order.placed', {
      orderId,
      items,
      customerId,
      status: 'pending',
      timestamp: new Date().toISOString()
    });
  }

  async confirmPayment(orderId, paymentId) {
    await this.publisher.publish('order.payment_confirmed', {
      orderId,
      paymentId,
      timestamp: new Date().toISOString()
    });
  }

  async shipOrder(orderId, trackingNumber) {
    await this.publisher.publish('order.shipped', {
      orderId,
      trackingNumber,
      timestamp: new Date().toISOString()
    });
  }
}

// Rebuild order state from events
async function getOrderState(orderId) {
  const events = await loadEvents(`order.${orderId}.*`);

  let order = { id: orderId };
  for (const event of events) {
    switch (event.name) {
      case 'order.placed':
        order = { ...order, ...event.data, status: 'pending' };
        break;
      case 'order.payment_confirmed':
        order.status = 'confirmed';
        order.paymentId = event.data.paymentId;
        break;
      case 'order.shipped':
        order.status = 'shipped';
        order.trackingNumber = event.data.trackingNumber;
        break;
    }
  }

  return order;
}
```

### Example 2: CQRS (Command Query Responsibility Segregation)

```javascript
// Write model: Handle commands, emit events
class OrderCommandHandler {
  async handlePlaceOrder(command) {
    // Validate
    if (!command.items.length) {
      throw new Error('Order must have items');
    }

    // Create order (write)
    const order = await db.orders.create({
      customerId: command.customerId,
      items: command.items,
      status: 'pending'
    });

    // Emit event
    await publisher.publish('order.placed', {
      orderId: order.id,
      customerId: order.customerId,
      totalAmount: calculateTotal(order.items)
    });

    return order.id;
  }
}

// Read model: Listen to events, update read-optimized views
subscriber.on('order.placed', async (data) => {
  // Update denormalized view for fast queries
  await redis.set(`order:${data.orderId}`, JSON.stringify({
    orderId: data.orderId,
    customerId: data.customerId,
    totalAmount: data.totalAmount,
    status: 'pending',
    placedAt: new Date().toISOString()
  }));

  // Update customer order count
  await redis.hincrby(`customer:${data.customerId}`, 'orderCount', 1);
});
```

### Example 3: Saga Pattern (Distributed Transactions)

```javascript
// Orchestrate multi-service transaction with compensating actions
class OrderSaga {
  async execute(orderData) {
    const sagaId = uuidv4();

    try {
      // Step 1: Reserve inventory
      await publisher.publish('inventory.reserve', {
        sagaId,
        items: orderData.items
      });
      await waitForEvent('inventory.reserved', sagaId);

      // Step 2: Process payment
      await publisher.publish('payment.process', {
        sagaId,
        amount: orderData.amount,
        customerId: orderData.customerId
      });
      await waitForEvent('payment.processed', sagaId);

      // Step 3: Create shipment
      await publisher.publish('shipment.create', {
        sagaId,
        orderId: orderData.orderId,
        address: orderData.shippingAddress
      });
      await waitForEvent('shipment.created', sagaId);

      // Saga completed successfully
      await publisher.publish('order.saga_completed', { sagaId });

    } catch (error) {
      // Compensate: Rollback in reverse order
      console.error('Saga failed, executing compensations', error);

      await publisher.publish('shipment.cancel', { sagaId });
      await publisher.publish('payment.refund', { sagaId });
      await publisher.publish('inventory.release', { sagaId });
      await publisher.publish('order.saga_failed', { sagaId, reason: error.message });
    }
  }
}
```

## Error Handling

**Common issues and solutions:**

**Problem**: Events lost during broker outage
- **Cause**: Publisher doesn't wait for acknowledgment
- **Solution**: Use persistent messages, wait for broker ACK, implement transactional outbox

**Problem**: Duplicate event processing
- **Cause**: Subscriber crashes before ACK, message redelivered
- **Solution**: Make handlers idempotent, store processed event IDs in DB

**Problem**: Events processed out of order
- **Cause**: Multiple consumers, network delays
- **Solution**: Use Kafka partitions with same key, single consumer per partition

**Problem**: Subscriber can't keep up with events
- **Cause**: Handler too slow, throughput mismatch
- **Solution**: Scale subscribers horizontally, optimize handlers, batch processing

**Problem**: Dead-letter queue fills up
- **Cause**: Persistent failures not monitored
- **Solution**: Set up DLQ monitoring alerts, implement DLQ consumer for manual review

**Transactional outbox pattern** (prevent lost events):
```javascript
// Atomic database write + event publish
async function createUserWithEvent(userData) {
  const transaction = await db.transaction();

  try {
    // 1. Create user in database
    const user = await db.users.create(userData, { transaction });

    // 2. Store event in outbox table (same transaction)
    await db.outbox.create({
      eventName: 'user.created',
      payload: { userId: user.id, email: user.email },
      published: false
    }, { transaction });

    await transaction.commit();

    // 3. Background job publishes from outbox
    // If app crashes, outbox worker retries unpublished events

  } catch (error) {
    await transaction.rollback();
    throw error;
  }
}
```

## Configuration

### Event Schema (JSON Schema)

```javascript
const userCreatedSchema = {
  $schema: "http://json-schema.org/draft-07/schema#",
  type: "object",
  required: ["id", "name", "timestamp", "version", "data"],
  properties: {
    id: { type: "string", format: "uuid" },
    name: { type: "string", const: "user.created" },
    timestamp: { type: "string", format: "date-time" },
    version: { type: "string", pattern: "^\\d+\\.\\d+\\.\\d+$" },
    data: {
      type: "object",
      required: ["userId", "email"],
      properties: {
        userId: { type: "integer" },
        email: { type: "string", format: "email" },
        name: { type: "string", minLength: 1 }
      }
    }
  }
};
```

### RabbitMQ Configuration

```javascript
const rabbitConfig = {
  url: process.env.RABBITMQ_URL || 'amqp://localhost',
  exchange: {
    name: 'events',
    type: 'topic', // Supports wildcard routing (user.*, order.created)
    durable: true  // Survive broker restart
  },
  queue: {
    durable: true,
    deadLetterExchange: 'events.dlx',
    messageTtl: 86400000, // 24 hours
    maxLength: 100000,    // Max messages in queue
    maxPriority: 10       // Priority queue support
  },
  publisher: {
    confirm: true,  // Wait for broker acknowledgment
    persistent: true // Messages survive broker restart
  },
  subscriber: {
    prefetch: 1,    // Messages to prefetch
    noAck: false,   // Manual acknowledgment
    exclusive: false // Allow multiple consumers
  }
};
```

## Best Practices

DO:
- Design events as past-tense facts ("user.created" not "create.user")
- Include all necessary data in events (avoid requiring additional lookups)
- Version your events for backward compatibility
- Make event handlers idempotent (use event ID for deduplication)
- Monitor event lag (time between publish and process)
- Use dead-letter queues for failed events
- Implement circuit breakers for external dependencies in handlers
- Log event processing with correlation IDs

DON'T:
- Publish events for every database change (too granular)
- Include sensitive data without encryption (PII, secrets)
- Make event handlers depend on synchronous responses
- Publish events before database transaction commits
- Ignore event ordering when it matters (use Kafka partitions)
- Let DLQs fill up without monitoring
- Skip schema validation (causes runtime errors downstream)

TIPS:
- Use event naming conventions: `<entity>.<action>` (user.created, order.shipped)
- Include event metadata: ID, timestamp, version, source service
- Start with simple pub/sub, add event sourcing/CQRS only if needed
- Test event handlers in isolation with mock events
- Use feature flags to enable/disable event subscribers gradually
- Implement event replay capability for debugging and recovery

## Related Commands

- `/build-api-gateway` - Route events through API gateway
- `/generate-rest-api` - Generate REST API that publishes events
- `/create-monitoring` - Monitor event processing metrics
- `/implement-throttling` - Rate limit event publishing
- `/scan-api-security` - Security scan event handlers

## Performance Considerations

- **Throughput**: RabbitMQ ~10k msgs/sec, Kafka ~100k+ msgs/sec per partition
- **Latency**: RabbitMQ <10ms, Kafka 5-100ms depending on config
- **Ordering**: Kafka guarantees order per partition, RabbitMQ per queue
- **Persistence**: Disk writes slow down throughput, use SSDs for brokers

**Optimization strategies:**
```javascript
// Batch events for higher throughput
const eventBatch = [];
setInterval(async () => {
  if (eventBatch.length > 0) {
    await publisher.publishBatch(eventBatch);
    eventBatch.length = 0;
  }
}, 100); // Flush every 100ms

// Parallel event processing (if order doesn't matter)
subscriber.channel.prefetch(10); // Process 10 messages concurrently
```

## Security Considerations

- **Authentication**: Use TLS/SSL for broker connections, client certificates
- **Authorization**: Configure topic/queue permissions per service
- **Encryption**: Encrypt sensitive event data before publishing
- **Audit**: Log all event publishes and subscriptions
- **Validation**: Validate event schemas to prevent injection attacks

**Security checklist:**
```javascript
// Use TLS for RabbitMQ
const connection = await amqp.connect('amqps://user:pass@broker:5671', {
  ca: [fs.readFileSync('ca-cert.pem')],
  cert: fs.readFileSync('client-cert.pem'),
  key: fs.readFileSync('client-key.pem')
});

// Validate event schemas
const Ajv = require('ajv');
const ajv = new Ajv();
const validate = ajv.compile(eventSchema);

function publishEvent(event) {
  if (!validate(event)) {
    throw new Error(`Invalid event: ${ajv.errorsText(validate.errors)}`);
  }
  // Proceed with publish
}
```

## Troubleshooting

**Events not being consumed:**
1. Check queue binding to exchange with correct routing key
2. Verify subscriber is connected and consuming from queue
3. Check firewall/network connectivity to broker
4. Review broker logs for errors

**High event processing lag:**
1. Scale subscribers horizontally (add more consumers)
2. Optimize event handler performance (reduce I/O, batch operations)
3. Increase prefetch count for parallel processing
4. Check for slow dependencies (databases, external APIs)

**Events being processed multiple times:**
1. Verify idempotency check is working (check event ID storage)
2. Ensure ACK is sent after successful processing
3. Check for subscriber crashes before ACK
4. Review handler timeouts (increase if operations are slow)

**Dead-letter queue filling up:**
1. Review DLQ messages to identify common failure patterns
2. Fix handler bugs causing persistent failures
3. Implement DLQ replay mechanism after fixes
4. Set up alerts for DLQ threshold

## Version History

- **1.0.0** (2025-10-11): Initial release with RabbitMQ and Kafka examples
  - Event publisher and subscriber implementations
  - Event sourcing, CQRS, and Saga patterns
  - Idempotency and dead-letter queue handling
  - Transactional outbox pattern
  - Security and performance best practices
