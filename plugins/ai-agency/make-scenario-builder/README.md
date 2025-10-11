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
