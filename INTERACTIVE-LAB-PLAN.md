# Interactive Learning Lab Implementation Plan

**Epic ID**: claude-code-plugins-pvx  
**Created**: 2025-12-21  
**Status**: Ready to execute  
**Strategy**: Feature branches, easiest-first, incremental releases

---

## 🎯 Vision

Transform the Learning Lab from static markdown into interactive, executable learning experiences where users can:
- Run code examples in-browser (no setup)
- Modify and experiment with workflows
- See results immediately
- Progress from beginner → expert with hands-on practice

---

## 📋 Execution Strategy

### Three-Phase Approach

**Phase 1: Colab Notebooks** (Easiest, Quick Win)
- Feature branch: `feature/interactive-colab`
- Time estimate: 4-6 hours
- Deliverable: 5 interactive Jupyter notebooks
- Release: v4.1.0

**Phase 2: GitHub Codespaces** (Full Environment)
- Feature branch: `feature/codespaces-env`
- Time estimate: 2-3 hours
- Deliverable: One-click dev environment
- Release: v4.2.0

**Phase 3: Advanced Features** (Premium Experience)
- Feature branch: `feature/advanced-interactive`
- Time estimate: 1-2 days
- Deliverable: Streamlit demos, video integration
- Release: v4.3.0

---

## Phase 1: Google Colab Notebooks (START HERE)

### Tasks

**Task 1.1: Environment Setup**
- Install jupytext: `pip install jupytext nbformat ipykernel`
- Create `notebooks/` directory structure
- Set up conversion workflow
- Priority: P1
- Estimated: 30 min

**Task 1.2: Convert GUIDE-00 (Mental Model)**
- Convert markdown → .ipynb
- Add interactive code cells with examples
- Add "Try it yourself" prompts
- Test in Colab (verify all cells run)
- Priority: P1
- Estimated: 1 hour

**Task 1.3: Convert ORCHESTRATION-PATTERN**
- Convert markdown → .ipynb (main reference)
- Add executable examples for each section
- Interactive phase contract builder
- Add verification script demo
- Priority: P1
- Estimated: 2 hours

**Task 1.4: Convert GUIDE-01 (Architecture)**
- Convert markdown → .ipynb
- Add context budget calculator (interactive)
- Visualize phase flow with diagrams
- Priority: P1
- Estimated: 1 hour

**Task 1.5: Convert GUIDE-02 (Build Your Own)**
- Convert markdown → .ipynb
- Add workflow template generator
- Interactive decision tree
- Priority: P1
- Estimated: 1 hour

**Task 1.6: Convert GUIDE-03 (Debugging)**
- Convert markdown → .ipynb
- Add debugging examples (runnable)
- Interactive troubleshooting wizard
- Priority: P1
- Estimated: 1 hour

**Task 1.7: Update README with Colab Badges**
- Add "Open in Colab" badges for all 5 notebooks
- Update Learning Lab section
- Add "Interactive Version" callout
- Priority: P1
- Estimated: 30 min

**Task 1.8: Test & Validate**
- Open each notebook in Colab
- Run all cells end-to-end
- Verify no errors
- Test on fresh Google account
- Priority: P1
- Estimated: 1 hour

**Task 1.9: Create Release PR**
- Merge feature/interactive-colab → main
- Update CHANGELOG.md (v4.1.0)
- Tag and release
- Priority: P1
- Estimated: 30 min

---

## Phase 2: GitHub Codespaces

### Tasks

**Task 2.1: Create .devcontainer Configuration**
- Create `.devcontainer/devcontainer.json`
- Configure base image (Ubuntu)
- Install required tools (bash, jq, git)
- Priority: P2
- Estimated: 30 min

**Task 2.2: Add Workspace Configuration**
- Configure VS Code extensions
- Set up integrated terminal
- Add welcome message with instructions
- Priority: P2
- Estimated: 30 min

**Task 2.3: Create Getting Started Guide**
- Add `CODESPACES.md` with instructions
- Quick start commands
- How to run the 5-phase workflow
- Priority: P2
- Estimated: 30 min

**Task 2.4: Add Codespaces Badge to README**
- Add "Open in GitHub Codespaces" badge
- Update docs to mention both options
- Priority: P2
- Estimated: 15 min

**Task 2.5: Test Codespaces Environment**
- Launch fresh Codespace
- Run through entire workflow
- Verify all scripts executable
- Priority: P2
- Estimated: 30 min

**Task 2.6: Create Release PR**
- Merge feature/codespaces-env → main
- Update CHANGELOG.md (v4.2.0)
- Tag and release
- Priority: P2
- Estimated: 30 min

---

