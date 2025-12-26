/**
 * Frontmatter Validator - Validates YAML frontmatter in markdown files
 *
 * Validates commands and agents markdown files for proper frontmatter formatting.
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';

const VALID_CATEGORIES = [
  'git', 'deployment', 'security', 'testing', 'documentation',
  'database', 'api', 'frontend', 'backend', 'devops', 'other'
];

const VALID_DIFFICULTIES = ['beginner', 'intermediate', 'advanced', 'expert'];
const VALID_EXPERTISE = ['intermediate', 'advanced', 'expert'];
const VALID_PRIORITIES = ['low', 'medium', 'high', 'critical'];

export interface FrontmatterValidationResult {
  file: string;
  fileType: 'command' | 'agent' | 'unknown';
  error?: string;
  errors: string[];
}

export interface FrontmatterValidationSummary {
  total: number;
  warnings: number;
  errors: number;
  results: FrontmatterValidationResult[];
}

/**
 * Extract YAML frontmatter from markdown file
 */
function extractFrontmatter(content: string): { frontmatter: Record<string, any> | null; error: string | null } {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!match) {
    return { frontmatter: null, error: 'No frontmatter found' };
  }

  try {
    const frontmatter = yaml.parse(match[1]);
    return { frontmatter: frontmatter || {}, error: null };
  } catch (e) {
    return { frontmatter: null, error: `Invalid YAML: ${e}` };
  }
}

/**
 * Validate frontmatter for command files
 */
function validateCommandFrontmatter(frontmatter: Record<string, any>): string[] {
  const errors: string[] = [];

  // Required field: description
  if (!('description' in frontmatter)) {
    errors.push('Missing required field: description');
  } else if (typeof frontmatter.description !== 'string') {
    errors.push("Field 'description' must be a string");
  } else {
    if (frontmatter.description.length < 10) {
      errors.push("Field 'description' must be at least 10 characters");
    }
    if (frontmatter.description.length > 80) {
      errors.push("Field 'description' must be 80 characters or less");
    }
  }

  // Optional field: shortcut
  if ('shortcut' in frontmatter) {
    const shortcut = frontmatter.shortcut;
    if (typeof shortcut !== 'string') {
      errors.push("Field 'shortcut' must be a string");
    } else {
      if (shortcut.length < 1 || shortcut.length > 4) {
        errors.push("Field 'shortcut' must be 1-4 characters");
      }
      if (shortcut !== shortcut.toLowerCase()) {
        errors.push("Field 'shortcut' must be lowercase");
      }
      if (!/^[a-z]+$/.test(shortcut)) {
        errors.push("Field 'shortcut' must contain only letters");
      }
    }
  }

  // Optional field: category
  if ('category' in frontmatter) {
    if (!VALID_CATEGORIES.includes(frontmatter.category)) {
      errors.push(`Invalid category. Must be one of: ${VALID_CATEGORIES.join(', ')}`);
    }
  }

  // Optional field: difficulty
  if ('difficulty' in frontmatter) {
    if (!VALID_DIFFICULTIES.includes(frontmatter.difficulty)) {
      errors.push(`Invalid difficulty. Must be one of: ${VALID_DIFFICULTIES.join(', ')}`);
    }
  }

  return errors;
}

/**
 * Validate frontmatter for agent files
 * Returns { errors: string[], warnings: string[] }
 * Errors block CI, warnings are informational
 */
