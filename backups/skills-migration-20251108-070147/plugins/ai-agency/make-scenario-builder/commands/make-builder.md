---
description: Design Make.com scenarios with AI assistance
---

# Make.com Scenario Builder

Create visual Make.com automation scenarios with detailed module configuration.

## Usage

When the user requests a Make.com scenario, design a complete visual workflow with module-by-module instructions.

## Scenario Templates

### 1. AI Email Auto-Responder

**Flow:**
```
Gmail: Watch emails
  → OpenAI: Generate response
  → Gmail: Send email
  → Google Sheets: Log conversation
```

**Module Configuration:**

1. **Gmail: Watch emails**
   - Connection: Your Gmail
   - Folder: INBOX
   - Criteria: Unread messages
   - Max results: 10

2. **OpenAI: Create completion**
   - Connection: Your OpenAI API
   - Model: gpt-4
   - Max tokens: 500
   - Temperature: 0.7
   - Prompt: `Draft a professional response to:\n\nFrom: {{1.from}}\nSubject: {{1.subject}}\nBody: {{1.textPlain}}`

3. **Gmail: Send an email**
   - To: `{{1.from}}`
   - Subject: `Re: {{1.subject}}`
   - Content: `{{2.choices[0].message.content}}`

4. **Google Sheets: Add a row**
   - Spreadsheet: Email Log
   - Sheet: Responses
   - From: `{{1.from}}`
   - Subject: `{{1.subject}}`
   - Response: `{{2.choices[0].message.content}}`
   - Date: `{{now}}`

### 2. Lead Qualification with AI

**Flow:**
```
Webhook: Custom webhook
  → OpenAI: Score lead
  → Router:
     ├─ High score → Slack notification + HubSpot deal
     ├─ Medium score → Email nurture
     └─ Low score → Archive to Airtable
```

**Module Configuration:**

1. **Webhook**
   - Create a custom webhook
   - Expected data: name, email, company, role, budget

2. **OpenAI: Create completion**
   - Prompt: `Score this lead from 0-100:\nName: {{1.name}}\nCompany: {{1.company}}\nRole: {{1.role}}\nBudget: {{1.budget}}\n\nProvide only the numeric score.`
   - Parse: Use Text parser to extract number

3. **Router**
   - Route 1 Filter: `{{3.score}}` Greater than `70`
   - Route 2 Filter: `{{3.score}}` Between `40` and `70`
   - Fallback: All other cases

4A. **Slack: Create a message** (High route)
   - Channel: #sales-leads
   - Text: ` Hot lead: {{1.name}} from {{1.company}} - Score: {{3.score}}`

4B. **HubSpot: Create a deal** (High route)
   - Deal name: `{{1.company}} - {{1.name}}`
   - Stage: Qualification
   - Amount: `{{1.budget}}`

5. **ActiveCampaign: Add contact to list** (Medium route)
   - Email: `{{1.email}}`
   - List: Nurture Campaign
   - Tags: `medium-priority,{{1.role}}`

6. **Airtable: Create a record** (Low route)
   - Base: Leads
   - Table: Archived
   - Fields: Map all lead data + score

### 3. Content Distribution Pipeline

**Flow:**
```
RSS: Read feed
  → Filter: New items only
  → OpenAI: Rewrite for social
  → Iterator: For each platform
     ├─ Twitter: Post
     ├─ LinkedIn: Post
     └─ Facebook: Post
```

**Module Configuration:**

1. **RSS: Watch RSS feed items**
   - URL: Your RSS feed
   - Maximum number of returned items: 5

2. **Filter**
   - Condition: `{{1.published}}` After `{{addHours(now; -24)}}`
   - Label: "Only items from last 24 hours"

3. **OpenAI: Create completion**
   - Prompt: `Rewrite this article for social media (280 chars max):\n\nTitle: {{1.title}}\nContent: {{1.contentSnippet}}\n\nMake it engaging with relevant hashtags.`

4. **Set multiple variables**
   - platforms: `["twitter", "linkedin", "facebook"]`
   - content: `{{3.choices[0].message.content}}`
   - link: `{{1.link}}`

5. **Iterator**
   - Array: `{{4.platforms}}`

