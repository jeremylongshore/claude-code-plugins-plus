# Quick Start Guide - Your First 5 Minutes

**Goal:** Create a feature branch, make a commit, and open a pull request using the DevOps Automation Pack

**Time:** 5 minutes

**Difficulty:** Beginner

---

## What You'll Do

In this guide, you'll use three powerful commands to automate your Git workflow:

1. Create a feature branch with proper naming
2. Make a smart conventional commit
3. Generate a professional pull request

**By the end,** you'll have completed a full development cycle using automation.

---

## Prerequisites Check

Before starting, make sure:

- [ ] DevOps Automation Pack is installed (see `INSTALLATION.md`)
- [ ] You're in a Git repository (`cd` into your project)
- [ ] You have some uncommitted changes to work with
- [ ] Git is configured with your name and email

**Don't have a test project?** Create one:

```bash
mkdir ~/test-devops-pack
cd ~/test-devops-pack
git init
git config user.name "Your Name"
git config user.email "[email protected]"
echo "# Test Project" > README.md
```

---

## Step 1: Create a Feature Branch (30 seconds)

Instead of manually creating branches, use the branch creator:

```bash
/branch-create
```

**What happens:**

The command will ask you:
- **Feature type?** (feature, bugfix, hotfix, etc.)
- **Brief description?** (what you're building)

**Example interaction:**
```
? Select branch type: feature
? Brief description: add user authentication

 Created and switched to: feature/add-user-authentication
```

**Expected result:**

You're now on a new branch with a properly formatted name following team conventions.

**Verify:**
```bash
git branch
```

You should see `* feature/add-user-authentication` (or your branch name).

---

## Step 2: Make Changes and Smart Commit (2 minutes)

Let's make a simple change and commit it intelligently.

### Make a change:

```bash
echo "Added authentication system" >> README.md
```

### Create a smart commit:

Instead of writing your own commit message, let AI do it:

```bash
/commit-smart
```

**What happens:**

The command will:
1. Analyze your changes (sees you modified README.md)
2. Review your recent commit messages for style
3. Generate a conventional commit message
4. Show you the proposed commit

**Example output:**
```
 Analyzing changes...
 Found 1 modified file: README.md
 Reviewed commit history for style

Suggested commit message:
─────────────────────────────────────
docs: document authentication system addition

- Update README with authentication feature
- Follow conventional commits format

─────────────────────────────────────

Create this commit? (y/n):
```

### Review and confirm:

Type `y` and press Enter.

**Expected result:**
```
 Commit created: a3f8d92
 Message follows conventional commits standard
 Ready to push

Next step: Create a pull request with /pr-create
```

**Verify:**
```bash
git log -1
```

You'll see your beautifully formatted conventional commit!

>  **Tip:** The shortcut `/gc` does the same thing (gc = Git Commit)

---

## Step 3: Create a Pull Request (2 minutes)

Now let's open a pull request using automation.

### Push your branch:

First, push to remote (if you have one configured):

```bash
git push -u origin feature/add-user-authentication
```

Don't have a remote? That's fine - you can still see the PR template generation.

### Generate pull request:

```bash
/pr-create
```

**What happens:**

The command will:
1. Detect your current branch
2. Analyze commits in this branch
3. Generate a professional PR description
4. Create the PR (if you're on GitHub/GitLab)

**Example output:**
```
 Analyzing branch: feature/add-user-authentication
 Found 1 commit
 Detected base branch: main

Generated Pull Request:
─────────────────────────────────────
Title: Add user authentication

## Summary
This PR adds documentation for the new authentication system.

## Changes
- Updated README.md with authentication details
- Follows conventional commits standard

## Testing
- [ ] Documentation is clear
- [ ] Links work correctly

## Type of Change
- [x] Documentation update
- [ ] New feature
- [ ] Bug fix

─────────────────────────────────────

Create this PR? (y/n):
```

### Review and create:

Type `y` to create the pull request.

**Expected result:**
```
 Pull request created!
 URL: https://github.com/yourname/repo/pull/42

Next steps:
- Request reviewers
- Wait for CI/CD checks
- Merge when approved
```

**If no remote configured:**

The command will show you the PR template and instructions:
```
 Pull request template generated
 Save this to use when creating PR manually

Copy the template above and paste it when creating your PR on GitHub/GitLab.
```

>  **Tip:** The shortcut `/gpr` does the same thing (gpr = Git Pull Request)

---

## Step 4: View Your Workflow (30 seconds)

Let's see what you just accomplished:

```bash
git log --oneline --graph --all
```

**You'll see:**
```
* a3f8d92 (HEAD -> feature/add-user-authentication) docs: document authentication system addition
* b2e7c81 (main) Initial commit
```

A clean, professional commit history with:
-  Properly named feature branch
-  Conventional commit message
-  Professional pull request description

**All created in under 5 minutes!**

---

## What You Just Learned

In 5 minutes, you used the DevOps Automation Pack to:

1. **Create feature branches** with proper naming conventions
2. **Generate smart commits** following conventional commits standard
3. **Open pull requests** with professional descriptions

### Manual vs Automated

**Without the pack:**
- Manually type branch names (easy to mess up)
- Write commit messages from scratch (time-consuming)
- Format PR descriptions (often incomplete)
- **Total time:** 10-15 minutes per feature

**With the pack:**
- Quick guided workflows
- AI-generated messages
- Professional templates
- **Total time:** 5 minutes

**Time saved:** 50-70% on every feature!

---

## What's Next?

Now that you've mastered the basics, explore more commands:

### Try These Next:

**1. Optimize a Dockerfile:**
```bash
/docker-optimize
```
Analyzes your Dockerfile and suggests optimizations (can save 80%+ image size!)

**2. Generate a CI/CD Pipeline:**
```bash
/github-actions-create
```
Creates a GitHub Actions workflow with testing, linting, and deployment.

**3. Create Kubernetes Manifests:**
```bash
/k8s-manifest-generate
```
Generates production-ready K8s manifests with best practices.

**4. Build a Terraform Module:**
```bash
/terraform-module-create
```
Creates reusable infrastructure-as-code modules.

### Explore All 25 Plugins:

```bash
/help | grep devops
```

See complete list with descriptions and shortcuts.

### Read Real-World Examples:

See `docs/USE_CASES.md` for:
- Junior dev setting up first CI/CD
- Team migrating to Docker
- Startup deploying to Kubernetes
- And 4 more scenarios

### Get Advanced:

See `docs/TROUBLESHOOTING.md` for:
- Common issues and fixes
- Advanced configurations
- Performance tips

---

## Quick Reference

**Most Used Commands:**

| Command | Shortcut | What It Does |
|---------|----------|--------------|
| `/commit-smart` | `/gc` | Generate conventional commits |
| `/pr-create` | `/gpr` | Create pull requests |
| `/branch-create` | `/bc` | Create feature branches |
| `/docker-optimize` | `/do` | Reduce Docker image size |
| `/k8s-troubleshoot` | `/kt` | Debug Kubernetes pods |

**Get Help:**

- Command help: `/commit-smart --help`
- All commands: `/help`
- Support: mandy@intentsolutions.io

---

## Troubleshooting Your First Workflow

### Problem: "Git not configured"

**Solution:**
```bash
git config --global user.name "Your Name"
git config --global user.email "[email protected]"
```

### Problem: "Not in a Git repository"

**Solution:**
```bash
cd /path/to/your/project
# OR create a test project:
git init
```

### Problem: "No changes to commit"

**Solution:**
Make some changes first:
```bash
echo "test" >> README.md
git add README.md
/commit-smart
```

### Problem: "Push failed - no remote"

**Solution:**
Either:
1. Add a remote: `git remote add origin <url>`
2. Or skip the push step - you can still create PR template

---

## Congratulations!

You've completed your first workflow with the DevOps Automation Pack.

**What you've achieved:**
-  Created a properly named feature branch
-  Made a conventional commit with AI assistance
-  Generated a professional pull request
-  Saved 10+ minutes of manual work

**Keep going!** Every command saves you time and enforces best practices.

**Questions?** Email mandy@intentsolutions.io

---

**Document Version:** 1.0.0
**Pack Version:** 1.0.0
**Last Updated:** October 10, 2025
