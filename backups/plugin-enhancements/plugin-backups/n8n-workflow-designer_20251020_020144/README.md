# n8n Workflow Designer

Design complex n8n workflows with AI assistance - the most powerful open-source automation platform.

## Why n8n?

n8n is the most powerful open-source automation platform available:

-  **Open Source** - Self-host for complete control, no vendor lock-in
-  **Cost Effective** - No per-execution fees, process millions for free
-  **Advanced Logic** - Loops, branching, custom JavaScript code
-  **More Powerful** - More capable than Zapier or Make.com
-  **Extensible** - Create custom nodes, integrate anything
-  **AI-Ready** - Native OpenAI, Anthropic, and LangChain integration
-  **Data Control** - Keep sensitive data on your infrastructure

## Installation

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install n8n-workflow-designer
```

## Features

### Workflow Design Capabilities
- **Complex Branching** - Route data based on conditions
- **Loops & Iterations** - Process batches efficiently
- **Error Handling** - Retry logic and fallback strategies
- **Custom Code** - JavaScript for complex transformations
- **200+ Integrations** - Connect to any service
- **Webhooks** - Trigger workflows from anywhere

### AI Integration
- **OpenAI/GPT-4** - Native node support
- **Anthropic Claude** - Full API integration
- **Custom Models** - Connect any AI service
- **Prompt Templates** - Reusable prompts
- **Response Parsing** - Extract structured data

### Performance Features
- **Batch Processing** - Handle large datasets efficiently
- **Parallel Execution** - Multiple branches run simultaneously
- **Rate Limiting** - Built-in API throttling
- **Caching** - Reduce API calls and costs
- **Resource Management** - Monitor and optimize

## Commands

| Command | Description |
|---------|-------------|
| `/n8n` | Generate complete workflow JSON |
| Talk about workflows | Activates n8n-expert agent automatically |

## Example Workflows

### 1. AI Email Auto-Responder
```
Gmail Trigger → OpenAI Response → Gmail Send → Database Log
```

**Use Case:** Automatically respond to customer inquiries with AI-generated responses

**Cost:** ~$0.02 per email (using GPT-4)

### 2. Content Pipeline
```
RSS Feed → Filter → AI Enhancement → Multi-Platform Publish
```

**Use Case:** Automatically create and distribute content from RSS feeds

**Cost:** ~$0.05 per post (content generation + social media)

### 3. Lead Qualification
```
Form Submit → Data Enrichment → AI Scoring → Route → CRM/Email
```

**Use Case:** Automatically score and route leads based on fit

**Cost:** ~$0.01 per lead (AI scoring only)

### 4. Document Processing
```
Email Trigger → Extract PDF → OCR → AI Analysis → Database → Notify
```

**Use Case:** Process documents with AI and extract structured data

**Cost:** ~$0.10 per document (OCR + AI analysis)

### 5. Customer Support Automation
```
Ticket Created → Classify → Route → AI Draft → Human Review → Send
```

**Use Case:** Triage and draft responses for support tickets

**Cost:** ~$0.03 per ticket (classification + draft)

## Getting Started

### 1. Install the Plugin
```bash
/plugin install n8n-workflow-designer
```

### 2. Describe Your Workflow
```
I need a workflow that monitors my Gmail for support requests,
uses AI to draft responses, and sends them to Slack for approval.
```

### 3. Get Complete Workflow
The plugin generates:
- Visual architecture diagram
- Node-by-node configuration
- Complete importable JSON
- Setup instructions
- Testing checklist
- Cost estimates

### 4. Import to n8n
1. Copy the JSON output
2. Open your n8n instance
3. Click "Import from JSON"
4. Paste and configure credentials
5. Test and activate

## n8n Setup Options

### Cloud (Easiest)
- Visit [n8n.cloud](https://n8n.cloud)
- 5-10 workflows free
- $20/month for standard plan
- Hosted and managed

### Self-Hosted (Most Powerful)
```bash
# Docker Compose
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Benefits:**
- Free for unlimited workflows
- Full control over data
- No execution limits
- Custom nodes
- Better for sensitive data

## Real-World Examples

### Agency Use Case: Client Onboarding
```
Form Submit → Create Folders → Send Contracts → Schedule Kickoff → CRM Update
```

**Time Saved:** 2 hours per client
**Setup Time:** 30 minutes
**ROI:** After 1 client

### SaaS Use Case: User Activation
```
New Signup → Send Welcome → Monitor Usage → Trigger Onboarding → Alert Sales
```

**Conversion Lift:** 15-25%
**Setup Time:** 1 hour
**Cost:** $0.001 per user

### E-commerce Use Case: Order Processing
```
Order Received → Inventory Check → Payment → Fulfillment → Tracking → Follow-up
```

**Error Reduction:** 80%
**Setup Time:** 2 hours
**Payback:** 1 week

## Best Practices

1. **Start Simple** - Build incrementally, test each node
2. **Error Handling** - Always plan for failures
3. **Logging** - Track workflow execution
4. **Version Control** - Export workflows to git
5. **Documentation** - Add notes to complex nodes
6. **Testing** - Use small datasets first
7. **Monitoring** - Watch costs and performance
8. **Security** - Use environment variables for secrets

## Comparison: n8n vs Alternatives

| Feature | n8n | Make.com | Zapier |
|---------|-----|----------|--------|
| **Self-Hosting** |  Free |  Cloud only |  Cloud only |
| **Loops** |  Native | ️ Limited |  No |
| **Custom Code** |  JavaScript | ️ Limited | ️ Limited |
| **Cost (1M ops)** | $0 | $299/mo | $1,899/mo |
| **Open Source** |  Yes |  No |  No |
| **Complex Logic** |  Advanced | ️ Good | ️ Basic |
| **AI Integration** |  Native | ️ Manual | ️ Manual |

**Winner for Agencies:** n8n (cost, flexibility, power)

## Requirements

- **Claude Code** >= 1.0.0
- **n8n instance** (cloud or self-hosted)
- **API credentials** for integrated services

## Support & Resources

- **n8n Documentation:** [docs.n8n.io](https://docs.n8n.io)
- **Community Forum:** [community.n8n.io](https://community.n8n.io)
- **Discord:** Join the n8n Discord
- **Plugin Issues:** [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)

## License

MIT - See LICENSE file

## Contributing

Contributions welcome! Please submit PRs with:
- New workflow templates
- Integration examples
- Performance optimizations
- Documentation improvements

---

**Part of [Claude Code Plugin Hub](https://github.com/jeremylongshore/claude-code-plugins)**

Built for agencies, freelancers, and businesses who need powerful automation without the enterprise price tag.