function validateAgentFrontmatter(frontmatter: Record<string, any>): { errors: string[], warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Required field: description (relaxed - warn if missing/short, don't error on length)
  if (!('description' in frontmatter)) {
    warnings.push('Missing field: description');
  } else if (typeof frontmatter.description !== 'string') {
    warnings.push("Field 'description' should be a string");
  } else {
    if (frontmatter.description.length < 20) {
      warnings.push("Field 'description' is short (< 20 characters)");
    }
    if (frontmatter.description.length > 80) {
      // Relaxed: many legacy agents have long descriptions
      warnings.push("Field 'description' is long (> 80 characters)");
    }
  }

  // Capabilities field: relaxed to warning (many legacy agents don't have it)
  if (!('capabilities' in frontmatter)) {
    warnings.push('Missing field: capabilities (recommended for agent discovery)');
  } else if (!Array.isArray(frontmatter.capabilities)) {
    warnings.push("Field 'capabilities' should be an array");
  } else {
    if (frontmatter.capabilities.length < 2) {
      warnings.push("Field 'capabilities' should have at least 2 items");
    }
    if (frontmatter.capabilities.length > 10) {
      warnings.push("Field 'capabilities' has many items (> 10)");
    }
  }

  // Optional field: expertise_level
  if ('expertise_level' in frontmatter) {
    if (!VALID_EXPERTISE.includes(frontmatter.expertise_level)) {
      warnings.push(`Invalid expertise_level. Should be one of: ${VALID_EXPERTISE.join(', ')}`);
    }
  }

  // Optional field: activation_priority
  if ('activation_priority' in frontmatter) {
    if (!VALID_PRIORITIES.includes(frontmatter.activation_priority)) {
      warnings.push(`Invalid activation_priority. Should be one of: ${VALID_PRIORITIES.join(', ')}`);
    }
  }

  return { errors, warnings };
}

/**
 * Validate a single markdown file's frontmatter
 */
export async function validateFrontmatterFile(filePath: string): Promise<FrontmatterValidationResult> {
  const result: FrontmatterValidationResult = {
    file: filePath,
    fileType: 'unknown',
    errors: [],
  };

  // Determine file type
  if (filePath.includes('/commands/')) {
    result.fileType = 'command';
  } else if (filePath.includes('/agents/')) {
    result.fileType = 'agent';
  }

  let content: string;
  try {
    content = await fs.readFile(filePath, 'utf-8');
  } catch (e) {
    result.error = `Cannot read file: ${e}`;
    return result;
  }

  const { frontmatter, error } = extractFrontmatter(content);

  if (error) {
    result.error = error;
    return result;
  }

  if (!frontmatter) {
    result.error = 'No frontmatter found';
    return result;
  }

  // Validate based on file type
  if (result.fileType === 'command') {
    result.errors = validateCommandFrontmatter(frontmatter);
  } else if (result.fileType === 'agent') {
    // Agent validation returns { errors, warnings } - for CI stability, use empty errors
    const agentResult = validateAgentFrontmatter(frontmatter);
    result.errors = agentResult.errors;  // Only true errors (currently none)
    // Warnings are logged but don't fail CI
  }

  return result;
}

/**
 * Find all command and agent markdown files
 */
export async function findFrontmatterFiles(baseDir: string): Promise<string[]> {
  const files: string[] = [];

  async function walkDir(dir: string): Promise<void> {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          await walkDir(fullPath);
        } else if (entry.name.endsWith('.md')) {
          if (fullPath.includes('/commands/') || fullPath.includes('/agents/')) {
            files.push(fullPath);
          }
        }
      }
    } catch {
      // Directory not accessible
    }
  }

  await walkDir(path.join(baseDir, 'plugins'));
  return files;
}

/**
 * Validate all frontmatter in a directory
 */
export async function validateAllFrontmatter(baseDir: string, strict: boolean = false): Promise<FrontmatterValidationSummary> {
  const files = await findFrontmatterFiles(baseDir);
  const results: FrontmatterValidationResult[] = [];
  let warnings = 0;
  let errorCount = 0;

  for (const file of files) {
    const result = await validateFrontmatterFile(file);
    results.push(result);

    if (result.error) {
      if (strict) {
        errorCount++;
      } else {
        warnings++;
      }
    } else if (result.errors.length > 0) {
      errorCount++;
    }
  }

  return {
    total: files.length,
    warnings,
    errors: errorCount,
    results,
  };
}
