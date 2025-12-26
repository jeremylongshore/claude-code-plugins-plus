---
name: create-webhook-handler
description: >
  Create secure webhook endpoints with validation and resilience
shortcut: webh
---
# Create Webhook Handler

Automatically generate production-ready webhook endpoints with signature verification, idempotency, retry handling, event processing, and comprehensive security measures for reliable third-party integrations.

## When to Use This Command

Use `/create-webhook-handler` when you need to:
- Receive real-time events from external services (Stripe, GitHub, Slack)
- Build event-driven architectures with external triggers
- Implement payment processing notifications
- Handle CI/CD pipeline events
- Process incoming data from IoT devices
- Create serverless event receivers

DON'T use this when:
- Building internal service communication (use message queues)
- Need guaranteed ordering (webhooks are best-effort)
- Handling large payloads (>10MB typically)
- Bidirectional communication needed (consider WebSockets)

## Design Decisions

This command implements **signature-based verification** as the primary approach because:
- Industry-standard security practice (HMAC-SHA256)
- Prevents replay attacks with timestamp validation
- Ensures message integrity and authenticity
- Widely supported by webhook providers
- Simple to implement and verify
- Minimal overhead for validation

**Alternative considered: OAuth token validation**
- More complex setup required
- Additional network calls for validation
- Higher latency
- Recommended for user-authenticated webhooks

**Alternative considered: mTLS (mutual TLS)**
- Strongest security option
- Complex certificate management
- Not widely supported
- Recommended for enterprise B2B integrations

## Prerequisites

Before running this command:
1. Webhook URL endpoint defined
2. Shared secret or signing key from provider
3. Event types to handle documented
4. Database for idempotency tracking
5. Queue system for async processing (optional)

## Implementation Process

### Step 1: Create Webhook Endpoint
Define secure POST endpoint with proper routing and middleware.

### Step 2: Implement Signature Verification
Validate webhook authenticity using HMAC signatures.

### Step 3: Add Idempotency Handling
Prevent duplicate processing of retried events.

### Step 4: Route Events to Handlers
Dispatch events to appropriate processing functions.

### Step 5: Configure Monitoring
Set up logging, metrics, and alerting for webhook health.

## Output Format

The command generates:
- `webhooks/handlers/` - Event-specific handler functions
- `webhooks/middleware/` - Signature verification, rate limiting
- `webhooks/routes.js` - Webhook endpoint definitions
- `webhooks/processors/` - Async event processors
- `webhooks/schemas/` - Event validation schemas
- `config/webhooks.json` - Provider configurations
- `tests/webhooks/` - Integration tests with mock events

## Code Examples

### Example 1: Multi-Provider Webhook System with Express

