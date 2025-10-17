import { Octokit } from '@octokit/rest';

// GitHub username/repo name validation regex
const GITHUB_REPO_REGEX = /^[a-zA-Z0-9_-]{1,39}\/[a-zA-Z0-9_.-]{1,100}$/;

// GitHub API limits
const GITHUB_LIMITS = {
  TITLE_MAX_LENGTH: 256,
  LABEL_MAX_LENGTH: 50,
  USERNAME_MAX_LENGTH: 39
};

/**
 * GitHub API client wrapper
 * Handles authentication and issue creation with security validation
 */
export class GitHubClient {
  /**
   * @param {string} token - GitHub personal access token
   * @throws {Error} If token is missing or invalid
   */
  constructor(token) {
    if (!token || typeof token !== 'string' || token.trim() === '') {
      throw new Error('GitHub token required. Set GITHUB_TOKEN environment variable.');
    }

    this.octokit = new Octokit({ auth: token });
  }

  /**
   * Validate repository format
   * @param {string} repo - Repository in format "owner/repo"
   * @returns {boolean} True if valid
   * @private
   */
  _validateRepoFormat(repo) {
    return GITHUB_REPO_REGEX.test(repo);
  }

  /**
   * Sanitize error message to prevent token exposure
   * @param {string} message - Error message
   * @returns {string} Sanitized message
   * @private
   */
  _sanitizeErrorMessage(message) {
    return message
      .replace(/ghp_[a-zA-Z0-9]{36}/g, 'REDACTED_TOKEN')
      .replace(/token=[^&\s]+/gi, 'token=REDACTED')
      .replace(/Authorization:\s*Bearer\s+[^\s]+/gi, 'Authorization: Bearer REDACTED');
  }

  /**
   * Validate and sanitize issue data
   * @param {Object} data - Issue data
   * @returns {Object} Sanitized issue data
   * @throws {Error} If data is invalid
   * @private
   */
  _validateIssueData(data) {
    // Validate title
    if (!data.title || typeof data.title !== 'string') {
      throw new Error('Issue title is required and must be a string');
    }

    if (data.title.length > GITHUB_LIMITS.TITLE_MAX_LENGTH) {
      throw new Error(`Issue title exceeds ${GITHUB_LIMITS.TITLE_MAX_LENGTH} character limit`);
    }

    // Sanitize labels
    const sanitizedLabels = Array.isArray(data.labels)
      ? data.labels
          .filter(l => typeof l === 'string' && l.length > 0 && l.length <= GITHUB_LIMITS.LABEL_MAX_LENGTH)
          .map(l => l.trim())
      : [];

    // Sanitize assignees (GitHub usernames)
    const sanitizedAssignees = Array.isArray(data.assignees)
      ? data.assignees
          .filter(a =>
            typeof a === 'string' &&
            a.length > 0 &&
            a.length <= GITHUB_LIMITS.USERNAME_MAX_LENGTH &&
            /^[a-zA-Z0-9-]+$/.test(a)
          )
          .map(a => a.trim())
      : [];

    return {
      title: data.title.trim().substring(0, GITHUB_LIMITS.TITLE_MAX_LENGTH),
      body: data.body || '',
      labels: sanitizedLabels,
      assignees: sanitizedAssignees
    };
  }

  /**
   * Create a GitHub issue with formatted content
   * @param {string} repo - Repository in format "owner/repo"
   * @param {Object} data - Issue data
   * @param {string} data.title - Issue title (max 256 chars)
   * @param {string} [data.body] - Issue body in markdown
   * @param {string[]} [data.labels] - Optional labels
   * @param {string[]} [data.assignees] - Optional assignees
   * @returns {Promise<Object>} Created issue data
   * @throws {Error} If repo format invalid or API call fails
   */
  async createIssue(repo, data) {
    // Validate repo format with regex
    if (!this._validateRepoFormat(repo)) {
      throw new Error(
        `Invalid repo format: ${repo}. Must be owner/repo with valid GitHub characters`
      );
    }

    const [owner, repoName] = repo.split('/');

    // Validate and sanitize issue data
    const sanitizedData = this._validateIssueData(data);

    try {
      const response = await this.octokit.issues.create({
        owner,
        repo: repoName,
        ...sanitizedData
      });

      return response.data;
    } catch (error) {
      // Handle rate limiting specifically
      if (error.status === 403 && error.message.includes('rate limit')) {
        const resetTime = error.response?.headers?.['x-ratelimit-reset']
          ? new Date(error.response.headers['x-ratelimit-reset'] * 1000)
          : 'unknown time';
        throw new Error(
          `GitHub API rate limit exceeded. Resets at ${resetTime.toLocaleString ? resetTime.toLocaleString() : resetTime}`
        );
      }

      // Sanitize error message before re-throwing
      const sanitizedMessage = this._sanitizeErrorMessage(error.message);
      throw new Error(`Failed to create issue: ${sanitizedMessage}`);
    }
  }

  /**
   * Verify repo exists and user has access
   * @param {string} repo - Repository in format "owner/repo"
   * @returns {Promise<Object>} Repository information
   * @throws {Error} If repo format invalid or not found
   */
  async verifyRepo(repo) {
    // Validate repo format with regex
    if (!this._validateRepoFormat(repo)) {
      throw new Error(
        `Invalid repo format: ${repo}. Must be owner/repo with valid GitHub characters`
      );
    }

    const [owner, repoName] = repo.split('/');

    try {
      const response = await this.octokit.repos.get({
        owner,
        repo: repoName
      });

      return {
        exists: true,
        fullName: response.data.full_name,
        hasIssues: response.data.has_issues
      };
    } catch (error) {
      if (error.status === 404) {
        throw new Error(`Repository not found: ${repo}`);
      }

      // Sanitize error message before re-throwing
      const sanitizedMessage = this._sanitizeErrorMessage(error.message);
      throw new Error(`Failed to verify repository: ${sanitizedMessage}`);
    }
  }
}
