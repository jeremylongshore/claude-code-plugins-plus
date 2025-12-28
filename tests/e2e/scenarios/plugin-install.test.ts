import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import path from 'path';
import fs from 'fs/promises';
import {
  createTestEnv,
  installPlugin,
  uninstallPlugin,
  type TestEnvironment
} from '../setup';

describe('Plugin Installation', () => {
  let env: TestEnvironment;

  beforeEach(async () => {
    env = await createTestEnv();
  });

  afterEach(async () => {
    await env.cleanup();
  });

  describe('Successful Installation', () => {
    it('should install plugin from valid source', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      const metadata = await installPlugin(env, pluginPath);

      // Assert
      expect(metadata).toBeDefined();
      expect(metadata.name).toBe('test-plugin');
      expect(metadata.version).toBe('1.0.0');
      expect(metadata.description).toBe('Minimal test plugin for E2E validation');
      expect(env.installedPlugins.has('test-plugin')).toBe(true);
    });

    it('should copy all plugin files correctly', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      await installPlugin(env, pluginPath);
      const installPath = path.join(env.pluginsPath, 'test-plugin');

      // Assert
      const manifestExists = await fileExists(
        path.join(installPath, '.claude-plugin', 'plugin.json')
      );
      const readmeExists = await fileExists(
        path.join(installPath, 'README.md')
      );
      const skillExists = await fileExists(
        path.join(installPath, 'skills', 'test-skill', 'SKILL.md')
      );
      const commandExists = await fileExists(
        path.join(installPath, 'commands', 'test-command.md')
      );

      expect(manifestExists).toBe(true);
      expect(readmeExists).toBe(true);
      expect(skillExists).toBe(true);
      expect(commandExists).toBe(true);
    });

    it('should validate plugin.json schema', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      const metadata = await installPlugin(env, pluginPath);

      // Assert - verify required fields
      expect(metadata.name).toBeTruthy();
      expect(metadata.version).toMatch(/^\d+\.\d+\.\d+$/); // Semver format
      expect(metadata.description).toBeTruthy();
      expect(metadata.author).toHaveProperty('name');
      expect(metadata.author).toHaveProperty('email');
      expect(metadata.license).toBeTruthy();
    });

    it('should track installed plugin in environment', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      await installPlugin(env, pluginPath);

      // Assert
      expect(env.installedPlugins.size).toBe(1);
      expect(env.installedPlugins.has('test-plugin')).toBe(true);

      const plugin = env.installedPlugins.get('test-plugin');
      expect(plugin).toBeDefined();
      expect(plugin?.manifestPath).toContain('.claude-plugin/plugin.json');
      expect(plugin?.installPath).toContain('test-plugin');
    });
  });

  describe('Error Handling', () => {
    it('should reject plugin with missing manifest', async () => {
      // Arrange - create plugin directory without manifest
      const invalidPluginPath = path.join(env.basePath, 'invalid-plugin');
      await fs.mkdir(invalidPluginPath, { recursive: true });
      await fs.writeFile(
        path.join(invalidPluginPath, 'README.md'),
        'Invalid plugin'
      );

      // Act & Assert
      await expect(installPlugin(env, invalidPluginPath))
        .rejects
        .toThrow();
    });

    it('should reject plugin with invalid manifest JSON', async () => {
      // Arrange - create plugin with malformed manifest
      const invalidPluginPath = path.join(env.basePath, 'invalid-plugin');
      await fs.mkdir(path.join(invalidPluginPath, '.claude-plugin'), { recursive: true });
      await fs.writeFile(
        path.join(invalidPluginPath, '.claude-plugin', 'plugin.json'),
        '{ invalid json'
      );

      // Act & Assert
      await expect(installPlugin(env, invalidPluginPath))
        .rejects
        .toThrow();
    });

    it('should reject plugin missing required fields', async () => {
      // Arrange - create plugin with incomplete manifest
      const invalidPluginPath = path.join(env.basePath, 'incomplete-plugin');
      await fs.mkdir(path.join(invalidPluginPath, '.claude-plugin'), { recursive: true });
      await fs.writeFile(
        path.join(invalidPluginPath, '.claude-plugin', 'plugin.json'),
        JSON.stringify({
          name: 'incomplete-plugin'
          // Missing version and description
        })
      );

      // Act & Assert
      await expect(installPlugin(env, invalidPluginPath))
        .rejects
        .toThrow('Invalid plugin manifest: missing required fields');
    });

    it('should reject duplicate plugin installation', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');
      await installPlugin(env, pluginPath);

      // Act & Assert - try to install again
      await expect(installPlugin(env, pluginPath))
        .rejects
        .toThrow('Plugin test-plugin is already installed');
    });

    it('should reject non-existent plugin path', async () => {
      // Arrange
      const nonExistentPath = path.join(env.basePath, 'does-not-exist');

      // Act & Assert
      await expect(installPlugin(env, nonExistentPath))
        .rejects
        .toThrow();
    });
  });

  describe('Plugin Uninstallation', () => {
    it('should uninstall plugin completely', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');
      await installPlugin(env, pluginPath);

      // Act
      await uninstallPlugin(env, 'test-plugin');

      // Assert
      expect(env.installedPlugins.has('test-plugin')).toBe(false);

      const installPath = path.join(env.pluginsPath, 'test-plugin');
      const exists = await fileExists(installPath);
      expect(exists).toBe(false);
    });

    it('should remove all plugin files on uninstall', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');
      await installPlugin(env, pluginPath);
      const installPath = path.join(env.pluginsPath, 'test-plugin');

      // Verify files exist before uninstall
      const manifestExists = await fileExists(
        path.join(installPath, '.claude-plugin', 'plugin.json')
      );
      expect(manifestExists).toBe(true);

      // Act
      await uninstallPlugin(env, 'test-plugin');

      // Assert - all files removed
      const dirExists = await fileExists(installPath);
      expect(dirExists).toBe(false);
    });

    it('should reject uninstalling non-existent plugin', async () => {
      // Act & Assert
      await expect(uninstallPlugin(env, 'non-existent'))
        .rejects
        .toThrow('Plugin non-existent is not installed');
    });

    it('should allow reinstallation after uninstall', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act - install, uninstall, reinstall
      await installPlugin(env, pluginPath);
      await uninstallPlugin(env, 'test-plugin');
      const metadata = await installPlugin(env, pluginPath);

      // Assert
      expect(metadata.name).toBe('test-plugin');
      expect(env.installedPlugins.has('test-plugin')).toBe(true);
    });
  });

  describe('Multiple Plugins', () => {
    it('should install multiple plugins independently', async () => {
      // Arrange
      const plugin1Path = path.join(__dirname, '../fixtures/test-plugin');

      // Create a second test plugin
      const plugin2Path = path.join(env.basePath, 'test-plugin-2');
      await fs.mkdir(path.join(plugin2Path, '.claude-plugin'), { recursive: true });
      await fs.writeFile(
        path.join(plugin2Path, '.claude-plugin', 'plugin.json'),
        JSON.stringify({
          name: 'test-plugin-2',
          version: '2.0.0',
          description: 'Second test plugin',
          author: { name: 'Test', email: 'test@example.com' },
          license: 'MIT'
        })
      );
      await fs.writeFile(
        path.join(plugin2Path, 'README.md'),
        '# Test Plugin 2'
      );

      // Act
      await installPlugin(env, plugin1Path);
      await installPlugin(env, plugin2Path);

      // Assert
      expect(env.installedPlugins.size).toBe(2);
      expect(env.installedPlugins.has('test-plugin')).toBe(true);
      expect(env.installedPlugins.has('test-plugin-2')).toBe(true);
    });

    it('should maintain independent plugin state', async () => {
      // Arrange - install two plugins
      const plugin1Path = path.join(__dirname, '../fixtures/test-plugin');
      const plugin2Path = path.join(env.basePath, 'test-plugin-2');
      await fs.mkdir(path.join(plugin2Path, '.claude-plugin'), { recursive: true });
      await fs.writeFile(
        path.join(plugin2Path, '.claude-plugin', 'plugin.json'),
        JSON.stringify({
          name: 'test-plugin-2',
          version: '2.0.0',
          description: 'Second test plugin',
          author: { name: 'Test', email: 'test@example.com' },
          license: 'MIT'
        })
      );
      await fs.writeFile(path.join(plugin2Path, 'README.md'), '# Test Plugin 2');

      await installPlugin(env, plugin1Path);
      await installPlugin(env, plugin2Path);

      // Act - uninstall first plugin
      await uninstallPlugin(env, 'test-plugin');

      // Assert - second plugin still installed
      expect(env.installedPlugins.has('test-plugin')).toBe(false);
      expect(env.installedPlugins.has('test-plugin-2')).toBe(true);
      expect(env.installedPlugins.size).toBe(1);
    });
  });

  describe('Plugin Metadata', () => {
    it('should parse and store author information', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      const metadata = await installPlugin(env, pluginPath);

      // Assert
      expect(metadata.author).toEqual({
        name: 'Test Author',
        email: 'test@example.com'
      });
    });

    it('should parse and store license information', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      const metadata = await installPlugin(env, pluginPath);

      // Assert
      expect(metadata.license).toBe('MIT');
    });

    it('should validate semantic versioning', async () => {
      // Arrange
      const pluginPath = path.join(__dirname, '../fixtures/test-plugin');

      // Act
      const metadata = await installPlugin(env, pluginPath);

      // Assert - version follows semver
      expect(metadata.version).toMatch(/^\d+\.\d+\.\d+$/);
      const [major, minor, patch] = metadata.version.split('.').map(Number);
      expect(major).toBeGreaterThanOrEqual(0);
      expect(minor).toBeGreaterThanOrEqual(0);
      expect(patch).toBeGreaterThanOrEqual(0);
    });
  });
});

// Helper function
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
