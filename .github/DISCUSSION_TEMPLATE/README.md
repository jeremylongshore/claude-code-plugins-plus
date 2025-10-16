# GitHub Discussion Templates

This directory contains templates for structured GitHub Discussions in the claude-code-plugins repository.

## Available Templates

### 1. Plugin Pack Request (`plugin-pack-request.yml`)

**Purpose:** Request new plugin packs that bundle multiple related plugins (Agents, Skills, Commands, Hooks, MCP servers).

**When to Use:**
- You need a collection of plugins for a specific workflow (e.g., ML Engineering, Finance, Content Creation)
- You want to request Agent Skills that auto-activate based on context
- You have a use case that requires multiple integrated plugins

**What's Included:**
- Pack name and description
- Use case and target audience
- Specific Agent Skills, Subagents, Commands requested
- Example workflows
- Integration requirements
- Security considerations
- Contribution offers

**Examples of Existing Packs:**
- **DevOps Automation Pack** - 25 plugins for git, CI/CD, Docker, Kubernetes, Terraform
- **Security Pro Pack** - 10 plugins for OWASP, compliance, cryptography
- **Skills Powerkit** - Meta-plugin with 5 Agent Skills for plugin management

## How to Use Discussion Templates

### For Users (Requesting Plugin Packs)

1. **Navigate to Discussions**
   - Go to: https://github.com/jeremylongshore/claude-code-plugins/discussions

2. **Start New Discussion**
   - Click "New discussion"
   - Select **"Plugin Pack Request"** category
   - Template will auto-populate

3. **Fill Out Template**
   - Provide clear use cases and workflows
   - Be specific about Agent Skills vs Commands vs Subagents
   - Explain who benefits and why
   - Estimate time savings

4. **Submit & Engage**
   - Submit discussion
   - Respond to questions
   - Collaborate with community
   - Offer to help if able

### For Maintainers (Processing Requests)

1. **Review Incoming Requests**
   - Check feasibility and scope
   - Assess community interest (+1s, comments)
   - Evaluate alignment with marketplace goals

2. **Label Appropriately**
   - `plugin-pack-request` (auto-applied)
   - `enhancement` (auto-applied)
   - `community-request` (auto-applied)
   - Add: `accepted`, `in-design`, `needs-more-info`, `wont-do` as needed

3. **Respond to Requester**
   - Ask clarifying questions
   - Suggest scope adjustments
   - Invite collaboration
   - Set expectations on timeline

4. **If Accepted**
   - Create design document
   - Break down into tasks
   - Coordinate contributors
   - Track progress

## Plugin Pack Request Lifecycle

```
Request Submitted
       ↓
Community Discussion (Feedback, +1s, suggestions)
       ↓
Feasibility Review (Maintainers assess scope)
       ↓
   ┌───┴───┐
   ↓       ↓
Accepted   Declined (with explanation)
   ↓
Design Phase (Create design doc)
   ↓
Implementation (Community or maintainers build)
   ↓
Beta Testing (Early users provide feedback)
   ↓
Official Release 🎉
```

**Typical Timeline:**
- Small packs (3-5 plugins): 2-3 weeks
- Medium packs (6-12 plugins): 3-5 weeks
- Large packs (13-25 plugins): 5-6 weeks
- Meta-plugins: 4-8 weeks

**Factors Affecting Timeline:**
- Complexity of Agent Skills
- Need for MCP servers (real code)
- Integration requirements
- Community contributor availability

## Agent Skills vs Commands vs Subagents

### Agent Skills (Model-Invoked)
- **Activation:** Automatic based on conversation context
- **Example:** Say "clean my data" → Data Cleaner skill activates
- **Best For:** Workflows you do frequently
- **Template Section:** "Agent Skills Requested"

### Slash Commands (User-Invoked)
- **Activation:** Explicit `/command` syntax
- **Example:** `/train-model xgboost mydata.csv`
- **Best For:** Scaffolding, templates, one-time operations
- **Template Section:** "Slash Commands Requested"

