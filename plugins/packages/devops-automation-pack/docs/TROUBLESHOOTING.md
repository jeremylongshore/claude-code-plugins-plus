# Troubleshooting Guide - DevOps Automation Pack

**Quick solutions to common problems**

**Last Updated:** October 10, 2025

---

## Quick Diagnosis

**Start here to identify your issue:**

| Symptom | Likely Cause | Jump To |
|---------|--------------|---------|
| Commands not found | Installation issue | [#1](#1-commands-not-found-after-installation) |
| Commands error immediately | Permission or Git config | [#2](#2-command-fails-permission-denied) |
| Smart commit shows no changes | Git staging issue | [#7](#7-commit-smart-says-no-changes-to-commit) |
| PR creation fails | No remote or branch issue | [#8](#8-pr-create-fails-no-remote-configured) |
| Docker commands fail | Docker not running | [#11](#11-docker-commands-fail-docker-daemon) |
| K8s commands fail | kubectl not configured | [#13](#13-kubernetes-commands-fail-connection-refused) |
| Terraform commands fail | Terraform not installed | [#15](#15-terraform-commands-fail-command-not-found) |
| Slow performance | Large repository or network | [#18](#18-commands-are-slow-or-timeout) |

---

## Installation Issues

### 1. Commands Not Found After Installation

**Symptoms:**
```bash
/commit-smart
# Error: Unknown command '/commit-smart'
```

**Cause:** Plugin pack not installed correctly or Claude Code needs restart.

**Solution:**

**Step 1:** Verify installation
```bash
claude plugin list
```

You should see `devops-automation-pack` in the list.

**Step 2:** If not listed, reinstall
```bash
claude plugin install ~/Downloads/DevOps_Automation_Pack
```

**Step 3:** Restart Claude Code completely
```bash
# Close Claude Code window
# Reopen Claude Code
# Try command again
```

**Still not working?**
```bash
# Check installation directory
ls ~/.claude/plugins/

# Should see: devops-automation-pack/
```

If directory missing, reinstall from download location.

---

### 2. Command Fails: "Permission Denied"

**Symptoms:**
```bash
/github-actions-create
# Error: Permission denied: cannot write to .github/workflows/
```

**Cause:** No write permission in current directory.

**Solution:**

**Check directory permissions:**
```bash
ls -la .github/workflows/
```

**Fix permissions:**
```bash
# If directory doesn't exist, create it
mkdir -p .github/workflows

# If permission denied
sudo chown -R $USER:$USER .github/
```

**For scripts:**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

---

### 3. Plugin Installation Fails: "Already Exists"

**Symptoms:**
```bash
claude plugin install DevOps_Automation_Pack
# Error: Plugin 'devops-automation-pack' already installed
```

**Cause:** Old version still installed.

**Solution:**

**Uninstall old version first:**
```bash
claude plugin uninstall devops-automation-pack
```

**Then install new version:**
```bash
claude plugin install ~/Downloads/DevOps_Automation_Pack
```

**Verify version:**
```bash
claude plugin list | grep devops
# Should show: devops-automation-pack (v1.0.0)
```

---

## Git Workflow Issues

### 4. Git Not Configured

**Symptoms:**
```bash
/commit-smart
# Error: Please tell me who you are
# Error: Run 'git config --global user.email'
```

**Cause:** Git user identity not configured.

**Solution:**

**Set your identity globally:**
```bash
git config --global user.name "Your Name"
git config --global user.email "[email protected]"
```

**Verify configuration:**
```bash
git config --list | grep user
# Should show:
# user.name=Your Name
# [email protected]
```

**Set per-project (optional):**
```bash
cd your-project
git config user.name "Your Name"
git config user.email "[email protected]"
```

---

### 5. Not in a Git Repository

**Symptoms:**
```bash
/branch-create
# Error: fatal: not a git repository
```

**Cause:** Current directory is not a Git repository.

**Solution:**

**Initialize Git repository:**
```bash
git init
```

**Or navigate to existing repository:**
```bash
cd /path/to/your/project
```

**Verify you're in a Git repo:**
```bash
git status
# Should NOT say "not a git repository"
```

---

### 6. Branch Already Exists

**Symptoms:**
```bash
/branch-create
# Prompt: feature/user-auth
# Error: fatal: A branch named 'feature/user-auth' already exists
```

**Cause:** Branch name already in use.

**Solution:**

**Option 1: Use different branch name**
```bash
/branch-create
# Try: feature/user-auth-v2
```

**Option 2: Delete old branch (if safe)**
```bash
# View all branches
git branch -a

# Delete local branch (if not needed)
git branch -d feature/user-auth

# Force delete if has unmerged changes
git branch -D feature/user-auth
```

**Option 3: Switch to existing branch**
```bash
git checkout feature/user-auth
```

---

### 7. /commit-smart Says "No Changes to Commit"

**Symptoms:**
```bash
/commit-smart
# Error: No changes to commit
```

**Cause:** No files staged for commit.

**Solution:**

**Stage your changes first:**
```bash
# Stage all changes
git add .

# Or stage specific files
git add src/file.js

# Verify files are staged
git status
```

**Then try commit again:**
```bash
/commit-smart
```

**Alternative: Stage changes automatically**

Most commands auto-stage. If not working:
```bash
# Commit with auto-stage
git add . && /commit-smart
```

---

### 8. /pr-create Fails: "No Remote Configured"

**Symptoms:**
```bash
/pr-create
# Error: No remote repository configured
```

**Cause:** Local repository not connected to GitHub/GitLab.

**Solution:**

**Add remote repository:**
```bash
# GitHub
git remote add origin https://github.com/username/repo.git

# GitLab
git remote add origin https://gitlab.com/username/repo.git
```

**Verify remote:**
```bash
git remote -v
# Should show:
# origin  https://github.com/username/repo.git (fetch)
# origin  https://github.com/username/repo.git (push)
```

**Push branch to remote:**
```bash
git push -u origin your-branch-name
```

**Then create PR:**
```bash
/pr-create
```

---

### 9. Push Fails: "Authentication Failed"

**Symptoms:**
```bash
git push
# Error: Authentication failed
```

**Cause:** No GitHub/GitLab credentials configured.

**Solution:**

**For HTTPS (use personal access token):**
```bash
# GitHub: Create token at https://github.com/settings/tokens
# Use token as password when prompted

# Or configure credential helper
git config --global credential.helper cache
```

**For SSH (recommended):**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "[email protected]"

# Add key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH Keys → New SSH key
```

**Switch remote to SSH:**
```bash
git remote set-url origin [email protected]:username/repo.git
```

---

## CI/CD Issues

### 10. GitHub Actions Workflow Syntax Error

**Symptoms:**
```bash
/github-actions-create
# Workflow created, but GitHub shows syntax error
```

**Cause:** YAML indentation or structure issue.

**Solution:**

**Validate YAML syntax:**
```bash
# Install yamllint
pip install yamllint

# Check workflow file
yamllint .github/workflows/ci.yml
```

**Common YAML mistakes:**

```yaml
#  WRONG: Mixed tabs and spaces
jobs:
	build:
    runs-on: ubuntu-latest

#  CORRECT: Use spaces only
jobs:
  build:
    runs-on: ubuntu-latest
```

**Fix with GitHub's validator:**
1. Go to repository → Actions
2. Click "New workflow"
3. Paste your YAML
4. GitHub will show syntax errors

---

## Docker Issues

### 11. Docker Commands Fail: "Docker Daemon"

**Symptoms:**
```bash
/docker-optimize
# Error: Cannot connect to Docker daemon
```

**Cause:** Docker not running.

**Solution:**

**Start Docker:**

**On Mac:**
```bash
open -a Docker
# Wait for Docker icon in menu bar to show "running"
```

**On Linux:**
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Start on boot
```

**On Windows:**
```bash
# Start Docker Desktop from Start Menu
```

**Verify Docker is running:**
```bash
docker ps
# Should NOT say "Cannot connect to Docker daemon"
```

---

### 12. Dockerfile Build Fails: "No Such File"

**Symptoms:**
```bash
docker build -t myapp .
# Error: COPY failed: no such file or directory
```

**Cause:** Dockerfile references files not in build context.

**Solution:**

**Check build context:**
```bash
# List files Docker can see
docker build --no-cache -t test . 2>&1 | grep "COPY"
```

**Common mistakes:**

```dockerfile
#  WRONG: File outside context
COPY ../config.json /app/

#  CORRECT: File in context
COPY config.json /app/
```

**Fix: Copy files into context first**
```bash
# Copy file into project directory
cp ../config.json ./config.json

# Then build
docker build -t myapp .
```

---

## Kubernetes Issues

### 13. Kubernetes Commands Fail: "Connection Refused"

**Symptoms:**
```bash
/k8s-troubleshoot pod-name
# Error: Unable to connect to server: connection refused
```

**Cause:** kubectl not configured to connect to cluster.

**Solution:**

**Verify kubectl configured:**
```bash
kubectl cluster-info
# Should show cluster endpoint
```

**If not configured, set up kubeconfig:**

**For GKE:**
```bash
gcloud container clusters get-credentials CLUSTER_NAME --region REGION
```

**For EKS:**
```bash
aws eks update-kubeconfig --name CLUSTER_NAME --region REGION
```

**For local (minikube):**
```bash
minikube start
```

**Verify connection:**
```bash
kubectl get nodes
# Should list cluster nodes
```

---

### 14. Pod Troubleshooting Shows "Not Found"

**Symptoms:**
```bash
/k8s-troubleshoot my-pod
# Error: Pod 'my-pod' not found
```

**Cause:** Pod name incorrect or pod in different namespace.

**Solution:**

**List all pods:**
```bash
kubectl get pods --all-namespaces
```

**Get exact pod name:**
```bash
kubectl get pods | grep my-app
# Copy full pod name (includes random suffix)
# Example: my-app-7f9d6c-xk2m9
```

**Specify namespace if needed:**
```bash
kubectl get pods -n production
/k8s-troubleshoot my-pod -n production
```

---

## Terraform Issues

### 15. Terraform Commands Fail: "Command Not Found"

**Symptoms:**
```bash
/terraform-module-create
# Error: terraform: command not found
```

**Cause:** Terraform not installed.

**Solution:**

**Install Terraform:**

**On Mac:**
```bash
brew install terraform
```

**On Linux:**
```bash
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**On Windows:**
```bash
choco install terraform
```

**Verify installation:**
```bash
terraform --version
# Should show: Terraform v1.6.0 or higher
```

---

### 16. Terraform Plan Analysis Fails: "Invalid JSON"

**Symptoms:**
```bash
/terraform-plan-analyze plan.json
# Error: Invalid JSON format
```

**Cause:** Terraform plan not exported correctly.

**Solution:**

**Export plan correctly:**
```bash
# Step 1: Create plan
terraform plan -out=plan.out

# Step 2: Convert to JSON
terraform show -json plan.out > plan.json

# Step 3: Verify JSON valid
cat plan.json | jq empty

# Step 4: Analyze
/terraform-plan-analyze plan.json
```

**If still fails:**
```bash
# Check file size
ls -lh plan.json

# If too large (>10MB), filter:
terraform show -json plan.out | jq '.resource_changes' > plan.json
```

---

## General Performance Issues

### 17. Commands Hang or Take Too Long

**Symptoms:**
```bash
/commit-smart
# (command runs for 60+ seconds)
```

**Cause:** Large repository or many files.

**Solution:**

**For commit commands:**
```bash
# Commit specific paths only
git add src/
/commit-smart
```

**For analysis commands:**
```bash
# Analyze specific directory
cd src/
/docker-optimize
```

**Check repository size:**
```bash
du -sh .git/
# If >1GB, repository is large
```

**Optimize Git repository:**
```bash
git gc --aggressive
git prune
```

---

### 18. Commands Are Slow or Timeout

**Symptoms:**
```bash
/github-actions-create
# Error: Operation timed out after 60s
```

**Cause:** Network issues or API rate limits.

**Solution:**

**Check network connectivity:**
```bash
ping github.com
# Should show responses
```

**Check API rate limits:**

**GitHub:**
```bash
curl https://api.github.com/rate_limit
# Shows remaining API calls
```

**If rate limited, wait or authenticate:**
```bash
# Set GitHub token
export GITHUB_TOKEN=your_token_here
```

**Increase timeout (advanced):**
```bash
# Set in plugin config
claude config set timeout 120
```

---

## Agent Issues

### 19. AI Agent Not Activating

**Symptoms:**
```bash
# Ask about CI/CD
"How do I optimize my pipeline?"
# Generic response instead of CI/CD Expert Agent
```

**Cause:** Query not triggering agent activation.

**Solution:**

**Be more specific in questions:**

 "How do I make my code better?"
 "How do I optimize my GitHub Actions pipeline?"

 "I have Docker issues"
 "My Docker image is 2GB, how do I reduce it?"

**Explicitly invoke agent (if available):**
```bash
/ci-cd-expert "optimize my pipeline"
/docker-specialist "reduce image size"
```

---

### 20. Hooks Not Firing

**Symptoms:**
```bash
# Edit file
# No automatic formatting or validation
```

**Cause:** Hooks not configured or disabled.

**Solution:**

**Verify hooks enabled:**
```bash
claude plugin hooks list
# Should show devops-automation-pack hooks
```

**Enable hooks if disabled:**
```bash
claude plugin hooks enable devops-automation-pack
```

**Check hook configuration:**
```bash
cat ~/.claude/plugins/devops-automation-pack/hooks/hooks.json
```

---

## Still Having Issues?

If your problem isn't listed here:

### 1. Check Logs

```bash
# View Claude Code logs
claude logs

# View last 50 lines
claude logs --tail 50
```

### 2. Verify Prerequisites

```bash
# Check Claude Code version
claude --version
# Should be 1.5.0 or higher

# Check plugin version
claude plugin list | grep devops
# Should show version 1.0.0
```

### 3. Get Help

**Email Support:**
- **Address:** mandy@intentsolutions.io
- **Include:**
  - Exact error message (copy-paste)
  - Command you ran
  - Operating system
  - Claude Code version
  - Plugin version

**Response time:** Within 24 hours

---

## Quick Fix Checklist

Before contacting support, try these:

- [ ] Restart Claude Code
- [ ] Verify plugin installed: `claude plugin list`
- [ ] Check you're in Git repository: `git status`
- [ ] Verify Git configured: `git config user.name`
- [ ] Check Docker running (if using Docker commands): `docker ps`
- [ ] Verify kubectl configured (if using K8s commands): `kubectl get nodes`
- [ ] Check Terraform installed (if using Terraform commands): `terraform --version`
- [ ] View logs: `claude logs --tail 50`

---

**Document Version:** 1.0.0
**Pack Version:** 1.0.0
**Last Updated:** October 10, 2025
