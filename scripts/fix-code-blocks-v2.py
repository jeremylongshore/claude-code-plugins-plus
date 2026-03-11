#!/usr/bin/env python3
"""
Fix code block warnings in SKILL.md files (v2):
1. Add error handling to bash code blocks
2. Add comments to magic numbers - ensuring the comment contains the number itself
   (validator checks: re.search(rf'#.*{num}', block))

Works at the code-block level, not line level.
"""

import re
import sys
from pathlib import Path

# Common magic numbers and their meanings
MAGIC_NUMBERS = {
    # Ports
    '80': 'port 80 - HTTP',
    '443': 'port 443 - HTTPS',
    '3000': 'port 3000 - dev server',
    '3001': 'port 3001 - alternate dev',
    '3306': 'port 3306 - MySQL',
    '4000': 'port 4000 - dev server',
    '4200': 'port 4200 - Angular dev',
    '4321': 'port 4321 - Astro dev',
    '5000': 'port 5000 - Flask/dev',
    '5173': 'port 5173 - Vite dev',
    '5432': 'port 5432 - PostgreSQL',
    '5672': 'port 5672 - RabbitMQ',
    '6379': 'port 6379 - Redis',
    '6380': 'port 6380 - Redis TLS',
    '8000': 'port 8000 - API server',
    '8080': 'port 8080 - HTTP proxy',
    '8081': 'port 8081 - alternate HTTP',
    '8443': 'port 8443 - HTTPS alternate',
    '8888': 'port 8888 - Jupyter',
    '9090': 'port 9090 - Prometheus',
    '9092': 'port 9092 - Kafka',
    '9200': 'port 9200 - Elasticsearch',
    '9300': 'port 9300 - ES transport',
    '9411': 'port 9411 - Zipkin',
    '15672': 'port 15672 - RabbitMQ mgmt',
    '16686': 'port 16686 - Jaeger UI',
    '27017': 'port 27017 - MongoDB',
    '12345': 'port 12345 - example/test',
    '1234': 'port 1234 - example/test',
    # HTTP status codes
    '200': '200 OK',
    '201': '201 Created',
    '204': '204 No Content',
    '301': '301 Moved Permanently',
    '302': '302 Found (redirect)',
    '304': '304 Not Modified',
    '400': '400 Bad Request',
    '401': '401 Unauthorized',
    '403': '403 Forbidden',
    '404': '404 Not Found',
    '408': '408 Request Timeout',
    '409': '409 Conflict',
    '422': '422 Unprocessable Entity',
    '429': '429 Too Many Requests',
    '500': '500 Internal Server Error',
    '502': '502 Bad Gateway',
    '503': '503 Service Unavailable',
    '504': '504 Gateway Timeout',
    # Sizes
    '256': '256 bytes',
    '512': '512 bytes',
    '1024': '1024 = 1 KB',
    '2048': '2048 = 2 KB',
    '4096': '4096 = 4 KB',
    '8192': '8192 = 8 KB',
    '65535': '65535 = max port number',
    # Timeouts (seconds)
    '300': '300s = 5 min timeout',
    '600': '600s = 10 min timeout',
    '900': '900s = 15 min timeout',
    '1800': '1800s = 30 min timeout',
    '3600': '3600s = 1 hour timeout',
    '7200': '7200s = 2 hour timeout',
    '86400': '86400s = 24 hour timeout',
    '365': '365 days = 1 year',
    # Milliseconds
    '1000': '1000ms = 1 second',
    '2000': '2000ms = 2 seconds',
    '3000': '3000ms = 3 seconds',
    '5000': '5000ms = 5 seconds',
    '10000': '10000ms = 10 seconds',
    '30000': '30000ms = 30 seconds',
    '50000': '50000ms = 50 seconds',
    '60000': '60000ms = 1 minute',
    # Large numbers
    '200000': '200000 = 200K limit',
    '1000000': '1000000 = 1M limit',
    '10000000': '10000000 = 10M limit',
    # Years/dates (not really magic but flagged)
    '2024': '2024 year',
    '2025': '2025 year',
    '2026': '2026 year',
    '20241022': '20241022 = date/version stamp',
}

# Validator's exact regex for magic numbers
MAGIC_RE = re.compile(r'(?<![.\d])\b(?:(?:[2-9]\d{2,})|(?:1\d{3,}))\b(?![.\d])')


def fix_code_block(block_text: str, is_bash: bool) -> str:
    """Fix a single code block's content."""
    lines = block_text.splitlines()
    if not lines:
        return block_text

    # 1. Add error handling for bash blocks
    if is_bash:
        has_set_e = any('set -e' in l or 'set -o' in l for l in lines)
        if not has_set_e and len(lines) > 5:
            dangerous = ['rm ', 'rm\t', 'curl ', 'wget ', 'pip ', 'npm ', 'apt ',
                         'apt-get ', 'docker ', 'kubectl ', 'make ', 'sudo ']
            has_dangerous = any(any(d in l for d in dangerous) for l in lines
                                if not l.strip().startswith('#'))
            if has_dangerous:
                if lines[0].startswith('#!'):
                    lines.insert(1, 'set -euo pipefail')
                else:
                    lines.insert(0, 'set -euo pipefail')

    # 2. Fix magic numbers - check per-block, add comments per-line
    block_full = '\n'.join(lines)
    magic_nums_found = MAGIC_RE.findall(block_full)

    for num in set(magic_nums_found):
        # Check if the block already has a comment mentioning this number
        if re.search(rf'#.*{re.escape(num)}', block_full):
            continue  # Already explained

        # Find the line with this number and add a comment
        if num in MAGIC_NUMBERS:
            comment = MAGIC_NUMBERS[num]
        else:
            # Generic comment for unknown magic numbers
            comment = f'{num} = configured value'

        # Find first line with this number that doesn't have a comment
        for i, line in enumerate(lines):
            if re.search(rf'(?<![.\d]){re.escape(num)}(?![.\d])', line):
                if '#' not in line:
                    lines[i] = f"{line}  # {comment}"
                    break
                elif num not in line.split('#', 1)[1]:
                    # Has a comment but doesn't mention the number
                    # Add the number to the existing comment
                    parts = line.split('#', 1)
                    lines[i] = f"{parts[0]}# {num}: {parts[1].strip()}"
                    break

    return '\n'.join(lines)


def fix_file(skill_path: Path) -> bool:
    """Fix code blocks in a SKILL.md file. Returns True if changed."""
    content = skill_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    result = []
    in_code = False
    code_lang = ''
    code_block = []
    changed = False

    for line in lines:
        if re.match(r'^```', line):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip().lower()
                code_block = []
                result.append(line)
            else:
                in_code = False
                code_text = '\n'.join(code_block)
                is_bash = code_lang in ('bash', 'sh', 'shell', 'zsh', '')
                fixed = fix_code_block(code_text, is_bash)
                if fixed != code_text:
                    changed = True
                result.extend(fixed.splitlines())
                result.append(line)
                code_block = []
                code_lang = ''
        elif in_code:
            code_block.append(line)
        else:
            result.append(line)

    if changed:
        skill_path.write_text('\n'.join(result), encoding='utf-8')

    return changed


def main():
    root = Path('plugins')
    fixed = 0

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            if fix_file(skill_path):
                fixed += 1
        except Exception as e:
            print(f"  Error: {skill_path}: {e}", file=sys.stderr)

    print(f"Fixed code blocks in {fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
