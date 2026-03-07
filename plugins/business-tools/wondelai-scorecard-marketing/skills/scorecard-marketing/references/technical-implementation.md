# Scorecard Technical Implementation

Platform comparison, conditional logic patterns, PDF generation, and integration architecture.

## Platform Comparison

### Dedicated Quiz/Scorecard Platforms

| Platform | Best For | Key Features | Limitations |
|----------|----------|--------------|-------------|
| **ScoreApp** | Full scorecard methodology | Built for scorecards, PDF reports, CRM integration | Pricing, learning curve |
| **Typeform** | Beautiful UX, simple quizzes | Great design, logic jumps, integrations | Limited scoring, no native PDF |
| **Outgrow** | Interactive calculators | Calculators, quizzes, polls, good analytics | Can feel template-y |
| **Interact** | Quiz funnels, e-commerce | Personality quizzes, product recommendations | Less suited for B2B scorecards |
| **Bucket.io** | Advanced branching | Complex logic, multiple outcomes | Steeper learning curve |

### Form Builders with Quiz Capabilities

| Platform | Best For | Key Features | Limitations |
|----------|----------|--------------|-------------|
| **Tally** | Simple, free option | Clean UI, logic, calculations | Limited design control |
| **JotForm** | Established forms | Calculations, PDF reports, payments | UI feels dated |
| **Gravity Forms** | WordPress sites | Deep WP integration, add-ons | WordPress only |
| **Cognito Forms** | Calculations + forms | Good calculation engine | Less marketing-focused |

### Custom Development

**When to build custom:**
- Unique scoring logic not supported by platforms
- Deep product integration required
- High volume with cost concerns
- Specific compliance requirements

**Tech stack options:**
- React/Next.js + headless CMS
- Static form with serverless functions
- WordPress + custom plugin
- Low-code (Webflow + integrations)

---

## Scoring Logic Patterns

### Simple Additive Scoring

Each answer adds points to a total.

```javascript
const questions = [
  {
    id: 'q1',
    options: [
      { value: 'never', points: 1 },
      { value: 'sometimes', points: 3 },
      { value: 'always', points: 5 },
    ]
  }
];

function calculateScore(answers) {
  return Object.values(answers).reduce((total, answer) => {
    return total + answer.points;
  }, 0);
}
```

### Category-Based Scoring

Score multiple dimensions separately.

```javascript
const questions = [
  {
    id: 'q1',
    category: 'marketing',
    options: [
      { value: 'a', points: 1 },
      { value: 'b', points: 3 },
      { value: 'c', points: 5 },
    ]
  },
  {
    id: 'q2',
    category: 'operations',
    options: [...]
  }
];

function calculateCategoryScores(answers, questions) {
  const categories = {};

  questions.forEach(q => {
    if (!categories[q.category]) {
      categories[q.category] = { total: 0, max: 0 };
    }

    const answer = answers[q.id];
    const maxPoints = Math.max(...q.options.map(o => o.points));

    categories[q.category].total += answer.points;
    categories[q.category].max += maxPoints;
  });

  // Convert to percentages
  Object.keys(categories).forEach(cat => {
    categories[cat].percentage = Math.round(
      (categories[cat].total / categories[cat].max) * 100
    );
  });

  return categories;
}
```

### Weighted Scoring

Some questions matter more than others.

```javascript
const questions = [
  {
    id: 'q1',
    weight: 2,  // Double importance
    options: [...]
  },
  {
    id: 'q2',
    weight: 1,  // Normal importance
    options: [...]
  }
];

function calculateWeightedScore(answers, questions) {
  let weightedTotal = 0;
  let maxWeightedTotal = 0;

  questions.forEach(q => {
    const answer = answers[q.id];
    const maxPoints = Math.max(...q.options.map(o => o.points));

    weightedTotal += answer.points * q.weight;
    maxWeightedTotal += maxPoints * q.weight;
  });

  return Math.round((weightedTotal / maxWeightedTotal) * 100);
}
```

### Tier Assignment

Map scores to meaningful tiers.

```javascript
function getTier(score) {
  if (score >= 80) return { name: 'Advanced', level: 3 };
  if (score >= 50) return { name: 'Intermediate', level: 2 };
  return { name: 'Beginner', level: 1 };
}

// Category-specific tiers
function getCategoryTier(categoryScore) {
  const tiers = {
    marketing: [
      { min: 0, max: 40, name: 'Foundation' },
      { min: 41, max: 70, name: 'Growing' },
      { min: 71, max: 100, name: 'Optimized' },
    ],
    // Different tiers per category if needed
  };

  return tiers[category].find(t =>
    categoryScore >= t.min && categoryScore <= t.max
  );
}
```