## Phase 3: Advanced Features

### Tasks

**Task 3.1: Create Streamlit Demo App**
- Build interactive workflow visualizer
- Show phase execution in real-time
- Live report generation
- Priority: P3
- Estimated: 4 hours

**Task 3.2: Add Video Walkthroughs**
- Record 5-min intro video
- Embed in notebooks
- Add to README
- Priority: P3
- Estimated: 3 hours

**Task 3.3: Claude API Integration Examples**
- Add live API call examples in notebooks
- Show actual agent spawning
- Demonstrate verification pattern
- Priority: P3
- Estimated: 2 hours

**Task 3.4: Create Interactive Decision Tree**
- "Which workflow pattern fits my use case?"
- Web-based questionnaire
- Generates starter template
- Priority: P3
- Estimated: 3 hours

**Task 3.5: Build Observable Notebooks**
- Create visual architecture explorer
- Interactive diagrams
- Publish to Observable
- Priority: P3
- Estimated: 4 hours

**Task 3.6: Create Release PR**
- Merge feature/advanced-interactive → main
- Update CHANGELOG.md (v4.3.0)
- Tag and release
- Priority: P3
- Estimated: 30 min

---

## 🗂️ File Structure (After All Phases)

```
claude-code-plugins/
├── notebooks/                          # Phase 1: Colab notebooks
│   ├── 01-mental-model.ipynb
│   ├── 02-orchestration-pattern.ipynb
│   ├── 03-architecture-deep-dive.ipynb
│   ├── 04-build-your-own.ipynb
│   ├── 05-debugging-tips.ipynb
│   └── README.md                       # How to use notebooks
├── .devcontainer/                      # Phase 2: Codespaces
│   ├── devcontainer.json
│   └── welcome-message.md
├── demos/                              # Phase 3: Advanced
│   ├── streamlit-app/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── observable/
│   │   └── architecture-explorer.js
│   └── videos/
│       ├── intro-5min.mp4
│       └── walkthrough-links.md
├── workspace/lab/                      # Original static content
│   └── ... (unchanged)
└── README.md                           # Updated with all badges
```

---

## 📊 Success Metrics

### Phase 1 Success Criteria
- [ ] 5 notebooks created and tested
- [ ] All cells execute without errors in Colab
- [ ] Badges added to README
- [ ] v4.1.0 released
- [ ] User feedback: "I could run the examples immediately"

### Phase 2 Success Criteria
- [ ] Codespaces launches in <60 seconds
- [ ] Full workflow executable in Codespace
- [ ] Badge added to README
- [ ] v4.2.0 released
- [ ] User feedback: "I had a complete dev environment instantly"

### Phase 3 Success Criteria
- [ ] Streamlit demo deployed and accessible
- [ ] Videos embedded in notebooks
- [ ] Observable diagrams published
- [ ] v4.3.0 released
- [ ] User feedback: "This is a premium learning experience"

---

## 🚀 Quick Start Commands

### Phase 1: Start Right Now

```bash
# 1. Create feature branch
git checkout -b feature/interactive-colab

# 2. Install tools
pip install jupytext nbformat ipykernel

# 3. Create notebooks directory
mkdir -p notebooks

# 4. Convert first guide
jupytext --to notebook workspace/lab/GUIDE-00-START-HERE.md \
  -o notebooks/01-mental-model.ipynb

# 5. Edit notebook, add interactive cells
# 6. Test in Colab
# 7. Repeat for remaining guides
```

### Phase 2: After Phase 1 Complete

```bash
# 1. Create feature branch
git checkout -b feature/codespaces-env

# 2. Create devcontainer config
mkdir -p .devcontainer
# [create devcontainer.json]

# 3. Test in Codespace
# 4. Merge when validated
```

### Phase 3: After Phase 2 Complete

```bash
# 1. Create feature branch
git checkout -b feature/advanced-interactive

# 2. Build Streamlit app
mkdir -p demos/streamlit-app
# [create app.py, requirements.txt]

# 3. Record videos
# 4. Create Observable notebooks
# 5. Merge when complete
```

---

## 🎯 Next Actions (Immediate)

**Right Now**: Execute Phase 1, Task 1.1

```bash
# Mark epic and first task as in-progress
bd update claude-code-plugins-pvx.1 --status in_progress

# Create feature branch
git checkout -b feature/interactive-colab

# Install tools
pip install jupytext nbformat ipykernel

# Create directory
mkdir -p notebooks

# Start converting first guide
```

---

## 📝 Dependencies

### Required Tools
- Python 3.8+
- pip (package manager)
- git
- jupytext (notebook converter)
- nbformat (Jupyter format handler)
- ipykernel (notebook kernel)

