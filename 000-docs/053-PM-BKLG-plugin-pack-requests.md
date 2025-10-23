# Plugin Pack Requests Guide

**Want a custom plugin pack built for your workflow?** Submit a plugin pack request and the community will help build it!

---

## What Are Plugin Packs?

**Plugin packs** are curated collections of related plugins that work together for specific workflows.

### Existing Plugin Packs

| Pack Name | Plugins | Components | Install |
|-----------|---------|------------|---------|
| **DevOps Automation Pack** | 25 | 20 commands, 5 agents | `/plugin install devops-automation-pack@claude-code-plugins-plus` |
| **Security Pro Pack** | 10 | 5 commands, 5 agents | `/plugin install security-pro-pack@claude-code-plugins-plus` |
| **Fullstack Starter Pack** | 15 | 9 commands, 6 agents | `/plugin install fullstack-starter-pack@claude-code-plugins-plus` |
| **AI/ML Engineering Pack** | 12 | 4 commands, 8 agents | `/plugin install ai-ml-engineering-pack@claude-code-plugins-plus` |
| **Skills Powerkit** | 1 | 5 Agent Skills, 1 command | `/plugin install skills-powerkit@claude-code-plugins-plus` |

---

## How to Request a Plugin Pack

### Step 1: Navigate to Discussions

Go to: **[GitHub Discussions - Plugin Pack Requests](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/ideas)**

### Step 2: Start New Discussion

Click **"New discussion"** and select **"Plugin Pack Request"** if available (template coming soon).

### Step 3: Fill Out Request Template

The template will guide you through:

1. **Pack Name & Use Case**
   - What should it be called?
   - What problem does it solve?
   - Who is it for?

2. **Desired Components**
   - Agent Skills (model-invoked, auto-activate)
   - Subagents (domain experts)
   - Slash Commands (explicit /command syntax)
   - Hooks (event-driven automation)
   - MCP Servers (real code execution)

3. **Specific Requests**
   - List exact Skills, Agents, Commands you want
   - Provide trigger keywords for Skills
   - Define parameters for Commands

4. **Example Workflows**
   - Show step-by-step how you'd use the pack
   - Demonstrate time savings

5. **Additional Context**
   - Target audience and experience level
   - Integration requirements
   - Security considerations

### Step 4: Submit & Engage

- Submit your discussion
- Respond to community feedback
- Refine based on suggestions
- Offer to help if able!

---

## What Happens Next?

### 1. Community Discussion (Week 1)
- Other users +1 your request
- Community suggests improvements
- Similar use cases emerge

### 2. Feasibility Review (Week 1-2)
- Maintainers assess scope and complexity
- Check alignment with marketplace goals
- Evaluate community interest

### 3. Decision: Accepted or Declined
- **If Accepted:** Move to design phase
- **If Declined:** Explanation provided, alternatives suggested

### 4. Design Phase (Week 2-3)
- Create detailed design document
- Define all components (Skills, Commands, Agents)
- Break down into implementation tasks

### 5. Implementation (Week 3-6)
- Community contributors build plugins
- Or maintainers implement if complex
- Progress tracked publicly

### 6. Beta Testing (Week 6-7)
- Early users test the pack
- Bugs fixed, improvements made
- Documentation finalized

### 7. Official Release 🎉
- Pack added to marketplace
- Announcement in Discussions
- README and docs published

**Typical Timeline:** 2-6 weeks depending on complexity

---

## Plugin Component Types

### 🎯 Agent Skills (Model-Invoked)

**What they are:** Capabilities Claude uses automatically based on conversation context

**Example:** Skills Powerkit
- Say "create a plugin" → Plugin Creator skill activates
- Say "validate plugin" → Plugin Validator skill runs
- No `/command` needed!

**When to request:**
- Workflows you do repeatedly
- Tasks that should "just happen" when mentioned
- Context-aware automation

**Template section:** "Agent Skills Requested"

---

### 🤖 Subagents (Domain Experts)

**What they are:** Specialized AI agents invoked explicitly or through context

**Example:** DevOps Pack agents
- Docker Expert - Container optimization, Dockerfile best practices
- Kubernetes Agent - Cluster management, YAML configs
- Terraform Architect - Infrastructure as code patterns

**When to request:**
- Deep domain expertise needed
- Q&A and complex debugging
- Strategic guidance on architecture

**Template section:** "Subagents Requested"

---

### ⚡ Slash Commands (User-Invoked)

**What they are:** Custom shortcuts triggered with `/command-name` syntax