---

## Conditional Logic Patterns

### Question Branching

Show different questions based on previous answers.

```javascript
const questions = [
  {
    id: 'business_type',
    text: 'What type of business are you?',
    options: ['B2B', 'B2C', 'Both']
  },
  {
    id: 'b2b_sales',
    text: 'How long is your typical sales cycle?',
    showIf: { business_type: ['B2B', 'Both'] }
  },
  {
    id: 'b2c_volume',
    text: 'How many customers do you serve monthly?',
    showIf: { business_type: ['B2C', 'Both'] }
  }
];

function shouldShowQuestion(question, answers) {
  if (!question.showIf) return true;

  return Object.entries(question.showIf).every(([questionId, validValues]) => {
    const answer = answers[questionId];
    return validValues.includes(answer);
  });
}
```

### Dynamic Results

Show different content based on score patterns.

```javascript
const resultContent = {
  overall: {
    low: {
      headline: "You're just getting started",
      description: "Focus on fundamentals first...",
      cta: { text: "Get our beginner guide", url: "/guide" }
    },
    medium: {
      headline: "You have solid foundations",
      description: "Time to optimize and scale...",
      cta: { text: "Book a strategy call", url: "/call" }
    },
    high: {
      headline: "You're operating at high level",
      description: "Let's fine-tune for excellence...",
      cta: { text: "Explore advanced services", url: "/premium" }
    }
  },
  categories: {
    marketing: {
      low: "Your marketing needs attention. Start with...",
      medium: "Your marketing is working. Next step...",
      high: "Your marketing is strong. Consider..."
    }
  }
};

function getResultContent(scores) {
  const tier = scores.overall < 40 ? 'low' :
               scores.overall < 70 ? 'medium' : 'high';

  return {
    overall: resultContent.overall[tier],
    categories: Object.entries(scores.categories).map(([cat, score]) => ({
      category: cat,
      content: resultContent.categories[cat][getTier(score)]
    }))
  };
}
```

---

## PDF Report Generation

### Server-Side Generation

**Popular options:**

| Tool | Language | Best For |
|------|----------|----------|
| Puppeteer | Node.js | HTML-to-PDF, complex layouts |
| PDFKit | Node.js | Programmatic PDF creation |
| WeasyPrint | Python | CSS-based PDF |
| wkhtmltopdf | CLI | Simple HTML-to-PDF |
| React-pdf | Node.js/React | React-based templates |

### Puppeteer Example

```javascript
const puppeteer = require('puppeteer');

async function generatePDF(data) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Load HTML template with data
  const html = renderTemplate('report.html', data);
  await page.setContent(html, { waitUntil: 'networkidle0' });

  // Generate PDF
  const pdf = await page.pdf({
    format: 'A4',
    printBackground: true,
    margin: { top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' }
  });

  await browser.close();
  return pdf;
}
```

### PDF Content Structure

```html
<!-- Page 1: Cover -->
<div class="page cover">
  <img src="logo.png" />
  <h1>Your Scorecard Results</h1>
  <p>Prepared for: {{ name }}</p>
  <p>Date: {{ date }}</p>
</div>

<!-- Page 2: Overall Score -->
<div class="page">
  <h2>Overall Score: {{ overallScore }}%</h2>
  <div class="score-gauge"><!-- Visual gauge --></div>
  <p>{{ overallInterpretation }}</p>
</div>

<!-- Page 3+: Category Details -->
{{ for category in categories }}
<div class="page">
  <h2>{{ category.name }}: {{ category.score }}%</h2>
  <p>{{ category.interpretation }}</p>
  <h3>Recommendations:</h3>
  <ul>
    {{ for rec in category.recommendations }}
    <li>{{ rec }}</li>
    {{ endfor }}
  </ul>
</div>
{{ endfor }}

<!-- Final Page: Next Steps -->
<div class="page">
  <h2>Your Next Steps</h2>
  <ol>
    {{ for step in nextSteps }}
    <li>{{ step }}</li>
    {{ endfor }}
  </ol>
  <div class="cta">
    <p>Ready to improve your score?</p>
    <p>Book a call: {{ ctaUrl }}</p>
  </div>
</div>
```