```javascript
// webhooks/middleware/signature.js
const crypto = require('crypto');
const { WebhookError } = require('../errors');

class SignatureVerifier {
    constructor(config) {
        this.providers = config.providers;
        this.timestampTolerance = config.timestampTolerance || 300; // 5 minutes
    }

    // Stripe signature verification
    verifyStripe(payload, signature, secret) {
        const elements = signature.split(',');
        const timestamp = elements.find(e => e.startsWith('t=')).substring(2);
        const signatures = elements
            .filter(e => e.startsWith('v1='))
            .map(e => e.substring(3));

        // Check timestamp to prevent replay attacks
        const currentTime = Math.floor(Date.now() / 1000);
        if (currentTime - parseInt(timestamp) > this.timestampTolerance) {
            throw new WebhookError('Webhook timestamp too old', 'TIMESTAMP_TOO_OLD');
        }

        // Calculate expected signature
        const signedPayload = `${timestamp}.${payload}`;
        const expectedSignature = crypto
            .createHmac('sha256', secret)
            .update(signedPayload)
            .digest('hex');

        // Compare signatures
        const validSignature = signatures.some(sig =>
            crypto.timingSafeEqual(
                Buffer.from(sig),
                Buffer.from(expectedSignature)
            )
        );

        if (!validSignature) {
            throw new WebhookError('Invalid signature', 'INVALID_SIGNATURE');
        }

        return true;
    }

    // GitHub signature verification
    verifyGitHub(payload, signature, secret) {
        if (!signature.startsWith('sha256=')) {
            throw new WebhookError('Invalid signature format', 'INVALID_FORMAT');
        }

        const expectedSignature = 'sha256=' + crypto
            .createHmac('sha256', secret)
            .update(payload)
            .digest('hex');

        const isValid = crypto.timingSafeEqual(
            Buffer.from(signature),
            Buffer.from(expectedSignature)
        );

        if (!isValid) {
            throw new WebhookError('Invalid signature', 'INVALID_SIGNATURE');
        }

        return true;
    }

    // Shopify signature verification
    verifyShopify(payload, signature, secret) {
        const hash = crypto
            .createHmac('sha256', secret)
            .update(payload, 'utf8')
            .digest('base64');

        const isValid = crypto.timingSafeEqual(
            Buffer.from(signature),
            Buffer.from(hash)
        );

        if (!isValid) {
            throw new WebhookError('Invalid signature', 'INVALID_SIGNATURE');
        }

        return true;
    }

    // Generic HMAC verification
    verifyHMAC(payload, signature, secret, algorithm = 'sha256') {
        const expectedSignature = crypto
            .createHmac(algorithm, secret)
            .update(payload)
            .digest('hex');

        const isValid = crypto.timingSafeEqual(
            Buffer.from(signature),
            Buffer.from(expectedSignature)
        );

        if (!isValid) {
            throw new WebhookError('Invalid signature', 'INVALID_SIGNATURE');
        }

        return true;
    }

    // Middleware factory
    createMiddleware(provider) {
        return async (req, res, next) => {
            try {
                const config = this.providers[provider];
                if (!config) {
                    throw new WebhookError('Unknown provider', 'UNKNOWN_PROVIDER');
                }

                const rawBody = req.rawBody || JSON.stringify(req.body);
                const signature = req.headers[config.headerName];

                if (!signature) {
                    throw new WebhookError('Missing signature', 'MISSING_SIGNATURE');
                }

                // Verify based on provider
                switch (provider) {
                    case 'stripe':
                        this.verifyStripe(rawBody, signature, config.secret);
                        break;
                    case 'github':
                        this.verifyGitHub(rawBody, signature, config.secret);
                        break;
                    case 'shopify':
                        this.verifyShopify(rawBody, signature, config.secret);
                        break;
                    default:
                        this.verifyHMAC(rawBody, signature, config.secret, config.algorithm);
                }

                // Add provider info to request
                req.webhookProvider = provider;
                req.webhookVerified = true;

                next();
            } catch (error) {
                console.error(`Webhook verification failed: ${error.message}`);
                res.status(401).json({
                    error: 'Webhook verification failed',
                    code: error.code || 'VERIFICATION_FAILED'
                });
            }
        };
    }
}

// webhooks/middleware/idempotency.js
class IdempotencyHandler {
    constructor(store) {
        this.store = store; // Redis or database
        this.ttl = 86400; // 24 hours
    }

    async middleware(req, res, next) {
        try {
            // Extract idempotency key
            const idempotencyKey =
                req.headers['idempotency-key'] ||
                req.body.id ||
                req.body.event_id ||
                this.generateKey(req);

            // Check if already processed
            const existing = await this.store.get(idempotencyKey);
            if (existing) {
                console.log(`Duplicate webhook detected: ${idempotencyKey}`);
                const result = JSON.parse(existing);
                return res.status(result.status).json(result.body);
            }

            // Store the key immediately to prevent race conditions
            await this.store.setNX(idempotencyKey, 'PROCESSING', this.ttl);

            // Attach key to request
            req.idempotencyKey = idempotencyKey;

            // Capture response
            const originalSend = res.json;
            res.json = function(body) {
                // Store the response
                const response = {
                    status: res.statusCode,
                    body: body
                };
                this.store.set(
                    idempotencyKey,
                    JSON.stringify(response),
                    this.ttl
                ).catch(err => console.error('Failed to store response:', err));

                // Send the original response
                return originalSend.call(res, body);
            }.bind(this);

            next();
        } catch (error) {
            console.error('Idempotency check failed:', error);
            next(); // Continue processing even if idempotency fails
        }
    }

    generateKey(req) {
        const content = JSON.stringify({
            provider: req.webhookProvider,
            body: req.body,
            timestamp: Math.floor(Date.now() / 60000) // 1-minute window
        });

        return crypto
            .createHash('sha256')
            .update(content)
            .digest('hex');
    }
}

// webhooks/handlers/stripe.js
const { Queue } = require('bull');
const { EventEmitter } = require('events');

class StripeWebhookHandler extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.queue = new Queue('stripe-events', config.redis);
        this.setupProcessors();
    }

    async handleWebhook(req, res) {
        const event = req.body;

        // Log webhook receipt
        console.log(`Received Stripe webhook: ${event.type} (${event.id})`);

        try {
            // Validate event data
            this.validateEvent(event);

            // Queue for async processing
            const job = await this.queue.add(event.type, event, {
                attempts: 3,
                backoff: {
                    type: 'exponential',
                    delay: 2000
                },
                removeOnComplete: false,
                removeOnFail: false
            });

            // Emit event for real-time processing if needed
            this.emit(event.type, event);

            // Respond quickly to acknowledge receipt
            res.status(200).json({
                received: true,
                jobId: job.id,
                eventId: event.id
            });

        } catch (error) {
            console.error('Webhook processing error:', error);

            // Still return 200 to prevent retries if it's our error
            if (error.code === 'VALIDATION_ERROR') {
                res.status(200).json({
                    received: true,
                    error: 'Validation failed, event ignored'
                });
            } else {
                // Return 500 for Stripe to retry
                res.status(500).json({
                    error: 'Processing failed',
                    message: error.message
                });
            }
        }
    }

    validateEvent(event) {
        if (!event.type || !event.id || !event.data) {
            throw new Error('Invalid event structure');
        }

        // Additional validation based on event type
        switch (event.type) {
            case 'payment_intent.succeeded':
                if (!event.data.object.amount) {
                    throw new Error('Missing amount in payment_intent');
                }
                break;
            case 'customer.subscription.deleted':
                if (!event.data.object.customer) {
                    throw new Error('Missing customer in subscription');
                }
                break;
        }
    }

    setupProcessors() {
        // Payment succeeded
        this.queue.process('payment_intent.succeeded', async (job) => {
            const event = job.data;
            const payment = event.data.object;

            // Update order status
            await this.updateOrderStatus(payment.metadata.orderId, 'paid');

            // Send confirmation email
            await this.sendPaymentConfirmation(payment);

            // Update inventory
            await this.updateInventory(payment.metadata.orderId);

            // Analytics
            await this.trackRevenue(payment.amount / 100, payment.currency);

            return { processed: true, orderId: payment.metadata.orderId };
        });

        // Subscription canceled
        this.queue.process('customer.subscription.deleted', async (job) => {
            const event = job.data;
            const subscription = event.data.object;

            // Update user account
            await this.updateUserSubscription(subscription.customer, null);

            // Send cancellation email
            await this.sendCancellationEmail(subscription);

            // Clean up resources
            await this.cleanupUserResources(subscription.customer);

            return { processed: true, customerId: subscription.customer };
        });

        // Payment failed
        this.queue.process('payment_intent.payment_failed', async (job) => {
            const event = job.data;
            const payment = event.data.object;

            // Notify customer
            await this.sendPaymentFailedNotification(payment);

            // Update order status
            await this.updateOrderStatus(payment.metadata.orderId, 'payment_failed');

            // Alert operations team if high-value
            if (payment.amount > 100000) { // $1000+
                await this.alertOperationsTeam(payment);
            }

            return { processed: true, orderId: payment.metadata.orderId };
        });

        // Handle job failures
        this.queue.on('failed', (job, err) => {
            console.error(`Job ${job.id} failed:`, err);
            this.alertOnFailure(job, err);
        });

        // Monitor job completion
        this.queue.on('completed', (job, result) => {
            console.log(`Job ${job.id} completed:`, result);
        });
    }

    // Helper methods
    async updateOrderStatus(orderId, status) {
        // Implementation
    }

    async sendPaymentConfirmation(payment) {
        // Implementation
    }

    async updateInventory(orderId) {
        // Implementation
    }

    async trackRevenue(amount, currency) {
        // Implementation
    }

    async alertOnFailure(job, error) {
        // Send to monitoring service
    }
}

// webhooks/routes.js
const express = require('express');
const router = express.Router();
const { SignatureVerifier } = require('./middleware/signature');
const { IdempotencyHandler } = require('./middleware/idempotency');
const { RateLimiter } = require('./middleware/rateLimiter');
const { StripeWebhookHandler } = require('./handlers/stripe');
const { GitHubWebhookHandler } = require('./handlers/github');
const Redis = require('ioredis');

// Initialize middleware
const redis = new Redis(process.env.REDIS_URL);
const signatureVerifier = new SignatureVerifier({
    providers: {
        stripe: {
            secret: process.env.STRIPE_WEBHOOK_SECRET,
            headerName: 'stripe-signature'
        },
        github: {
            secret: process.env.GITHUB_WEBHOOK_SECRET,
            headerName: 'x-hub-signature-256'
        },
        shopify: {
            secret: process.env.SHOPIFY_WEBHOOK_SECRET,
            headerName: 'x-shopify-hmac-sha256'
        }
    },
    timestampTolerance: 300
});

const idempotencyHandler = new IdempotencyHandler(redis);
const rateLimiter = new RateLimiter({
    windowMs: 60000,
    maxRequests: 100,
    keyGenerator: (req) => req.webhookProvider
});

// Initialize handlers
const stripeHandler = new StripeWebhookHandler({ redis });
const githubHandler = new GitHubWebhookHandler({ redis });

// Stripe webhooks
router.post('/stripe',
    express.raw({ type: 'application/json' }),
    signatureVerifier.createMiddleware('stripe'),
    idempotencyHandler.middleware.bind(idempotencyHandler),
    rateLimiter.middleware(),
    stripeHandler.handleWebhook.bind(stripeHandler)
);

// GitHub webhooks
router.post('/github',
    express.json({ limit: '10mb' }),
    signatureVerifier.createMiddleware('github'),
    idempotencyHandler.middleware.bind(idempotencyHandler),
    rateLimiter.middleware(),
    githubHandler.handleWebhook.bind(githubHandler)
);

// Health check endpoint
router.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        providers: ['stripe', 'github', 'shopify'],
        timestamp: new Date().toISOString()
    });
});

module.exports = router;
```

