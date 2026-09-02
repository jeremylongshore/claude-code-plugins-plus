import assert from 'node:assert/strict';
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const installer = new URL('../ops/install-security-headers.sh', import.meta.url).pathname;
const source = new URL('../ops/tonsofskills-security-headers.caddy', import.meta.url).pathname;

function fixture(mainText = 'example.invalid {\n    import security-headers\n}\n') {
  const directory = mkdtempSync(join(tmpdir(), 'security-header-install-'));
  const target = join(directory, 'security-headers.caddy');
  const main = join(directory, 'Caddyfile');
  const bin = join(directory, 'bin');
  const caddy = join(bin, 'caddy');
  mkdirSync(bin);
  writeFileSync(caddy, '#!/usr/bin/env sh\n[ "$1" = "adapt" ]\n');
  chmodSync(caddy, 0o755);
  writeFileSync(main, mainText);
  return { directory, target, main, bin };
}

function check(paths) {
  return spawnSync(
    'bash',
    [installer, '--check', source, paths.target, paths.main, 'example.invalid {'],
    {
      encoding: 'utf8',
      env: { ...process.env, PATH: `${paths.bin}:${process.env.PATH}` },
    },
  );
}

test('installer validates an exact candidate without touching live files', () => {
  const paths = fixture();
  try {
    const before = readFileSync(paths.main, 'utf8');
    const result = check(paths);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /candidate valid; sha256=[0-9a-f]{64}/);
    assert.equal(readFileSync(paths.main, 'utf8'), before);
    assert.equal(readFileSync(source, 'utf8').includes('Content-Security-Policy'), true);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});

test('installer refuses ambiguous site anchors', () => {
  const paths = fixture(
    'one.invalid {\n    import security-headers\n}\ntwo.invalid {\n    import security-headers\n}\n',
  );
  try {
    const result = check(paths);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /expected one site block/);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});

test('installer is idempotent when the exact import already exists', () => {
  const paths = fixture();
  try {
    writeFileSync(
      paths.main,
      `example.invalid {\n    import security-headers\n    import ${paths.target}\n}\n`,
    );
    const result = check(paths);
    assert.equal(result.status, 0, result.stderr);
  } finally {
    rmSync(paths.directory, { recursive: true, force: true });
  }
});

test('post-install validation failure restores prior and absent target states', () => {
  for (const targetBefore of [null, 'previous-fragment\n']) {
    const paths = fixture();
    const reloadLog = join(paths.directory, 'reload.log');
    try {
      const mainBefore = readFileSync(paths.main, 'utf8');
      if (targetBefore !== null) writeFileSync(paths.target, targetBefore);
      writeFileSync(
        join(paths.bin, 'caddy'),
        '#!/usr/bin/env sh\n[ "$1" = "adapt" ] && exit 0\n[ "$1" = "validate" ] && exit 42\nexit 2\n',
      );
      writeFileSync(
        join(paths.bin, 'sudo'),
        '#!/usr/bin/env sh\nwhile [ "$#" -gt 0 ]; do\n  case "$1" in\n    -n) shift ;;\n    -u) shift 2 ;;\n    *) break ;;\n  esac\ndone\nexec "$@"\n',
      );
      writeFileSync(
        join(paths.bin, 'systemctl'),
        '#!/usr/bin/env sh\nprintf "%s\\n" "$*" >> "$SYSTEMCTL_LOG"\n',
      );
      for (const command of ['caddy', 'sudo', 'systemctl']) {
        chmodSync(join(paths.bin, command), 0o755);
      }

      const result = spawnSync(
        '/usr/bin/sudo',
        [
          '-n',
          'env',
          `PATH=${paths.bin}:/usr/bin:/bin`,
          `SYSTEMCTL_LOG=${reloadLog}`,
          'bash',
          installer,
          source,
          paths.target,
          paths.main,
          'example.invalid {',
        ],
        { encoding: 'utf8' },
      );

      assert.notEqual(result.status, 0, 'planted caddy validate failure must fail install');
      assert.match(result.stderr, /rolled back/);
      assert.equal(readFileSync(paths.main, 'utf8'), mainBefore);
      if (targetBefore === null) {
        assert.equal(existsSync(paths.target), false, 'new target must be removed');
      } else {
        assert.equal(readFileSync(paths.target, 'utf8'), targetBefore);
      }
      assert.equal(readFileSync(reloadLog, 'utf8'), 'reload caddy\n');
    } finally {
      rmSync(paths.directory, { recursive: true, force: true });
    }
  }
});

test('failure during either live-file install rolls back the complete transaction', () => {
  for (const failingCall of ['1', '2']) {
    for (const targetBefore of [null, 'previous-fragment\n']) {
      const paths = fixture();
      const reloadLog = join(paths.directory, 'reload.log');
      const installLog = join(paths.directory, 'install.log');
      try {
        const mainBefore = readFileSync(paths.main, 'utf8');
        if (targetBefore !== null) writeFileSync(paths.target, targetBefore);
        writeFileSync(
          join(paths.bin, 'caddy'),
          '#!/usr/bin/env sh\n[ "$1" = "adapt" ] || [ "$1" = "validate" ]\n',
        );
        writeFileSync(
          join(paths.bin, 'sudo'),
          '#!/usr/bin/env sh\nwhile [ "$#" -gt 0 ]; do\n  case "$1" in\n    -n) shift ;;\n    -u) shift 2 ;;\n    *) break ;;\n  esac\ndone\nexec "$@"\n',
        );
        writeFileSync(
          join(paths.bin, 'systemctl'),
          '#!/usr/bin/env sh\nprintf "%s\\n" "$*" >> "$SYSTEMCTL_LOG"\n',
        );
        writeFileSync(
          join(paths.bin, 'install'),
          '#!/usr/bin/env sh\nprintf "x\\n" >> "$INSTALL_CALL_LOG"\ncount=$(wc -l < "$INSTALL_CALL_LOG")\n/usr/bin/install "$@"\n[ "$count" != "$FAIL_INSTALL_CALL" ]\n',
        );
        for (const command of ['caddy', 'sudo', 'systemctl', 'install']) {
          chmodSync(join(paths.bin, command), 0o755);
        }

        const result = spawnSync(
          '/usr/bin/sudo',
          [
            '-n',
            'env',
            `PATH=${paths.bin}:/usr/bin:/bin`,
            `SYSTEMCTL_LOG=${reloadLog}`,
            `INSTALL_CALL_LOG=${installLog}`,
            `FAIL_INSTALL_CALL=${failingCall}`,
            'bash',
            installer,
            source,
            paths.target,
            paths.main,
            'example.invalid {',
          ],
          { encoding: 'utf8' },
        );

        assert.notEqual(result.status, 0, `install call ${failingCall} must fail`);
        assert.match(result.stderr, /rolled back/);
        assert.equal(readFileSync(paths.main, 'utf8'), mainBefore);
        if (targetBefore === null) {
          assert.equal(existsSync(paths.target), false, 'new target must be removed');
        } else {
          assert.equal(readFileSync(paths.target, 'utf8'), targetBefore);
        }
        assert.equal(readFileSync(reloadLog, 'utf8'), 'reload caddy\n');
      } finally {
        rmSync(paths.directory, { recursive: true, force: true });
      }
    }
  }
});