### Third-Party PDF Services

If building is too complex:
- **PDF.co** - API-based PDF generation
- **DocRaptor** - HTML-to-PDF API
- **Anvil** - PDF filling and generation

---

## Integration Architecture

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Landing   │────▶│   Quiz      │────▶│   Results   │
│    Page     │     │   Form      │     │    Page     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Lead     │     │     PDF     │
                    │   Capture   │     │  Generation │
                    └─────────────┘     └─────────────┘
                           │                    │
              ┌────────────┴────────────┬───────┘
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │     CRM     │          │    Email    │
       │  (HubSpot,  │          │   Service   │
       │ Salesforce) │          │  (Mailchimp)│
       └─────────────┘          └─────────────┘
```

### Webhook Integration

```javascript
// On quiz completion
async function handleQuizComplete(data) {
  const { answers, scores, contact } = data;

  // 1. Generate PDF
  const pdf = await generatePDF({ scores, contact });
  const pdfUrl = await uploadPDF(pdf, contact.email);

  // 2. Send to CRM
  await crmClient.createContact({
    email: contact.email,
    name: contact.name,
    properties: {
      scorecard_overall: scores.overall,
      scorecard_tier: scores.tier,
      scorecard_pdf: pdfUrl,
      ...formatCategoryScores(scores.categories)
    }
  });

  // 3. Send email with results
  await emailClient.send({
    to: contact.email,
    template: 'scorecard-results',
    data: {
      name: contact.name,
      scores,
      pdfUrl
    }
  });

  // 4. Track analytics
  await analytics.track('scorecard_completed', {
    tier: scores.tier,
    overall_score: scores.overall
  });
}
```

### Zapier/Make Integration

For no-code connections:

**Trigger:** Webhook when quiz completes
**Actions:**
1. Add row to Google Sheet (backup)
2. Create/update HubSpot contact
3. Send email via Mailchimp
4. Post to Slack (for high scores)

---

## Performance Optimization

### Fast Loading

```javascript
// Lazy load questions
const [visibleQuestions, setVisibleQuestions] = useState(
  questions.slice(0, 3)
);

// Preload next questions
useEffect(() => {
  const nextIndex = visibleQuestions.length;
  if (nextIndex < questions.length) {
    // Preload next 2 questions
    const nextQuestions = questions.slice(nextIndex, nextIndex + 2);
    preloadImages(nextQuestions);
  }
}, [visibleQuestions]);
```

### Progress Persistence

```javascript
// Save progress to localStorage
function saveProgress(answers) {
  localStorage.setItem('quiz_progress', JSON.stringify({
    answers,
    timestamp: Date.now()
  }));
}

// Restore on page load
function loadProgress() {
  const saved = localStorage.getItem('quiz_progress');
  if (saved) {
    const { answers, timestamp } = JSON.parse(saved);
    // Only restore if less than 24 hours old
    if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
      return answers;
    }
  }
  return null;
}
```

### Abandonment Recovery

```javascript
// Capture email early
const emailCaptureAt = 3; // After question 3

// On abandonment
window.addEventListener('beforeunload', () => {
  if (currentQuestion > emailCaptureAt && email) {
    // Trigger abandonment workflow
    navigator.sendBeacon('/api/quiz-abandoned', JSON.stringify({
      email,
      progress: answers,
      lastQuestion: currentQuestion
    }));
  }
});
```

---

## Security Considerations

### Data Protection

```javascript
// Don't store sensitive answers client-side
const sensitiveFields = ['revenue', 'employee_count'];

function sanitizeForStorage(answers) {
  return Object.fromEntries(
    Object.entries(answers).filter(
      ([key]) => !sensitiveFields.includes(key)
    )
  );
}
```

### Rate Limiting

```javascript
// Prevent spam submissions
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 submissions per window
  message: 'Too many submissions, please try again later'
});

app.post('/api/submit-quiz', rateLimiter, handleSubmit);
```

### Validation

```javascript
// Server-side validation
function validateSubmission(data) {
  const errors = [];

  // Required fields
  if (!data.email || !isValidEmail(data.email)) {
    errors.push('Valid email required');
  }

  // Answer validation
  questions.forEach(q => {
    const answer = data.answers[q.id];
    if (!q.options.some(o => o.value === answer)) {
      errors.push(`Invalid answer for ${q.id}`);
    }
  });

  return errors;
}
```