### Subagents (Domain Experts)
- **Activation:** Explicit invocation or context
- **Example:** "Ask the PyTorch Expert how to optimize this model"
- **Best For:** Deep domain expertise, Q&A, complex debugging
- **Template Section:** "Subagents Requested"

## Tips for Great Plugin Pack Requests

### ✅ Do This

1. **Be Specific About Workflows**
   - Describe step-by-step what you want to accomplish
   - Show "before/after" time comparisons
   - Give concrete examples

2. **Explain the "Why"**
   - What problem does this solve?
   - Who benefits?
   - Why existing tools aren't sufficient

3. **Differentiate Component Types**
   - Be clear: do you want Skills (auto-activate) or Commands (explicit)?
   - Specify trigger keywords for Skills
   - Define parameters for Commands

4. **Offer to Help**
   - Testing, documentation, use case examples
   - Even small contributions speed up delivery

5. **Research Similar Tools**
   - Mention existing plugins/tools you like
   - Explain what's missing
   - Show you understand the space

### ❌ Avoid This

1. **Vague Requests**
   - ❌ "I need AI plugins"
   - ✅ "I need ML model training automation with experiment tracking"

2. **Requesting Everything**
   - ❌ "100 plugins for every possible use case"
   - ✅ "10-12 focused plugins for my core data science workflow"

3. **No Use Cases**
   - ❌ Just listing plugin names
   - ✅ Describing workflows: "First I do X, then Y, then Z"

4. **No Context on Audience**
   - ❌ "Everyone needs this"
   - ✅ "Intermediate ML engineers working with PyTorch"

5. **Unrealistic Timelines**
   - ❌ "Need this in 2 days"
   - ✅ "Willing to wait 4-6 weeks, happy to test beta"

## Example: Great Plugin Pack Request

```yaml
Pack Name: ML Engineering Pack

Use Case:
I'm a data scientist who spends 60% of my time on repetitive ML tasks:
data cleaning, experiment tracking, model training, deployment config.
I want to automate these workflows so I can focus on research.

Agent Skills Requested:
1. Data Cleaner - Auto-handles missing values, outliers, type conversion
   Triggers: "clean data", "handle missing values", "preprocess dataset"

2. Experiment Tracker - Auto-logs hyperparameters, metrics, artifacts
   Triggers: "track experiment", "log results", "save metrics"

3. Model Trainer - Auto-scaffolds training loops with best practices
   Triggers: "train model", "fit model", "start training"

Commands Requested:
1. /deploy-model - Creates deployment config (Docker, FastAPI endpoint)
2. /experiment - Sets up MLflow experiment with logging boilerplate
3. /compare-models - Generates comparison table of model performance

Workflows:
Workflow 1: Experiment Pipeline
1. Load data, say "clean dataset" → Data Cleaner activates
2. Say "train XGBoost model" → Model Trainer scaffolds code
3. Say "track this experiment" → Experiment Tracker logs everything
4. /compare-models → Generates comparison table
5. /deploy-model best_model.pkl → Creates deployment config

Time Savings: 2-3 hours/day (currently manual)

Target Audience: Data Scientists / ML Engineers (intermediate level)

Contribution: I can help test and provide real-world examples
```

**Why This Is Great:**
- ✅ Specific workflows
- ✅ Clear time savings
- ✅ Differentiates Skills vs Commands
- ✅ Trigger keywords provided
- ✅ Realistic scope
- ✅ Offers to help

## Community Guidelines

### For Requesters

- **Be Patient:** Community-driven = no guaranteed timelines
- **Be Open:** Accept feedback and iteration
- **Be Collaborative:** Offer to help where you can
- **Be Realistic:** Understand scope and complexity

### For Maintainers

- **Be Responsive:** Acknowledge requests within 48 hours
- **Be Transparent:** Explain feasibility and priorities
- **Be Inclusive:** Welcome all contributors
- **Be Supportive:** Guide requesters through the process

## Getting Help

- **Questions?** Ask in [Discussions Q&A](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/q-a)
- **Feedback?** Share in [Discussions General](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/general)
- **Issues?** Report in [Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)

---

**Let's build amazing plugin packs together!** 🚀