### Example 2: Serverless Webhook Handler with AWS Lambda

```python
# webhook_handler.py - AWS Lambda function
import json
import hmac
import hashlib
import time
import boto3
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
sns = boto3.client('sns')

class WebhookProvider(Enum):
    STRIPE = "stripe"
    GITHUB = "github"
    SLACK = "slack"
    SENDGRID = "sendgrid"

@dataclass
class WebhookConfig:
    provider: WebhookProvider
    secret: str
    header_name: str
    algorithm: str = "sha256"
    timestamp_tolerance: int = 300

class WebhookValidator:
    """Validates webhook signatures from various providers."""

    @staticmethod
    def validate_stripe(body: str, signature: str, secret: str) -> bool:
        """Validate Stripe webhook signature."""
        elements = signature.split(',')
        timestamp = None
        signatures = []

        for element in elements:
            key, value = element.split('=')
            if key == 't':
                timestamp = value
            elif key == 'v1':
                signatures.append(value)

        if not timestamp:
            raise ValueError("No timestamp in signature")

        # Check timestamp
        current_time = int(time.time())
        if current_time - int(timestamp) > 300:  # 5 minutes
            raise ValueError("Timestamp too old")

        # Calculate expected signature
        signed_payload = f"{timestamp}.{body}"
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return any(
            hmac.compare_digest(sig, expected_sig)
            for sig in signatures
        )

    @staticmethod
    def validate_github(body: str, signature: str, secret: str) -> bool:
        """Validate GitHub webhook signature."""
        if not signature.startswith('sha256='):
            raise ValueError("Invalid signature format")

        expected = 'sha256=' + hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    @staticmethod
    def validate_generic(
        body: str,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
    ) -> bool:
        """Generic HMAC validation."""
        hash_func = getattr(hashlib, algorithm)
        expected = hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hash_func
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

class IdempotencyManager:
    """Manages idempotent processing of webhooks."""

    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)

    async def check_and_record(self, event_id: str) -> bool:
        """Check if event was already processed and record it."""
        try:
            # Try to create item with conditional check
            self.table.put_item(
                Item={
                    'event_id': event_id,
                    'processed_at': int(time.time()),
                    'ttl': int(time.time()) + 86400  # 24 hour TTL
                },
                ConditionExpression='attribute_not_exists(event_id)'
            )
            return False  # Not processed before
        except Exception as e:
            if 'ConditionalCheckFailedException' in str(e):
                return True  # Already processed
            raise

class WebhookProcessor:
    """Processes webhook events asynchronously."""

    def __init__(self, queue_url: str, topic_arn: str):
        self.queue_url = queue_url
        self.topic_arn = topic_arn

    async def process_stripe_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe webhook events."""
        event_type = event.get('type')
        event_data = event.get('data', {}).get('object', {})

        handlers = {
            'payment_intent.succeeded': self.handle_payment_success,
            'payment_intent.failed': self.handle_payment_failure,
            'customer.subscription.created': self.handle_subscription_created,
            'customer.subscription.deleted': self.handle_subscription_deleted,
            'invoice.payment_failed': self.handle_invoice_failed
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(event_data)
        else:
            print(f"No handler for event type: {event_type}")
            return {'processed': False, 'reason': 'No handler'}

    async def handle_payment_success(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment."""
        # Queue order fulfillment
        await self.queue_message({
            'action': 'fulfill_order',
            'order_id': payment.get('metadata', {}).get('order_id'),
            'amount': payment.get('amount'),
            'currency': payment.get('currency')
        })

        # Send notification
        await self.send_notification({
            'type': 'payment_success',
            'customer_email': payment.get('receipt_email'),
            'amount': payment.get('amount') / 100
        })

        return {'processed': True, 'action': 'payment_processed'}

    async def queue_message(self, message: Dict[str, Any]):
        """Queue message for async processing."""
        sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'Type': {
                    'StringValue': message.get('action', 'unknown'),
                    'DataType': 'String'
                }
            }
        )

    async def send_notification(self, notification: Dict[str, Any]):
        """Send SNS notification."""
        sns.publish(
            TopicArn=self.topic_arn,
            Message=json.dumps(notification),
            Subject=f"Webhook Event: {notification.get('type')}"
        )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for webhook processing."""

    # Parse request
    body = event.get('body', '')
    headers = event.get('headers', {})
    path = event.get('path', '')

    # Determine provider from path
    provider = path.split('/')[-1]  # /webhooks/stripe -> stripe

    try:
        # Get configuration
        config = WebhookConfig(
            provider=WebhookProvider(provider),
            secret=os.environ[f'{provider.upper()}_WEBHOOK_SECRET'],
            header_name=headers.get('x-webhook-header', 'signature')
        )

        # Validate signature
        validator = WebhookValidator()
        signature = headers.get(config.header_name)

        if not signature:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Missing signature'})
            }

        is_valid = False
        if config.provider == WebhookProvider.STRIPE:
            is_valid = validator.validate_stripe(body, signature, config.secret)
        elif config.provider == WebhookProvider.GITHUB:
            is_valid = validator.validate_github(body, signature, config.secret)
        else:
            is_valid = validator.validate_generic(
                body, signature, config.secret, config.algorithm
            )

        if not is_valid:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid signature'})
            }

        # Parse body
        webhook_data = json.loads(body)

        # Check idempotency
        idempotency = IdempotencyManager('webhook-events')
        event_id = webhook_data.get('id') or webhook_data.get('event_id')

        if await idempotency.check_and_record(event_id):
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Already processed'})
            }

        # Process webhook
        processor = WebhookProcessor(
            queue_url=os.environ['SQS_QUEUE_URL'],
            topic_arn=os.environ['SNS_TOPIC_ARN']
        )

        if config.provider == WebhookProvider.STRIPE:
            result = await processor.process_stripe_event(webhook_data)
        else:
            # Queue for processing
            await processor.queue_message({
                'provider': provider,
                'event': webhook_data
            })
            result = {'queued': True}

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"Webhook processing error: {str(e)}")

        # Return 200 to prevent retries for our errors
        if 'Validation' in str(e):
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'Validation failed'})
            }

        # Return 500 for provider to retry
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Processing failed'})
        }
```