**Example:** DevOps Pack commands
- `/docker-optimize` - Analyzes and optimizes Dockerfile
- `/k8s-health` - Checks Kubernetes cluster health
- `/tf-init` - Scaffolds Terraform project structure

**When to request:**
- Scaffolding and templates
- One-time operations
- Explicit control needed

**Template section:** "Slash Commands Requested"

---

### 🪝 Hooks (Event-Driven)

**What they are:** Automation that triggers on specific events (file edits, tool usage)

**Example:** Formatter plugin
- **PostToolUse hook** - Auto-formats code after every file edit

**When to request:**
- Background automation
- Enforce standards automatically
- React to events

**Template section:** "Desired Plugin Components" checkbox

---

### 🔧 MCP Servers (Real Code)

**What they are:** External TypeScript/Node.js applications with actual compiled code

**Example:** Project Health Auditor
- Real code complexity analysis
- Git churn detection
- Test coverage mapping

**When to request:**
- Need actual code execution (not AI interpretation)
- Performance-critical operations
- External tool integration (databases, APIs)

**Template section:** "Desired Plugin Components" checkbox + "Integration Requirements"

---

## Tips for Great Requests

### ✅ Do This

**1. Be Specific About Workflows**
```
❌ "I need DevOps plugins"
✅ "I deploy microservices to Kubernetes daily. I need:
   - Automated health checks before deployment
   - Rollback if errors detected
   - Slack notifications on status changes"
```

**2. Differentiate Component Types**
```
❌ "I want a data cleaner"
✅ "I want a Data Cleaner Agent SKILL that auto-activates when I say
   'clean dataset', 'handle missing values', or 'preprocess data'"
```

**3. Show Time Savings**
```
❌ "This would be helpful"
✅ "Currently takes 45 minutes manually. With this pack: 2 minutes.
   Saves 5-6 hours/week across my team."
```

**4. Provide Trigger Keywords (for Skills)**
```
❌ "Auto-clean data"
✅ "Trigger keywords: 'clean data', 'handle missing values',
   'remove outliers', 'preprocess dataset'"
```

**5. Offer to Help**
```
✅ "I can:
   - Test beta versions
   - Provide real-world example workflows
   - Write documentation based on my use cases"
```

### ❌ Avoid This

**1. Vague Requests**
```
❌ "Make AI better"
❌ "I need productivity tools"
❌ "Build something cool"
```

**2. No Use Cases**
```
❌ Just listing plugin names without explaining WHY
```

**3. Requesting Everything**
```
❌ "100 plugins covering every possible workflow"
```

**4. Unrealistic Timelines**
```
❌ "Need this by tomorrow"
```

**5. No Differentiation**
```
❌ "I want a data plugin" (Skill? Command? Agent? MCP server?)
```

---

## Example: Perfect Plugin Pack Request

### 📋 Request

**Pack Name:** ML Engineering Pack

**Use Case:**
I'm a data scientist who spends 2-3 hours/day on repetitive ML tasks: data cleaning, experiment tracking, hyperparameter tuning, model deployment. I want to reduce this to 15-30 minutes so I can focus on research.

**Target Audience:** Intermediate ML engineers using PyTorch/scikit-learn

**Time Savings:** 2-3 hours/day → 30 minutes/day = 10-12 hours/week saved

---

**Agent Skills Requested:**

1. **Data Cleaner**
   - **What it does:** Automatically handles missing values, outliers, type conversions
   - **Trigger keywords:** "clean data", "handle missing values", "preprocess dataset", "remove outliers"
   - **Output:** Python code for data cleaning with explanations

2. **Experiment Tracker**
   - **What it does:** Auto-logs hyperparameters, metrics, artifacts to MLflow
   - **Trigger keywords:** "track experiment", "log results", "save metrics", "record this run"
   - **Output:** Adds MLflow logging to training code

3. **Model Trainer**
   - **What it does:** Scaffolds training loops with best practices (early stopping, logging, checkpoints)
   - **Trigger keywords:** "train model", "fit model", "start training", "run training loop"
   - **Output:** Complete training script with boilerplate

---

**Slash Commands Requested:**

1. `/deploy-model [model_path]`
   - Creates FastAPI endpoint + Dockerfile for model serving
   - Generates Kubernetes deployment YAML

2. `/experiment [experiment_name]`
   - Sets up MLflow experiment structure
   - Creates logging boilerplate

3. `/compare-models`
   - Generates comparison table of model performance
   - Visualizes metric differences

---

**Subagents Requested:**

