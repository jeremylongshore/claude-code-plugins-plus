# Interactive Learning Lab Notebooks

**Interactive Jupyter notebooks** for hands-on learning of the Test Harness Pattern.

## 🚀 Quick Start

### Option 1: Google Colab (Recommended - No Setup)

Click "Open in Colab" badges below to run in your browser:

- **[01-mental-model.ipynb](01-mental-model.ipynb)** ✅ - 5-minute introduction to the test harness pattern
- **[02-orchestration-pattern.ipynb](02-orchestration-pattern.ipynb)** ✅ - Complete 60-min reference guide
- **[03-architecture-deep-dive.ipynb](03-architecture-deep-dive.ipynb)** *(Coming soon)* - Architecture breakdown
- **[04-build-your-own.ipynb](04-build-your-own.ipynb)** *(Coming soon)* - Build custom workflows
- **[05-debugging-tips.ipynb](05-debugging-tips.ipynb)** *(Coming soon)* - Troubleshooting guide

### Option 2: Local Jupyter

```bash
# Install dependencies
pip install jupyter jupytext nbformat ipykernel

# Start Jupyter
jupyter notebook

# Open any .ipynb file
```

### Option 3: VS Code

1. Install "Jupyter" extension
2. Open any `.ipynb` file
3. Click "Select Kernel" → Choose Python environment
4. Run cells with Shift+Enter

## 📚 Notebooks Overview

### 01-mental-model.ipynb
**What you'll learn:** The core mental model and why this pattern works

**Interactive elements:**
- ✨ Multi-step task challenge
- ✨ Session directory creation demo
- ✨ JSON validation examples
- ✨ Verification script simulation
- ✨ Complete 5-phase workflow runner

**Time:** 15-20 minutes (including exercises)

### 02-orchestration-pattern.ipynb ✅
**What you'll learn:** Complete deep-dive into subagent orchestration (915 lines, 6 parts)

**Interactive elements:**
- ✨ Context budget calculator (monolithic vs orchestrated)
- ✨ Phase contract builder & validator
- ✨ Verification pattern simulator with reconciliation
- ✨ Complete production orchestrator

**Time:** 60+ minutes

### 03-architecture-deep-dive.ipynb *(Coming soon)*
**What you'll learn:** Why the pattern is architected this way

**Interactive elements:**
- ✨ Context budget calculator
- ✨ Phase flow visualizer
- ✨ Trade-off analyzer

**Time:** 30 minutes

### 04-build-your-own.ipynb *(Coming soon)*
**What you'll learn:** Adapt the pattern for your use case

**Interactive elements:**
- ✨ Workflow template generator
- ✨ Interactive decision tree
- ✨ Custom phase builder

**Time:** 45 minutes

### 05-debugging-tips.ipynb *(Coming soon)*
**What you'll learn:** Common pitfalls and solutions

**Interactive elements:**
- ✨ Debugging wizard
- ✨ Error pattern matcher
- ✨ Troubleshooting flowchart

**Time:** 30 minutes

## 🎯 Learning Path

**Beginner:**
1. Start with `01-mental-model.ipynb`
2. Run all interactive cells
3. Experiment with the examples
4. Move to static guides when ready

**Intermediate:**
1. Complete `02-orchestration-pattern.ipynb`
2. Build custom workflow with `04-build-your-own.ipynb`
3. Reference `05-debugging-tips.ipynb` as needed

**Advanced:**
1. Study `03-architecture-deep-dive.ipynb`
2. Implement production workflow
3. Contribute your own use cases

## 🔧 Troubleshooting

### "Kernel not found"
Install ipykernel: `pip install ipykernel`

### "Module not found" errors
The notebooks use only Python standard library + basic packages. If you see import errors, install:
```bash
pip install jupyter nbformat
```

### Can't run in Colab
Make sure you clicked the "Open in Colab" badge. If the file downloads instead, upload it manually to Colab.

## 📖 Related Resources

- [Static Learning Guides](../workspace/lab/) - Read-only markdown versions
- [Reference Implementation](../workspace/lab/schema-optimization/) - Complete working example
- [Exercises](../workspace/lab/exercises/) - Hands-on practice tasks

## 🤝 Contributing

Have ideas for interactive examples? Found a bug?

1. Fork the repository
2. Add/fix the notebook
3. Test in Colab and local Jupyter
4. Submit PR with description

## 📄 License

MIT License - Free to use, modify, and distribute.

---

**Next:** Open `01-mental-model.ipynb` and start experimenting!
