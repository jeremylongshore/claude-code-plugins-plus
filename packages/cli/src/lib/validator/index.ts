/**
 * Plugin Validator - Unified validation for Claude Code plugins
 *
 * Provides validation for:
 * - Skills (SKILL.md files)
 * - Frontmatter (commands and agents)
 * - Plugin structure (plugin.json)
 */

export * from './skills.js';
export * from './frontmatter.js';

import { validateAllSkills, SkillValidationSummary } from './skills.js';
import { validateAllFrontmatter, FrontmatterValidationSummary } from './frontmatter.js';

export interface ValidationSummary {
  skills: SkillValidationSummary;
  frontmatter: FrontmatterValidationSummary;
  hasErrors: boolean;
  hasWarnings: boolean;
}

/**
 * Run all validators on a plugin directory
 */
export async function validateAll(baseDir: string, strict: boolean = false): Promise<ValidationSummary> {
  const skills = await validateAllSkills(baseDir);
  const frontmatter = await validateAllFrontmatter(baseDir, strict);

  const hasErrors = skills.withErrors > 0 || frontmatter.errors > 0;
  const hasWarnings = skills.withWarnings > 0 || frontmatter.warnings > 0;

  return {
    skills,
    frontmatter,
    hasErrors,
    hasWarnings,
  };
}
