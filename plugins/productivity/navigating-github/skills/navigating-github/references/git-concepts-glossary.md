# Git & GitHub Concepts Glossary

Plain-English definitions of git and GitHub terms. Use these when explaining concepts to users at any level.

## Core Concepts

### Repository (Repo)

- **Beginner:** A folder that git watches. It tracks every change you make so you can go back in time.
- **Technical:** A directory with a `.git/` subdirectory containing the complete history of all tracked files.

### Commit

- **Beginner:** A save point. Like saving your game — you can always come back to this exact moment.
- **Technical:** A snapshot of staged changes with a message, author, timestamp, and pointer to parent commit(s).

### Branch

- **Beginner:** A copy of your project where you can try things without messing up the original. Like "Save As" with a new name.
- **Technical:** A lightweight movable pointer to a commit. The default branch is typically `main`.

### Main / Master

- **Beginner:** The "official" version of your project. The one everyone agrees is the real, working version.
- **Technical:** The default branch. Convention has shifted from `master` to `main`. This is the branch that usually maps to production.

### Staging Area (Index)

- **Beginner:** A waiting room for changes. You pick which changes to include in your next save point before actually saving.
- **Technical:** An intermediate area where changes are collected before committing. `git add` moves changes to the staging area.

### Working Tree

- **Beginner:** Your actual files, right now, as you see them in your editor.
- **Technical:** The files currently checked out on disk. Changes here are "unstaged" until added to the index.

## Remote Operations

### Clone

- **Beginner:** Downloading a project from GitHub to your computer so you can work on it.
- **Technical:** Creates a local copy of a remote repository, including all history and branches.

### Fork

- **Beginner:** Making your own copy of someone else's project on GitHub. You can change your copy without affecting theirs.
- **Technical:** A server-side copy of a repository under your GitHub account. Used for contributing to projects you don't have write access to.

### Push

- **Beginner:** Uploading your saved changes from your computer to GitHub. Like syncing to the cloud.
- **Technical:** Transfers local commits to a remote repository.

### Pull

- **Beginner:** Downloading the latest changes from GitHub and applying them to the project on your computer. The opposite of push.
- **Technical:** Fetches changes from a remote and integrates them into the current branch. By default equivalent to `git fetch` + `git merge`, but can be configured to rebase instead (`pull.rebase = true` or `git pull --rebase`).

### Fetch

- **Beginner:** Downloading the latest updates from GitHub into git's memory, without changing the files on screen. Like checking for new mail without opening any of it.
- **Technical:** Downloads objects and refs from a remote into `.git/` storage. Does not modify the working tree or current branch — the fetched data must be explicitly merged or rebased.

### Remote

- **Beginner:** The GitHub address where your project lives online. Usually called "origin."
- **Technical:** A named reference to a remote repository. `origin` is the default name for the primary remote.

## Collaboration

### Pull Request (PR)

- **Beginner:** A request to add your changes to the main project. Like raising your hand and saying "I made these changes — can someone review them before we add them in?"
- **Technical:** A GitHub feature that lets you propose changes from one branch to another, with review, discussion, and CI integration.

### Code Review

- **Beginner:** Someone else looking at your changes before they get added to the project. Like having a friend proofread your essay.
- **Technical:** The process of examining proposed code changes for correctness, style, performance, and security before merging.

### Merge

- **Beginner:** Combining two versions of the project into one. Like merging two Google Docs into a single document.
- **Technical:** Integrates changes from one branch into another. Three strategies: fast-forward (linear history, no merge commit), three-way merge (creates a merge commit), and squash merge (collapses all commits into one).

### Fast-Forward

- **Beginner:** When the main branch hasn't changed since the branch was created, git can simply move the pointer forward — no combining needed.
- **Technical:** A merge strategy where HEAD advances linearly to the target commit without creating a merge commit. Only possible when there is no divergent history.

### Merge Conflict

- **Beginner:** Two people changed the same part of a file, and git doesn't know which version to keep. You have to choose.
- **Technical:** Occurs when changes in different branches modify the same lines. Marked with `<<<<<<<`, `=======`, `>>>>>>>` markers. Must be resolved manually.

### Rebase

- **Beginner:** Moving your changes to sit on top of the latest version of the project. Like rewriting your additions on a fresh copy of the document.
- **Technical:** Replays commits from one branch onto another, creating a linear history. Rewrites commit hashes.
- **Safety:** Never rebase commits that have been pushed to a shared branch — this rewrites history others depend on.
- **Advanced note:** `git rebase -i` (interactive) allows squashing, reordering, and editing commits.

## Git Operations

### Diff

- **Beginner:** A before-and-after comparison showing exactly what changed. Green lines are additions, red lines are removals.
- **Technical:** Shows the difference between two states — working tree vs staging, staging vs last commit, or between any two commits/branches.

### Stash

- **Beginner:** Temporarily hiding your changes so you can do something else, then bringing them back later. Like putting your work in a drawer.
- **Technical:** Saves uncommitted changes to a stack, reverting the working tree to HEAD. `git stash pop` restores them.

### Cherry-pick

- **Beginner:** Taking one specific save point from another branch and applying it to your current branch. Like copying one page from another notebook.
- **Technical:** Applies the changes from a specific commit to the current branch, creating a new commit.

### Tag

- **Beginner:** A permanent bookmark on a specific save point. Usually used for releases like "v1.0".
- **Technical:** A named reference to a specific commit. Lightweight tags are just pointers; annotated tags include metadata.

### HEAD

- **Beginner:** "Where you are right now" in the project's history. Like a "You Are Here" marker on a map.
- **Technical:** A reference to the current commit. Usually points to a branch name, which in turn points to a commit.

### Detached HEAD

- **Beginner:** You've wandered off the path. You're looking at an old save point but not on any branch. Any new changes might get lost unless you create a branch.
- **Technical:** HEAD points directly to a commit instead of a branch. Commits made in this state are unreachable once you switch branches, unless saved to a new branch.

## GitHub Features

### Issue

- **Beginner:** A to-do item or bug report for your project. Like a sticky note on a project board.
- **Technical:** A GitHub tracking item for bugs, features, or tasks. Can be linked to PRs, assigned, labeled, and milestoned.

### GitHub Actions

- **Beginner:** Automatic tasks that run when you push code. Like a robot that checks your homework every time you turn it in.
- **Technical:** GitHub's CI/CD platform. Workflows defined in `.github/workflows/` YAML files triggered by events (push, PR, schedule).

### Branch Protection

- **Beginner:** Rules that prevent accidents on important branches. Like a lock on the front door — you need a key (code review) to get in.
- **Technical:** GitHub settings that enforce requirements before merging to protected branches: required reviews, status checks, signed commits, etc.

### `.gitignore`

- **Beginner:** A list of files that git should pretend don't exist. Used for things like passwords, temporary files, and downloaded packages.
- **Technical:** Specifies intentionally untracked files. Patterns match against the working tree. Does not affect already-tracked files.