### Optional Tools (Phase 3)
- Streamlit (`pip install streamlit`)
- ffmpeg (video processing)
- Observable account (free tier)

### Services Required
- Google account (for Colab testing)
- GitHub account (for Codespaces, already have)
- Observable account (Phase 3, free)

---

## ⚠️ Risk Mitigation

### Risk 1: Notebooks Don't Run in Colab
**Mitigation**: Test each notebook immediately after conversion, fix before moving to next

### Risk 2: Codespaces Resource Limits
**Mitigation**: Keep environment minimal, document free tier limits clearly

### Risk 3: User Confusion (Too Many Options)
**Mitigation**: Clear progression path in README: "Start with Colab → Try Codespaces → Explore Advanced"

### Risk 4: Maintenance Burden
**Mitigation**: Keep notebooks in sync with markdown using jupytext bidirectional sync

---

## 🏁 Release Schedule

- **v4.1.0**: Colab Notebooks (1 week from now)
- **v4.2.0**: GitHub Codespaces (+1 week)
- **v4.3.0**: Advanced Features (+2 weeks)

Total timeline: ~1 month for all 3 phases

---

**Ready to execute Phase 1!**

Next command: 
```bash
bd update claude-code-plugins-pvx.1 --status in_progress
```

---

## ✅ BEADS PLAN CREATED

**Epic**: `claude-code-plugins-pvx`  
**Total Tasks**: 21 tasks (9 Phase 1 + 6 Phase 2 + 6 Phase 3)  
**Status**: All tasks created and synced to GitHub

### Task Breakdown

**Phase 1: Colab Notebooks** (P1 - 9 tasks)
```
pvx.1  - Environment setup (30min)
pvx.2  - Convert GUIDE-00 (1hr)
pvx.3  - Convert ORCHESTRATION-PATTERN (2hrs) ⭐ BIGGEST
pvx.4  - Convert GUIDE-01 (1hr)
pvx.5  - Convert GUIDE-02 (1hr)
pvx.6  - Convert GUIDE-03 (1hr)
pvx.7  - Update README badges (30min)
pvx.8  - Test & validate (1hr)
pvx.9  - Release v4.1.0 (30min)
```
**Total Phase 1**: ~8.5 hours

**Phase 2: Codespaces** (P2 - 6 tasks)
```
pvx.10 - Create devcontainer (30min)
pvx.11 - Workspace config (30min)
pvx.12 - Getting started guide (30min)
pvx.13 - README badge (15min)
pvx.14 - Test Codespaces (30min)
pvx.15 - Release v4.2.0 (30min)
```
**Total Phase 2**: ~2.75 hours

**Phase 3: Advanced** (P3 - 6 tasks)
```
pvx.16 - Streamlit demo (4hrs)
pvx.17 - Video walkthroughs (3hrs)
pvx.18 - Claude API examples (2hrs)
pvx.19 - Decision tree (3hrs)
pvx.20 - Observable notebooks (4hrs)
pvx.21 - Release v4.3.0 (30min)
```
**Total Phase 3**: ~16.5 hours

---

## 🚀 START NOW: First Task

```bash
# 1. Mark first task as in-progress
bd update claude-code-plugins-pvx.1 --status in_progress

# 2. Create feature branch
git checkout -b feature/interactive-colab

# 3. Install tools
pip install jupytext nbformat ipykernel

# 4. Create directory
mkdir -p notebooks

# 5. Verify cass is installed
cass --version
# Output: cass 0.1.36

# 6. Ready to convert first notebook!
```

---

## 📊 Beads Commands Cheat Sheet

```bash
# View all Phase 1 tasks
bd list --title "Phase 1" --sort id

# View all tasks for this epic
bd list --title "pvx"

# Start a task
bd update claude-code-plugins-pvx.1 --status in_progress

# Complete a task
bd close claude-code-plugins-pvx.1 --reason "Environment set up. Tools installed."

# See what's ready to work on
bd ready

# Sync to GitHub
bd sync
```

---

## 🎯 Tools Installed

✅ **beads (bd)** - Globally installed, working  
✅ **cass** - v0.1.36 - Coding agent session search  
✅ **git** - Version control  
✅ **Python 3** - Ready for jupytext  

**To install for Phase 1**:
```bash
pip install jupytext nbformat ipykernel
```

---

**Plan saved to**: `INTERACTIVE-LAB-PLAN.md`  
**Beads epic**: `claude-code-plugins-pvx`  
**First task**: `claude-code-plugins-pvx.1`

**Execute now**:
```bash
bd update claude-code-plugins-pvx.1 --status in_progress
```
