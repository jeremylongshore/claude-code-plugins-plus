import { Octokit } from '@octokit/rest';

/**
 * GitHub API client wrapper
 * Handles authentication and issue creation
 */
export class GitHubClient {
  constructor(token) {
    if (!token) {
      throw new Error('GitHub token required. Set GITHUB_TOKEN environment variable.');
    }

    this.octokit = new Octokit({ auth: token });
  }

  /**
   * Create a GitHub issue with formatted content
   */
  async createIssue(repo, data) {
    const [owner, repoName] = repo.split('/');

    if (!owner || !repoName) {
      throw new Error(`Invalid repo format: ${repo}. Use: owner/repo`);
    }

    try {
      const response = await this.octokit.issues.create({
        owner,
        repo: repoName,
        title: data.title,
        body: data.body,
        labels: data.labels || [],
        assignees: data.assignees || []
      });

      return response.data;
    } catch (error) {
      throw new Error(`Failed to create issue: ${error.message}`);
    }
  }

  /**
   * Verify repo exists and user has access
   */
  async verifyRepo(repo) {
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
      return {
        exists: false,
        error: error.message
      };
    }
  }
}
