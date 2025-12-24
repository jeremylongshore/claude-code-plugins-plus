# Make.com Scenario Builder

Create visual Make.com automation scenarios with AI assistance - perfect for no-code automation.

## Why Make.com?

Make.com (formerly Integromat) is a powerful visual automation platform:

-  **Visual Design** - See your entire workflow at a glance
-  **1000+ Integrations** - Connect virtually any app
-  **No-Code** - Build complex automations without coding
-  **Powerful Features** - Routers, filters, error handlers
-  **Affordable** - More cost-effective than Zapier
-  **Scalable** - Handle complex multi-step workflows
- ️ **Built-in Error Handling** - Visual error routes

## FREE Alternative: Use n8n + Ollama (Self-Hosted)

**Want the same power without monthly costs?** Use n8n (self-hosted) + Ollama (local LLM) for $0/month.

### Quick Comparison

| Component | Paid (Make.com) | FREE (n8n + Ollama) |
|-----------|----------------|---------------------|
| **Automation Platform** | Make.com: $9-29/mo | n8n: $0 (self-hosted) |
| **AI Provider** | OpenAI: $30-60/mo | Ollama: $0 (local) |
| **Total Monthly Cost** | **$39-89/mo** | **$0/mo** |
| **Operations Limit** | 10,000/mo | Unlimited |
| **Privacy** | Data sent to Make.com | 100% local |
| **Hosting** | Managed SaaS | Docker/K8s |

**Savings: $468-1,068/year** (enough to buy new hardware!)

### Why n8n + Ollama?

