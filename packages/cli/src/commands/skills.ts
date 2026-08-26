import { promises as fs } from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { randomUUID } from 'node:crypto';

type Scope = 'project' | 'user';
type Support =
  | 'verified-native'
  | 'standard-compatible'
  | 'native-extension'
  | 'research-required'
  | 'unsupported';
export type Harness = {
  id: string;
  displayName: string;
  support: Support;
  projectPath: string | null;
  userPath: string | null;
};

export type PortableInstallResult = {
  harness: string;
  support: Support;
  scope: Scope;
  source: string;
  destination: string;
  dryRun: boolean;
};

async function registry(): Promise<Harness[]> {
  const file = new URL('../../registry/harness-registry.json', import.meta.url);
  return (JSON.parse(await fs.readFile(file, 'utf8')) as { harnesses: Harness[] }).harnesses;
}

function asScope(scope: string): Scope {
  if (scope === 'project' || scope === 'user') return scope;
  throw new Error(`Invalid scope: ${scope}. Use project or user.`);
}

function target(harness: Harness, scope: Scope): string {
  const value = scope === 'project' ? harness.projectPath : harness.userPath;
  if (!value) throw new Error(`${harness.displayName} has no ${scope}-scope portable-skill path`);
  return value.startsWith('~/') ? path.join(os.homedir(), value.slice(2)) : path.resolve(value);
}

async function portableSource(source: string): Promise<{ directory: string; name: string }> {
  const candidate = path.resolve(source);
  const directory = path.basename(candidate) === 'SKILL.md' ? path.dirname(candidate) : candidate;
  const skillFile = path.join(directory, 'SKILL.md');
  const info = await fs.stat(skillFile).catch(() => null);
  if (!info?.isFile())
    throw new Error(`Portable source must be a skill directory containing SKILL.md: ${source}`);
  const name = path.basename(directory);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name)) {
    throw new Error(`Portable skill directory must be lowercase kebab-case: ${name}`);
  }
  return { directory, name };
}

async function selectedHarness(id: string): Promise<Harness> {
  const harness = (await registry()).find((item) => item.id === id);
  if (!harness) throw new Error(`Unknown harness: ${id}`);
  return harness;
}

export async function listHarnesses(json: boolean): Promise<void> {
  const harnesses = await registry();
  console.log(
    json
      ? JSON.stringify(harnesses, null, 2)
      : harnesses.map((h) => `${h.id}\t${h.support}\t${h.displayName}`).join('\n'),
  );
}

export async function doctorSkills(id: string, scope: Scope, json: boolean): Promise<void> {
  const resolvedScope = asScope(scope);
  const harness = await selectedHarness(id);
  const destination = target(harness, resolvedScope);
  const result = {
    harness: id,
    support: harness.support,
    scope: resolvedScope,
    destination,
    exists: await fs
      .stat(destination)
      .then(() => true)
      .catch(() => false),
  };
  console.log(
    json
      ? JSON.stringify(result, null, 2)
      : `${result.exists ? 'Found' : 'Missing'} ${destination}`,
  );
}

export async function installPortableSkill(
  source: string,
  id: string,
  scope: string,
  dryRun: boolean,
  json: boolean,
): Promise<void> {
  const resolvedScope = asScope(scope);
  const harness = await selectedHarness(id);
  if (harness.support !== 'verified-native') {
    throw new Error(
      `${harness.displayName} is ${harness.support}; installation is available only for verified-native harnesses.`,
    );
  }
  const portable = await portableSource(source);
  const root = target(harness, resolvedScope);
  const destination = path.join(root, portable.name);
  const result: PortableInstallResult = {
    harness: harness.id,
    support: harness.support,
    scope: resolvedScope,
    source: portable.directory,
    destination,
    dryRun,
  };
  if (!dryRun) {
    await fs.mkdir(root, { recursive: true });
    try {
      await fs.lstat(destination);
      throw new Error(`Refusing to overwrite existing portable skill: ${destination}`);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
    const staging = path.join(root, `.${portable.name}.${randomUUID()}`);
    try {
      await fs.cp(portable.directory, staging, { recursive: true, errorOnExist: true });
      await fs.rename(staging, destination);
    } catch (error) {
      await fs.rm(staging, { recursive: true, force: true });
      throw error;
    }
  }
  console.log(
    json
      ? JSON.stringify(result, null, 2)
      : `${dryRun ? 'Would install' : 'Installed'} ${portable.name} at ${destination}`,
  );
}
