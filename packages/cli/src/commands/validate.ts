/**
 * Validate Command - Validate plugins, skills, and frontmatter
 */

import chalk from 'chalk';
import ora from 'ora';
import * as path from 'path';
import { existsSync } from 'fs';
import {
  validateAll,
  validateAllSkills,
  validateAllFrontmatter,
  validateSkillFile,
  validateFrontmatterFile,
} from '../lib/validator/index.js';

export interface ValidateOptions {
  skills?: boolean;
  frontmatter?: boolean;
  strict?: boolean;
  json?: boolean;
}

/**
 * Main validate command handler
 */
export async function validateCommand(
  targetPath: string | undefined,
  options: ValidateOptions
): Promise<void> {
  // Determine base directory
  let baseDir: string;

  if (targetPath) {
    baseDir = path.isAbsolute(targetPath) ? targetPath : path.resolve(process.cwd(), targetPath);
    if (!existsSync(baseDir)) {
      console.error(chalk.red(`Error: Path not found: ${baseDir}`));
      process.exit(1);
    }
  } else {
    baseDir = process.cwd();
  }

  // Check if it's a single file
  const isSingleFile = targetPath && (
    targetPath.endsWith('.md') ||
    targetPath.endsWith('SKILL.md')
  );

  if (isSingleFile) {
    await validateSingleFile(baseDir, options);
    return;
  }

  // Determine what to validate
  const validateSkillsOnly = options.skills && !options.frontmatter;
  const validateFrontmatterOnly = options.frontmatter && !options.skills;

  if (!options.json) {
    console.log(chalk.bold('\nPlugin Validator\n'));
  }

  const spinner = options.json ? null : ora('Validating...').start();

  try {
    if (validateSkillsOnly) {
      const result = await validateAllSkills(baseDir);
      spinner?.stop();
      displaySkillsResult(result, options);

      if (result.withErrors > 0) {
        process.exit(1);
      }
    } else if (validateFrontmatterOnly) {
      const result = await validateAllFrontmatter(baseDir, options.strict);
      spinner?.stop();
      displayFrontmatterResult(result, options);

      if (result.errors > 0) {
        process.exit(1);
      }
    } else {
      // Validate all
      const result = await validateAll(baseDir, options.strict);
      spinner?.stop();

      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        displaySkillsResult(result.skills, options);
        console.log('');
        displayFrontmatterResult(result.frontmatter, options);
        displaySummary(result.hasErrors, result.hasWarnings);
      }

      if (result.hasErrors) {
        process.exit(1);
      }
    }
  } catch (error) {
    spinner?.fail('Validation failed');
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
    process.exit(1);
  }
}

/**
 * Validate a single file
 */
async function validateSingleFile(filePath: string, options: ValidateOptions): Promise<void> {
  const isSkill = filePath.includes('SKILL.md') || filePath.includes('/skills/');

  if (isSkill) {
    const result = await validateSkillFile(filePath);

    if (options.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(chalk.bold(`\nValidating: ${filePath}\n`));

      if (result.fatal) {
        console.log(chalk.red(`FATAL: ${result.fatal}`));
        process.exit(1);
      }

      if (result.errors.length > 0) {
        for (const error of result.errors) {
          console.log(chalk.red(`  ERROR: ${error}`));
        }
      }

      if (result.warnings.length > 0) {
        for (const warning of result.warnings) {
          console.log(chalk.yellow(`  WARN: ${warning}`));
        }
      }

      if (result.info.length > 0) {
        for (const info of result.info) {
          console.log(chalk.gray(`  INFO: ${info}`));
        }
      }

      if (result.errors.length === 0 && result.warnings.length === 0) {
        console.log(chalk.green('Valid skill file'));
      }
    }

    if (result.fatal || result.errors.length > 0) {
      process.exit(1);
    }
  } else {
    const result = await validateFrontmatterFile(filePath);

    if (options.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(chalk.bold(`\nValidating: ${filePath}\n`));

      if (result.error) {
        console.log(chalk.red(`  ERROR: ${result.error}`));
      }

      for (const error of result.errors) {
        console.log(chalk.red(`  ERROR: ${error}`));
      }

      if (!result.error && result.errors.length === 0) {
        console.log(chalk.green(`Valid ${result.fileType} frontmatter`));
      }
    }

    if (result.error || result.errors.length > 0) {
      process.exit(1);
    }
  }
}

/**
 * Display skills validation result
 */
function displaySkillsResult(result: any, options: ValidateOptions): void {
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log(chalk.bold('Skills Validation'));
  console.log(chalk.gray('─'.repeat(50)));

  // Show errors and warnings
  for (const skill of result.results) {
    if (skill.fatal) {
      console.log(chalk.red(`${skill.file}`));
      console.log(chalk.red(`  FATAL: ${skill.fatal}`));
      continue;
    }

    if (skill.errors.length > 0 || skill.warnings.length > 0) {
      const icon = skill.errors.length > 0 ? chalk.red('x') : chalk.yellow('!');
      console.log(`${icon} ${skill.file}`);

      for (const error of skill.errors) {
        console.log(chalk.red(`    ERROR: ${error}`));
      }

      for (const warning of skill.warnings) {
        console.log(chalk.yellow(`    WARN: ${warning}`));
      }
    }
  }

  // Summary
  console.log('');
  console.log(chalk.bold('Skills Summary:'));
  console.log(`  Total: ${result.total}`);
  console.log(chalk.green(`  Compliant: ${result.compliant}`));
  if (result.withWarnings > 0) {
    console.log(chalk.yellow(`  Warnings: ${result.withWarnings}`));
  }
  if (result.withErrors > 0) {
    console.log(chalk.red(`  Errors: ${result.withErrors}`));
  }
}

/**
 * Display frontmatter validation result
 */
function displayFrontmatterResult(result: any, options: ValidateOptions): void {
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log(chalk.bold('Frontmatter Validation'));
  console.log(chalk.gray('─'.repeat(50)));

  // Show errors
  for (const file of result.results) {
    if (file.error || file.errors.length > 0) {
      console.log(chalk.red(`x ${file.file} (${file.fileType})`));

      if (file.error) {
        console.log(chalk.red(`    ${file.error}`));
      }

      for (const error of file.errors) {
        console.log(chalk.red(`    ${error}`));
      }
    }
  }

  // Summary
  console.log('');
  console.log(chalk.bold('Frontmatter Summary:'));
  console.log(`  Total: ${result.total}`);
  if (result.warnings > 0) {
    console.log(chalk.yellow(`  Warnings: ${result.warnings}`));
  }
  if (result.errors > 0) {
    console.log(chalk.red(`  Errors: ${result.errors}`));
  }
  if (result.warnings === 0 && result.errors === 0) {
    console.log(chalk.green(`  All valid`));
  }
}

/**
 * Display overall summary
 */
function displaySummary(hasErrors: boolean, hasWarnings: boolean): void {
  console.log('');
  console.log(chalk.gray('═'.repeat(50)));

  if (hasErrors) {
    console.log(chalk.red('\nValidation FAILED with errors\n'));
  } else if (hasWarnings) {
    console.log(chalk.yellow('\nValidation PASSED with warnings\n'));
  } else {
    console.log(chalk.green('\nAll validations passed!\n'));
  }
}