6A. **Twitter: Create a tweet**
   - Text: `{{4.content}}\n\n{{4.link}}`

6B. **LinkedIn: Create a post**
   - Text: `{{4.content}}\n\n{{4.link}}`

6C. **Facebook: Create a post**
   - Message: `{{4.content}}`
   - Link: `{{4.link}}`

### 4. Document Processing Workflow

**Flow:**
```
Google Drive: Watch files
  → Filter: PDFs only
  → OCR.space: Extract text
  → OpenAI: Summarize & extract data
  → Router:
     ├─ Success → Google Sheets: Log + Email summary
     └─ Error → Slack: Notify failure
```

**Module Configuration:**

1. **Google Drive: Watch files**
   - Folder: Inbox
   - Types: application/pdf
   - Limit: 10

2. **Filter**
   - Condition: File name contains "invoice" OR "receipt"

3. **HTTP: Make a request (OCR.space)**
   - URL: https://api.ocr.space/parse/image
   - Method: POST
   - Headers: apikey: YOUR_OCR_KEY
   - Body: file: `{{1.data}}`

4. **OpenAI: Create completion**
   - Prompt: `Extract structured data from this document:\n\n{{3.ParsedResults[0].ParsedText}}\n\nProvide: Date, Amount, Vendor, Category`
   - Format: JSON mode

5. **Google Sheets: Add a row**
   - Spreadsheet: Document Log
   - Date: `{{4.date}}`
   - Amount: `{{4.amount}}`
   - Vendor: `{{4.vendor}}`
   - Category: `{{4.category}}`

6. **Gmail: Send an email**
   - To: accounting@company.com
   - Subject: New document processed: `{{1.name}}`
   - Body: Summary of extracted data

**Error Handler on all modules:**
- Slack: Send message to #errors channel

### 5. Customer Support Automation

**Flow:**
```
Zendesk: Watch tickets
  → OpenAI: Classify urgency + category
  → Router:
     ├─ Urgent → Assign to senior agent + Slack alert
     ├─ Normal → Assign to queue + Draft response
     └─ Low → Auto-respond with KB articles
```

**Module Configuration:**

1. **Zendesk: Watch tickets**
   - Status: new
   - Limit: 20

2. **OpenAI: Create completion**
   - Prompt: `Classify this support ticket:\n\nSubject: {{1.subject}}\nDescription: {{1.description}}\n\nProvide:\n1. Urgency (high/medium/low)\n2. Category (billing/technical/general)\n3. Suggested response`

3. **Router**
   - Route 1: Urgency = "high"
   - Route 2: Urgency = "medium"
   - Route 3: Urgency = "low"

4A. **Zendesk: Update ticket** (Urgent)
   - Priority: urgent
   - Assignee: Senior agent ID

4B. **Slack: Create message** (Urgent)
   - Channel: #support-urgent
   - Text: ` Urgent ticket: {{1.subject}} - {{1.ticket_id}}`

5. **Zendesk: Update ticket** (Normal)
   - Priority: normal
   - Comment: `{{2.suggested_response}}`
   - Status: pending

6. **Zendesk: Update ticket** (Low)
   - Comment: Auto-generated response + KB links
   - Status: solved

## Best Practices

1. **Always add error handlers** to critical modules
2. **Use filters early** to reduce operations
3. **Test with sample data** before activating
4. **Monitor operations usage** in Make dashboard
5. **Add notes to modules** for documentation
6. **Use variables** for reusable values
7. **Set up notifications** for failures
8. **Clone scenarios** before major changes

## Output Format

When generating a scenario, provide:

```markdown
## Scenario: [Name]

### Business Value
[What problem this solves]

### Visual Flow
[ASCII diagram or clear description]

### Module Configuration
[Detailed setup for each module]

### Data Mapping
[How data flows between modules]

### Testing Steps
1. [Step by step testing instructions]

### Cost Estimate
- Operations per execution: X
- Expected monthly runs: Y
- Total operations: Z
- Make plan needed: [Free/Core/Pro]

### Setup Time
Estimated: [X] minutes
```

This helps users implement Make.com scenarios quickly with clear, actionable instructions.