### Example 3: Testing Webhook Handlers

```javascript
// tests/webhook.test.js
const request = require('supertest');
const crypto = require('crypto');
const app = require('../app');
const Redis = require('ioredis-mock');

describe('Webhook Handler Tests', () => {
    let redis;

    beforeEach(() => {
        redis = new Redis();
    });

    describe('Stripe Webhooks', () => {
        const secret = 'whsec_test_secret';

        function generateStripeSignature(payload, secret) {
            const timestamp = Math.floor(Date.now() / 1000);
            const signedPayload = `${timestamp}.${payload}`;
            const signature = crypto
                .createHmac('sha256', secret)
                .update(signedPayload)
                .digest('hex');

            return `t=${timestamp},v1=${signature}`;
        }

        it('should accept valid webhook with correct signature', async () => {
            const payload = JSON.stringify({
                id: 'evt_test_123',
                type: 'payment_intent.succeeded',
                data: {
                    object: {
                        id: 'pi_test_123',
                        amount: 2000,
                        currency: 'usd',
                        metadata: {
                            order_id: 'order_123'
                        }
                    }
                }
            });

            const signature = generateStripeSignature(payload, secret);

            const response = await request(app)
                .post('/webhooks/stripe')
                .set('stripe-signature', signature)
                .set('Content-Type', 'application/json')
                .send(payload)
                .expect(200);

            expect(response.body.received).toBe(true);
            expect(response.body.eventId).toBe('evt_test_123');
        });

        it('should reject webhook with invalid signature', async () => {
            const payload = JSON.stringify({
                id: 'evt_test_123',
                type: 'payment_intent.succeeded'
            });

            await request(app)
                .post('/webhooks/stripe')
                .set('stripe-signature', 'invalid_signature')
                .send(payload)
                .expect(401);
        });

        it('should handle idempotent requests', async () => {
            const payload = JSON.stringify({
                id: 'evt_test_duplicate',
                type: 'payment_intent.succeeded',
                data: { object: { amount: 1000 } }
            });

            const signature = generateStripeSignature(payload, secret);

            // First request
            const response1 = await request(app)
                .post('/webhooks/stripe')
                .set('stripe-signature', signature)
                .send(payload)
                .expect(200);

            // Duplicate request
            const response2 = await request(app)
                .post('/webhooks/stripe')
                .set('stripe-signature', signature)
                .send(payload)
                .expect(200);

            // Both should return same response
            expect(response1.body).toEqual(response2.body);
        });

        it('should reject old timestamps', async () => {
            const oldTimestamp = Math.floor(Date.now() / 1000) - 400; // 6+ minutes old
            const payload = JSON.stringify({
                id: 'evt_old',
                type: 'payment_intent.succeeded'
            });

            const signedPayload = `${oldTimestamp}.${payload}`;
            const signature = crypto
                .createHmac('sha256', secret)
                .update(signedPayload)
                .digest('hex');

            const signatureHeader = `t=${oldTimestamp},v1=${signature}`;

            await request(app)
                .post('/webhooks/stripe')
                .set('stripe-signature', signatureHeader)
                .send(payload)
                .expect(401);
        });
    });

    describe('GitHub Webhooks', () => {
        const secret = 'github_secret';

        function generateGitHubSignature(payload, secret) {
            return 'sha256=' + crypto
                .createHmac('sha256', secret)
                .update(payload)
                .digest('hex');
        }

        it('should process push event', async () => {
            const payload = JSON.stringify({
                ref: 'refs/heads/main',
                repository: {
                    name: 'test-repo',
                    full_name: 'user/test-repo'
                },
                commits: [{
                    id: 'abc123',
                    message: 'Test commit'
                }]
            });

            const signature = generateGitHubSignature(payload, secret);

            const response = await request(app)
                .post('/webhooks/github')
                .set('x-hub-signature-256', signature)
                .set('x-github-event', 'push')
                .send(payload)
                .expect(200);

            expect(response.body.received).toBe(true);
        });
    });

    describe('Rate Limiting', () => {
        it('should rate limit excessive requests', async () => {
            const payload = JSON.stringify({
                id: 'evt_rate_test',
                type: 'test.event'
            });

            const signature = generateStripeSignature(payload, 'test_secret');

            // Make many requests
            const requests = [];
            for (let i = 0; i < 150; i++) {
                requests.push(
                    request(app)
                        .post('/webhooks/stripe')
                        .set('stripe-signature', signature)
                        .send(payload)
                );
            }

            const responses = await Promise.all(requests);
            const rateLimited = responses.filter(r => r.status === 429);

            expect(rateLimited.length).toBeGreaterThan(0);
        });
    });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid signature" | Wrong secret or tampered payload | Verify secret key configuration |
| "Timestamp too old" | Webhook delivered late | Increase tolerance or check delays |
| "Duplicate event" | Webhook retried by provider | Idempotency working correctly |
| "Processing timeout" | Long-running handler | Move to async queue processing |
| "Rate limit exceeded" | Too many webhooks | Increase limits or optimize |

## Configuration Options

**Security Options**
- `signatureAlgorithm`: HMAC-SHA256, HMAC-SHA512
- `timestampTolerance`: Maximum age of webhook (seconds)
- `ipAllowlist`: Restrict to provider IPs
- `rateLimits`: Per-provider rate limiting

**Processing Options**
- `asyncProcessing`: Queue events for background processing
- `retryAttempts`: Number of processing retries
- `deadLetterQueue`: Failed event storage
- `parallelProcessing`: Concurrent event handling

## Best Practices

DO:
- Always verify signatures before processing
- Respond quickly (< 5 seconds) to webhook
- Implement idempotency for all handlers
- Log all webhook events for audit
- Use async processing for heavy operations
- Monitor webhook health and success rates

DON'T:
- Process webhooks synchronously if slow
- Trust webhook data without validation
- Ignore timestamp verification
- Return errors for duplicate events
- Skip rate limiting
- Store sensitive webhook data in logs

## Performance Considerations

- Use connection pooling for database operations
- Queue heavy processing asynchronously
- Implement circuit breakers for downstream services
- Cache frequently accessed data
- Use bulk operations where possible
- Monitor processing latency and queue depth

## Security Considerations

- Always use HTTPS endpoints
- Rotate webhook secrets regularly
- Implement IP allowlisting for critical webhooks
- Never log full webhook payloads with sensitive data
- Use separate secrets per environment
- Monitor for replay attacks
- Implement webhook firewall rules

## Related Commands

- `/api-event-emitter` - Create event systems
- `/api-gateway-builder` - Build API gateways
- `/message-queue-setup` - Configure message queues
- `/serverless-function` - Create Lambda handlers
- `/monitoring-setup` - Add monitoring

## Version History

- v1.0.0 (2024-10): Initial implementation with Stripe, GitHub, Shopify support
- Planned v1.1.0: Add Twilio, SendGrid, and Slack webhook handlers