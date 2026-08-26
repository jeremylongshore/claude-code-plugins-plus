import { promises as fs } from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

type Scope = 'project' | 'user';
type Harness = {
  id: string;
  displayName: string;
  support: string;
  projectPath: string | null;
  userPath: string | null;
};

async function registry(): Promise<Harness[]> {
  const file = new URL('../../registry/harness-registry.json', import.meta.url);
  return (JSON.parse(await fs.readFile(file, 'utf8')) as { harnesses: Harness[] }).harnesses;
}

function target(harness: Harness, scope: Scope): string {
  const value = scope === 'project' ? harness.projectPath : harness.userPath;
  if (!value) throw new Error(`${harness.displayName} has no ${scope}-scope portable-skill path`);
  return value.startsWith('~/') ? path.join(os.homedir(), value.slice(2)) : path.resolve(value);
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
  const harness = (await registry()).find((item) => item.id === id);
  if (!harness) throw new Error(`Unknown harness: ${id}`);
  const destination = target(harness, scope);
  const result = {
    harness: id,
    support: harness.support,
    scope,
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
