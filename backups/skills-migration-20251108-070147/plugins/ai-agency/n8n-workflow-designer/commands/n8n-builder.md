---
description: Generate complete n8n workflow JSON files
---

# n8n Workflow Builder

Generate production-ready n8n workflow JSON files.

## Usage

When the user requests an n8n workflow, analyze their requirements and create a complete, importable workflow JSON file.

## Workflow Templates

### 1. AI Email Responder
```json
{
  "name": "AI Email Auto-Responder",
  "nodes": [
    {
      "parameters": {
        "pollTimes": {
          "item": [
            {
              "mode": "everyMinute"
            }
          ]
        },
        "simple": true,
        "filters": {
          "labelIds": ["INBOX"]
        }
      },
      "id": "1",
      "name": "Gmail Trigger",
      "type": "n8n-nodes-base.gmailTrigger",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "messages": {
          "values": [
            {
              "content": "=Draft a professional response to this email:\n\nFrom: {{ $json.from }}\nSubject: {{ $json.subject }}\nBody: {{ $json.body }}\n\nWrite a helpful, friendly response."
            }
          ]
        }
      },
      "id": "2",
      "name": "OpenAI",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1,
      "position": [450, 300],
      "credentials": {
        "openAiApi": {
          "id": "1",
          "name": "OpenAI API"
        }
      }
    },
    {
      "parameters": {
        "sendTo": "={{ $('Gmail Trigger').item.json.from }}",
        "subject": "=Re: {{ $('Gmail Trigger').item.json.subject }}",
        "message": "={{ $json.output }}",
        "options": {}
      },
      "id": "3",
      "name": "Gmail Send",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2,
      "position": [650, 300],
      "credentials": {
        "gmailOAuth2": {
          "id": "1",
          "name": "Gmail OAuth2"
        }
      }
    }
  ],
  "connections": {
    "Gmail Trigger": {
      "main": [
        [
          {
            "node": "OpenAI",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "OpenAI": {
      "main": [
        [
          {
            "node": "Gmail Send",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 2. Data Processing Pipeline
```json
{
  "name": "CSV to Database with AI Enhancement",
  "nodes": [
    {
      "parameters": {
        "fileFormat": "csv",
        "options": {}
      },
      "id": "1",
      "name": "Read CSV",
      "type": "n8n-nodes-base.spreadsheetFile",
      "typeVersion": 2,
      "position": [250, 300]
    },
    {
      "parameters": {
        "batchSize": 10,
        "options": {}
      },
      "id": "2",
      "name": "Loop Over Items",
      "type": "n8n-nodes-base.splitInBatches",
      "typeVersion": 3,
      "position": [450, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "messages": {
          "values": [
            {
              "content": "=Enhance this data record with additional context:\n{{ JSON.stringify($json) }}"
            }
          ]
        }
      },
      "id": "3",
      "name": "AI Enhancement",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "operation": "insert",
        "schema": {
          "__rl": true,
          "value": "public",
          "mode": "list"
        },
        "table": {
          "__rl": true,
          "value": "records",
          "mode": "list"
        },
        "columns": {
          "mappingMode": "autoMapInputData",
          "value": {}
        },
        "options": {}
      },
      "id": "4",
      "name": "PostgreSQL Insert",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.4,
      "position": [850, 300]
    }
  ],
  "connections": {
    "Read CSV": {
      "main": [
        [
          {
            "node": "Loop Over Items",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Loop Over Items": {
      "main": [
        [
          {
            "node": "AI Enhancement",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "AI Enhancement": {
      "main": [
        [
          {
            "node": "PostgreSQL Insert",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 3. Content Pipeline
```json
{
  "name": "RSS to Social Media with AI",
  "nodes": [
    {
      "parameters": {
        "url": "https://example.com/feed.xml",
        "options": {}
      },
      "id": "1",
      "name": "RSS Feed",
      "type": "n8n-nodes-base.rssFeedRead",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "conditions": {
          "dateTime": [
            {
              "value1": "={{ $json.pubDate }}",
              "operation": "after",
              "value2": "={{ $now.minus({ hours: 24 }) }}"
            }
          ]
        }
      },
      "id": "2",
      "name": "Filter New Items",
      "type": "n8n-nodes-base.filter",
      "typeVersion": 2,
      "position": [450, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "messages": {
          "values": [
            {
              "content": "=Create a compelling social media post from this article:\n\nTitle: {{ $json.title }}\nSummary: {{ $json.contentSnippet }}\n\nMake it engaging and include relevant hashtags."
            }
          ]
        }
      },
      "id": "3",
      "name": "Generate Post",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "text": "={{ $json.output }}",
        "additionalFields": {}
      },
      "id": "4",
      "name": "Twitter Post",
      "type": "n8n-nodes-base.twitter",
      "typeVersion": 2,
      "position": [850, 300]
    }
  ],
  "connections": {
    "RSS Feed": {
      "main": [
        [
          {
            "node": "Filter New Items",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Filter New Items": {
      "main": [
        [
          {
            "node": "Generate Post",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Generate Post": {
      "main": [
        [
          {
            "node": "Twitter Post",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 4. Lead Qualification
```json
{
  "name": "Lead Scoring and Routing",
  "nodes": [
    {
      "parameters": {
        "path": "lead-webhook",
        "options": {}
      },
      "id": "1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300]
    },
    {
      "parameters": {
        "model": "gpt-4",
        "messages": {
          "values": [
            {
              "content": "=Score this lead from 0-100 based on fit:\n\nCompany: {{ $json.company }}\nRole: {{ $json.role }}\nIndustry: {{ $json.industry }}\nBudget: {{ $json.budget }}\n\nProvide score and reasoning."
            }
          ]
        }
      },
      "id": "2",
      "name": "AI Score",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.score }}",
              "operation": "larger",
              "value2": 70
            }
          ]
        }
      },
      "id": "3",
      "name": "IF High Score",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [650, 300]
    },
    {
      "parameters": {
        "resource": "deal",
        "operation": "create"
      },
      "id": "4",
      "name": "Create CRM Deal",
      "type": "n8n-nodes-base.hubspot",
      "typeVersion": 2,
      "position": [850, 250]
    },
    {
      "parameters": {
        "resource": "email",
        "operation": "send",
        "subject": "New Lead Follow Up",
        "message": "={{ $json.reasoning }}"
      },
      "id": "5",
      "name": "Nurture Email",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2,
      "position": [850, 350]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "AI Score",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "AI Score": {
      "main": [
        [
          {
            "node": "IF High Score",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "IF High Score": {
      "main": [
        [
          {
            "node": "Create CRM Deal",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Nurture Email",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Features

- Complex branching logic
- Loops and iterations
- Error handling and retries
- Custom code nodes
- 200+ integrations
- Self-hostable
- AI model integration
- Database operations
- API calls and webhooks

## Best Practices

1. **Always add error handling** - Use error workflows or try-catch nodes
2. **Test with small datasets first** - Validate before processing large volumes
3. **Use environment variables for secrets** - Never hardcode API keys
4. **Implement logging for debugging** - Add notes or database logging
5. **Version control your workflows** - Export and commit to git
6. **Monitor resource usage** - Watch execution times and API costs
7. **Use descriptive node names** - Make workflows self-documenting
8. **Implement rate limiting** - Respect API limits with Wait nodes
9. **Batch processing for scale** - Use Split in Batches for large datasets
10. **Regular backups** - Export workflows regularly

## Output Format

When generating a workflow, provide:

1. **Workflow Name** - Clear, descriptive name
2. **Architecture Diagram** - Visual flow of nodes
3. **Complete JSON** - Importable workflow file
4. **Setup Instructions** - Credentials, settings needed
5. **Testing Steps** - How to validate the workflow
6. **Deployment Notes** - Self-hosted vs cloud considerations
7. **Cost Estimation** - Expected API and resource costs

## Example Response

```markdown
# Workflow: AI Customer Support Automation

## Architecture
```
Ticket Created → Classify (AI) → Route by Priority → Draft Response (AI) → Human Review → Send
```

## Nodes
1. Webhook trigger for new tickets
2. OpenAI classification
3. IF node for routing
4. OpenAI response generation
5. Slack notification for review
6. Email send on approval

## Setup
1. Create webhook in your ticketing system
2. Add OpenAI API credentials
3. Configure Slack webhook
4. Set up email credentials
5. Test with sample ticket

## JSON
[Complete importable JSON here]

## Testing
- Send test ticket through webhook
- Verify classification accuracy
- Check routing logic
- Review AI-generated responses
- Test Slack notifications

## Cost Estimate
- ~$0.01 per ticket (GPT-4 usage)
- Self-hosted n8n: Free (Docker)
- Cloud n8n: $20/month (standard plan)
```

This workflow builder helps users create production-ready n8n automations with AI integration, error handling, and best practices built in.
