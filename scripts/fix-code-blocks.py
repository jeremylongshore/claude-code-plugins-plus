#!/usr/bin/env python3
"""
Fix code block warnings in SKILL.md files:
1. Add error handling (set -euo pipefail) to bash code blocks with dangerous commands
2. Add comments to magic numbers (ports, timeouts, HTTP status codes)
"""

import re
import sys
from pathlib import Path

# Common magic numbers and their meanings
MAGIC_NUMBERS = {
    # Ports
    '80': 'HTTP port',
    '443': 'HTTPS port',
    '3000': 'dev server port',
    '3001': 'alternate dev port',
    '3306': 'MySQL port',
    '4000': 'dev server port',
    '4200': 'Angular dev port',
    '4321': 'Astro dev port',
    '5000': 'Flask/dev port',
    '5173': 'Vite dev port',
    '5432': 'PostgreSQL port',
    '5672': 'RabbitMQ port',
    '6379': 'Redis port',
    '6380': 'Redis TLS port',
    '8000': 'API server port',
    '8080': 'HTTP proxy port',
    '8081': 'alternate HTTP port',
    '8443': 'HTTPS alternate port',
    '8888': 'Jupyter port',
    '9090': 'Prometheus port',
    '9092': 'Kafka port',
    '9200': 'Elasticsearch port',
    '9300': 'Elasticsearch transport port',
    '9411': 'Zipkin port',
    '15672': 'RabbitMQ management port',
    '16686': 'Jaeger UI port',
    '27017': 'MongoDB port',
    # Timeouts
    '200': 'HTTP 200 OK',
    '201': 'HTTP 201 Created',
    '204': 'HTTP 204 No Content',
    '301': 'HTTP 301 Moved Permanently',
    '302': 'HTTP 302 Found (redirect)',
    '304': 'HTTP 304 Not Modified',
    '400': 'HTTP 400 Bad Request',
    '401': 'HTTP 401 Unauthorized',
    '403': 'HTTP 403 Forbidden',
    '404': 'HTTP 404 Not Found',
    '408': 'HTTP 408 Request Timeout',
    '409': 'HTTP 409 Conflict',
    '422': 'HTTP 422 Unprocessable Entity',
    '429': 'HTTP 429 Too Many Requests',
    '500': 'HTTP 500 Internal Server Error',
    '502': 'HTTP 502 Bad Gateway',
    '503': 'HTTP 503 Service Unavailable',
    '504': 'HTTP 504 Gateway Timeout',
    # Sizes/limits
    '1024': '1 KB',
    '2048': '2 KB',
    '4096': '4 KB',
    '8192': '8 KB',
    '65535': 'max port number',
    # Timeouts (seconds)
    '300': 'timeout: 5 minutes',
    '600': 'timeout: 10 minutes',
    '900': 'timeout: 15 minutes',
    '1800': 'timeout: 30 minutes',
    '3600': 'timeout: 1 hour',
    '7200': 'timeout: 2 hours',
    '86400': 'timeout: 24 hours',
    # Retries/intervals
    '1000': '1 second in ms',
    '2000': '2 seconds in ms',
    '3000': '3 seconds in ms',
    '5000': '5 seconds in ms',
    '10000': '10 seconds in ms',
    '30000': '30 seconds in ms',
    '60000': '1 minute in ms',
}

# Pattern to find magic numbers in code block lines
# Match numbers >= 200 that appear as standalone values (not array indices, version numbers, etc.)
MAGIC_NUM_PATTERN = re.compile(
    r'(?<![.\d_a-zA-Z])(\d{3,5})(?![.\d_a-zA-Z])'
)


def add_error_handling_to_bash(code: str) -> str:
    """Add set -euo pipefail to bash blocks that have dangerous commands."""
    lines = code.splitlines()
    if not lines:
        return code

    # Check if already has error handling
    has_set_e = any('set -e' in l or 'set -o' in l for l in lines)
    if has_set_e:
        return code

    # Check if has dangerous commands
    dangerous = ['rm ', 'rm\t', 'curl ', 'wget ', 'pip ', 'npm ', 'apt ', 'apt-get ',
                 'docker ', 'kubectl ', 'make ', 'sudo ']
    has_dangerous = any(any(d in l for d in dangerous) for l in lines
                        if not l.strip().startswith('#'))
    if not has_dangerous:
        return code

    # Add set -euo pipefail after shebang or at top
    if lines[0].startswith('#!'):
        lines.insert(1, 'set -euo pipefail')
    else:
        lines.insert(0, 'set -euo pipefail')

    return '\n'.join(lines)


def comment_magic_numbers(line: str) -> str:
    """Add inline comment for magic numbers in a code line."""
    if '#' in line:  # Already has a comment
        return line

    matches = MAGIC_NUM_PATTERN.findall(line)
    for num in matches:
        if num in MAGIC_NUMBERS:
            return f"{line}  # {MAGIC_NUMBERS[num]}"

    return line


def fix_code_blocks(content: str) -> str:
    """Fix code blocks in SKILL.md content."""
    lines = content.splitlines()
    result = []
    in_code = False
    code_lang = ''
    code_block = []

    for line in lines:
        if re.match(r'^```', line):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip().lower()
                code_block = []
                result.append(line)
            else:
                # End of code block
                in_code = False

                # Process the code block
                code_text = '\n'.join(code_block)

                if code_lang in ('bash', 'sh', 'shell', 'zsh', ''):
                    code_text = add_error_handling_to_bash(code_text)

                # Comment magic numbers in all code blocks
                processed_lines = []
                for cl in code_text.splitlines():
                    processed_lines.append(comment_magic_numbers(cl))
                code_text = '\n'.join(processed_lines)

                result.extend(code_text.splitlines())
                result.append(line)
                code_block = []
                code_lang = ''
        elif in_code:
            code_block.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def main():
    root = Path('plugins')
    fixed = 0

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            content = skill_path.read_text(encoding='utf-8')
            new_content = fix_code_blocks(content)
            if new_content != content:
                skill_path.write_text(new_content, encoding='utf-8')
                fixed += 1
        except Exception as e:
            print(f"  Error: {skill_path}: {e}", file=sys.stderr)

    print(f"Fixed code blocks in {fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