**n8n (Self-Hosted Automation)**:
- Visual workflow builder (same as Make.com)
- 400+ integrations (vs Make's 1000+, but covers 90% of use cases)
- Advanced error handling
- Self-hosted = unlimited operations
- Open-source = community support

**Ollama (Local LLM)**:
- Runs Llama 3.2, Mistral, CodeLlama locally
- No API keys required
- Privacy-first (data never leaves your machine)
- Free forever

### Setup Guide

#### 1. Install n8n (Docker)

```bash
# Create docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3'
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
    volumes:
      - ~/.n8n:/home/node/.n8n
EOF

# Start n8n
docker-compose up -d

# Access at http://localhost:5678
```

#### 2. Install Ollama

```bash
# macOS
brew install ollama
brew services start ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull AI model (4GB download)
ollama pull llama3.2
```

See [ollama-local-ai](../../../ai-ml/ollama-local-ai/) plugin for detailed setup.

#### 3. Connect Ollama to n8n

In n8n, use the **HTTP Request** node:

```json
{
  "method": "POST",
  "url": "http://localhost:11434/api/generate",
  "body": {
    "model": "llama3.2",
    "prompt": "{{ $json.input }}",
    "stream": false
  }
}
```

### Migration Examples

#### Before (Make.com + OpenAI)

**Cost:** $9/mo + $30/mo = **$39/mo**

```
Trigger: Gmail New Email
↓
Action: OpenAI Chat Completion ($0.002/request)
↓
Action: Gmail Send Reply
↓
Action: Google Sheets Add Row
```

#### After (n8n + Ollama)

**Cost:** $0/mo + $0/mo = **$0/mo**

```
Trigger: Gmail New Email (n8n)
↓
HTTP Request: Ollama Chat (localhost:11434)
↓
Action: Gmail Send Reply (n8n)
↓
Action: Google Sheets Add Row (n8n)
```

**Same functionality, zero cost.**

### Real Use Case: AI Email Assistant

#### Make.com + OpenAI Version
- Make.com Core: $9/mo
- OpenAI API: ~$30/mo (1000 emails)
- **Total: $39/mo**

#### n8n + Ollama Version
```javascript
// n8n HTTP Request Node
{
  "method": "POST",
  "url": "http://localhost:11434/api/generate",
  "body": {
    "model": "llama3.2",
    "prompt": "Reply professionally to: {{ $json.emailBody }}",
    "stream": false
  }
}
```
- n8n (self-hosted): $0
- Ollama (local): $0
- **Total: $0/mo**

**Same AI quality, $468/year saved.**

### n8n Workflow Templates

**Available in [n8n-workflow-designer](../../n8n-workflow-designer/) plugin:**
- AI email automation
- Lead scoring & routing
- Content distribution
- Document processing
- Support ticket triage

### Performance Comparison

| Metric | Make.com + OpenAI | n8n + Ollama |
|--------|-------------------|--------------|
| **Response Time** | 2-5s (API latency) | 1-3s (local LLM) |
| **Uptime** | 99.9% (SaaS) | 100% (self-hosted) |
| **Privacy** | Data sent to cloud | 100% local |
| **Operations/month** | 10,000 limit | Unlimited |
| **Cost** | $39-89/mo | $0/mo |

### When to Use Make.com vs n8n

**Use Make.com if:**
- You need 1000+ integrations (vs n8n's 400+)
- You prefer managed hosting (no DevOps)
- Your team is non-technical
- Budget allows $39-89/month

**Use n8n + Ollama if:**
- You want unlimited operations
- You need privacy/compliance (HIPAA, GDPR)
- You have basic Docker skills
- You want to save $468-1,068/year

### Resources

- **n8n Docs:** [docs.n8n.io](https://docs.n8n.io)
- **Ollama Setup:** Use `/setup-ollama` command from [ollama-local-ai](../../../ai-ml/ollama-local-ai/) plugin
- **n8n Workflows:** Install [n8n-workflow-designer](../../n8n-workflow-designer/) plugin
- **Migration Guide:** [n8n vs Make.com](https://docs.n8n.io/integrations/make-to-n8n/)

**Bottom Line:** If you're comfortable with Docker and want to save $468+/year, n8n + Ollama is the superior choice.

---

## Installation

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install make-scenario-builder
```

## Features

### Scenario Design
- **Visual Workflows** - Clear module-by-module design
- **Routers & Filters** - Conditional logic and branching
- **Data Mapping** - Transform data between apps
- **Error Handling** - Graceful failure management
- **Iterators** - Process lists and arrays
- **Aggregators** - Combine multiple items

### AI Integration
- **OpenAI** - Native GPT integration
- **Anthropic Claude** - Via HTTP module
- **Custom AI** - Connect any AI API
- **Prompt Design** - Optimized prompts included

### Module Types
- **Triggers** - Webhooks, scheduled, polling
- **Actions** - Create, update, search, delete
- **Tools** - Router, iterator, aggregator, filter
- **Flow Control** - Delays, repeaters, break

## Commands

| Command | Description |
|---------|-------------|
| `/make` | Generate Make.com scenario design |
| Talk about Make/Integromat | Activates make-expert agent |

## Example Scenarios

### 1. AI Email Assistant
```
Gmail Trigger → OpenAI Response → Send Reply → Log to Sheets
```

**Business Value:** Auto-respond to customer emails
**Cost:** ~$0.02/email (4 operations)
**Setup Time:** 15 minutes

### 2. Lead Qualification
```
Webhook → AI Scoring → Router → [High/Medium/Low] → Actions
```

**Business Value:** Automatically prioritize and route leads
**Cost:** ~$0.04/lead (4-6 operations)
**Setup Time:** 20 minutes

### 3. Content Distribution
```
RSS Feed → AI Rewrite → Iterator → Post to Social Platforms
```

**Business Value:** Automate content sharing across platforms
**Cost:** ~$0.12/post (3 platforms × 4 ops)
**Setup Time:** 25 minutes

### 4. Document Processing
```
Drive Trigger → OCR → AI Extract → Sheets Log → Email Summary
```

**Business Value:** Automate invoice/receipt processing
**Cost:** ~$0.08/document (8 operations)
**Setup Time:** 30 minutes

### 5. Support Automation
```
Ticket Created → AI Classify → Router → Route by Priority
```

**Business Value:** Triage support tickets automatically
**Cost:** ~$0.06/ticket (6 operations)
**Setup Time:** 25 minutes

## Getting Started

### 1. Install the Plugin
```bash
/plugin install make-scenario-builder
```

### 2. Describe Your Scenario
```
I need to automatically process new Google Drive PDFs,
extract data with OCR, and log it to a spreadsheet.
```

### 3. Get Complete Design
The plugin provides:
- Visual workflow diagram
- Module-by-module configuration
- Data mapping instructions
- Error handling setup
- Testing steps
- Cost estimates

### 4. Build in Make
1. Log into [make.com](https://make.com)
2. Create new scenario
3. Add modules as described
4. Configure data mapping
5. Test with sample data
6. Activate scenario

## Make.com Plans

| Plan | Price | Operations | Best For |
|------|-------|------------|----------|
| **Free** | $0 | 1,000/mo | Testing, small projects |
| **Core** | $9/mo | 10,000/mo | Solo entrepreneurs |
| **Pro** | $16/mo | 10,000/mo | Agencies, power users |
| **Teams** | $29/mo | 10,000/mo | Collaboration |

**Operations:** Each module action counts as 1 operation

## Real-World Use Cases

### Agency: Client Onboarding
**Scenario:** New client signup → Create folders → Send contracts → Schedule calls → Update CRM

**Results:**
- Time saved: 3 hours per client
- Setup time: 45 minutes
- ROI: Positive after 1 client

### SaaS: User Activation
**Scenario:** New signup → Welcome email → Monitor usage → Trigger onboarding → Alert sales

**Results:**
- Activation rate: +18%
- Setup time: 1 hour
- Cost: $0.004 per user

### E-commerce: Order Fulfillment
**Scenario:** Order received → Inventory check → Payment processing → Fulfillment → Tracking

**Results:**
- Error reduction: 75%
- Setup time: 2 hours
- Payback: 2 weeks

## Make.com vs Alternatives

| Feature | Make.com | Zapier | n8n |
|---------|----------|--------|-----|
| **Visual Design** |  Excellent | ️ Basic | ️ Good |
| **Integrations** | 1000+ | 5000+ | 200+ |
| **Ease of Use** |  Excellent |  Easy | ️ Moderate |
| **Cost (10K ops)** | $9-16 | $49 | $0 |
| **Error Handling** |  Visual | ️ Limited |  Advanced |
| **Complex Logic** |  Good |  Limited |  Excellent |
| **Self-Hosting** |  No |  No |  Yes |

**Best For:** Visual learners, agencies, businesses wanting managed hosting

## Best Practices

### Design Principles
1. **Start simple** - Build incrementally
2. **Use routers wisely** - Keep logic clear
3. **Add error handlers** - Always plan for failures
4. **Test thoroughly** - Use sample data first
5. **Document scenarios** - Use Notes modules

### Performance Tips
1. **Filter early** - Reduce unnecessary operations
2. **Use aggregators** - Batch API calls
3. **Optimize data mapping** - Only map needed fields
4. **Monitor usage** - Watch operations dashboard
5. **Schedule wisely** - Spread load across time

### Security
1. **Use connections** - Don't hardcode API keys
2. **Validate webhooks** - Verify request sources
3. **Limit data exposure** - Only map necessary fields
4. **Regular audits** - Review scenario permissions
5. **Team management** - Use proper access controls

## Advanced Features

### Routers
Create conditional branches:
```
Input → Router
  ├─ High priority → Immediate action
  ├─ Medium → Queue for later
  └─ Low → Archive
```

### Iterators
Process arrays:
```
Get list of items → Iterator → Process each → Aggregate results
```

### Error Handlers
Graceful failure management:
```
API Call → [Success] → Continue
         → [Error] → Retry → Fallback → Notify
```

### Data Stores
Temporary storage:
```
Store data → Process → Retrieve → Continue workflow
```

## Troubleshooting

### Common Issues

**"Not enough operations"**
- Solution: Upgrade plan or optimize scenario

**"Connection error"**
- Solution: Reauthorize app connection

**"Data mapping error"**
- Solution: Check field names and data types

**"Timeout error"**
- Solution: Reduce batch size or add delays

**"Incomplete execution"**
- Solution: Review error logs and add error handlers

## Requirements

- **Claude Code** >= 1.0.0
- **Make.com account** (free tier available)
- **App connections** for integrated services

## Support & Resources

- **Make.com Documentation:** [make.com/en/help](https://www.make.com/en/help)
- **Make Academy:** Free training courses
- **Community Forum:** [community.make.com](https://community.make.com)
- **Plugin Issues:** [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)

## License

MIT - See LICENSE file

## Contributing

Contributions welcome! Submit PRs with:
- New scenario templates
- Module configurations
- Use case examples
- Documentation improvements

---

**Part of [Claude Code Plugin Hub](https://github.com/jeremylongshore/claude-code-plugins)**

Perfect for agencies and businesses that want powerful automation with a visual, no-code interface.