1. **PyTorch Expert**
   - Deep learning architectures, training loops, optimization
   - Debugging CUDA errors, memory issues

2. **MLOps Engineer**
   - Model deployment, monitoring, CI/CD for ML
   - A/B testing, model versioning

---

**Example Workflows:**

**Workflow 1: Quick Experiment**
1. Load dataset: `df = pd.read_csv("data.csv")`
2. Say "clean this dataset" → Data Cleaner skill activates, generates cleaning code
3. Say "train XGBoost model" → Model Trainer scaffolds training script
4. Say "track this experiment" → Experiment Tracker adds MLflow logging
5. `/compare-models` → Generates comparison with baseline

**Workflow 2: Production Deployment**
1. Train best model
2. Say "evaluate model on test set" → Auto-generates evaluation code
3. `/deploy-model best_model.pkl` → Creates FastAPI + Docker config
4. Say "create Kubernetes deployment" → K8s YAML generated
5. Deploy to production cluster

---

**Integration Requirements:**
- MLflow tracking server (local or remote)
- PyTorch, scikit-learn, pandas
- Docker for deployment
- Optional: Kubernetes cluster

**Security Considerations:**
- Don't hardcode MLflow URIs or API keys
- Validate model file paths
- Sanitize user inputs in FastAPI endpoints

**Contribution Offer:**
I can help with:
- Testing beta versions with real ML workflows
- Providing example datasets and models
- Writing documentation based on data science perspective
- Giving feedback on trigger keywords

---

### Why This Request Is Perfect

✅ **Specific workflows** - Clear step-by-step examples
✅ **Quantified time savings** - 10-12 hours/week
✅ **Differentiates components** - Skills vs Commands vs Agents
✅ **Trigger keywords** - Exact phrases for Skills
✅ **Realistic scope** - 3 Skills + 3 Commands + 2 Agents = medium pack
✅ **Integration details** - MLflow, PyTorch, Docker, K8s
✅ **Security considered** - No hardcoded secrets
✅ **Offers to help** - Testing, docs, feedback

**Estimated Timeline:** 3-4 weeks with community help

---

## FAQ

### Q: How long does it take?

**A:** 2-6 weeks depending on:
- Pack size (small/medium/large)
- Complexity (simple commands vs Agent Skills)
- MCP servers needed (real code takes longer)
- Community contributor availability

### Q: Can I request just 1-2 plugins?

**A:** Yes! Not every request needs to be a full pack. For single plugin requests, use the [Feature Request](https://github.com/jeremylongshore/claude-code-plugins/issues/new?template=feature-request.yml) issue template instead.

### Q: What if my request is declined?

**A:** Maintainers will explain why and suggest alternatives:
- Scope too large → Break into smaller packs
- Overlaps with existing → Use existing pack + customization
- Too niche → Consider building it yourself (we'll help!)

### Q: Can I build it myself?

**A:** Absolutely! Check out:
- [Creating Plugins Guide](./creating-plugins.md)
- [Plugin Templates](../templates/)
- [Skills Powerkit](../plugins/examples/skills-powerkit/) - Use it to scaffold your pack!

### Q: How do I know if Skills or Commands are better?

**Skills (Model-Invoked):**
- ✅ Use when: Task is frequent, should "just happen" when mentioned
- ✅ Example: "clean data" → Data Cleaner activates automatically

**Commands (User-Invoked):**
- ✅ Use when: One-time operation, explicit control needed
- ✅ Example: `/deploy-model` → You control when it runs

**Both:**
- ✅ Use when: Pack has frequent tasks (Skills) + one-time operations (Commands)

### Q: Can I request updates to existing packs?

**A:** Yes! Use the same template but specify it's an enhancement to an existing pack. Maintainers will evaluate feasibility.

---

## Resources

- **[Discussion Template](.github/DISCUSSION_TEMPLATE/plugin-pack-request.yml)** - Full request form
- **[Template Guide](.github/DISCUSSION_TEMPLATE/README.md)** - Detailed usage instructions
- **[Creating Plugins](./creating-plugins.md)** - Build your own plugins
- **[Plugin Structure](./plugin-structure.md)** - Technical specifications
- **[Agent Skills Docs](https://docs.claude.com/en/docs/claude-code/skills)** - Official Skills documentation

---

## Get Started

**Ready to request a plugin pack?**

1. Go to [Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
2. Click "New discussion"
3. Select "Plugin Pack Request" (Ideas category)
4. Fill out the template
5. Submit and engage with the community!

**Questions?** Ask in [Q&A Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/q-a)

---

**Let's build amazing plugin packs together!** 🚀
