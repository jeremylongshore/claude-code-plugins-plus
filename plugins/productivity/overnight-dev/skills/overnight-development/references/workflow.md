# Workflow

## Workflow

### Phase 1: Project Setup and Configuration

To prepare the project for overnight development:

1. **Verify Prerequisites:** Ensure the project is a Git repository, has a configured test framework, and includes at least one passing test.

    ```bash
    git init
    npm install --save-dev jest # Example for Node.js
    ```

2. **Install the Plugin:** Add the Claude Code Plugin marketplace and install the `overnight-dev` plugin.

    ```bash
    /plugin marketplace add jeremylongshore/claude-code-plugins
    /plugin install overnight-dev@claude-code-plugins-plus
    ```

3. **Run Setup Command:** Execute the `/overnight-setup` command to create necessary Git hooks and configuration files.

    ```bash
    /overnight-setup
    ```

### Phase 2: Task Definition and Planning

To define the task for the overnight session:

1. **Define a Clear Goal:** Specify a clear and testable goal for the overnight session, such as "Build user authentication with JWT (90% coverage)."

    ```text
    Task: Build user authentication with JWT (90% coverage)
    Success: All tests pass, 90%+ coverage, fully documented
    ```

2. **Start Coding:** Begin implementing the feature by writing tests first, following the TDD approach.

    ```javascript
    // Example test case (Node.js with Jest)
    it('should authenticate a user with valid credentials', async () => {
      // Test implementation
    });
    ```

3. **Attempt to Commit:** Try to commit the changes, which will trigger the Git hooks and run the tests.

    ```bash
    git commit -m "feat: implement user authentication"
    ```

### Phase 3: Autonomous Development and Debugging

To allow Claude to work autonomously:

1. **Git Hooks Enforcement:** The Git hooks will block the commit if any tests fail, providing Claude with the error messages.

    ```text
    Overnight Dev: Running pre-commit checks...
    Running linting...
    Linting passed
    Running tests...
    12 tests failing
    Commit blocked!
    ```

2. **Automated Debugging:** Claude analyzes the error messages, identifies the issues, and attempts to fix the code.

    ```text
    Claude: Fixing test failures in user authentication module.
    ```

3. **Retry Commits:** Claude retries the commit after making the necessary fixes, repeating the process until all tests pass.

    ```bash
    git commit -m "fix: address test failures in user authentication"
    ```

### Phase 4: Progress Tracking and Completion

To monitor the progress and finalize the session:

1. **Monitor Progress:** Track the progress of the overnight session by viewing the log file.

    ```bash
    cat .overnight-dev-log.txt
    ```

2. **Review Results:** Wake up to fully tested code, complete features, and a clean Git history.

    ```text
    7 AM: You wake up to:
    - 47 passing tests (0 failing)
    - 94% test coverage
    - Clean conventional commit history
    - Fully documented JWT authentication
    - Production-ready code
    ```

3. **Session Completion:** The session completes when all tests pass, the code meets the specified quality standards, and the changes are committed.
