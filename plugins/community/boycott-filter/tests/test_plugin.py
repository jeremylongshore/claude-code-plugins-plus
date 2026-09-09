#!/usr/bin/env python3
"""Basic tests for the Boycott Filter plugin structure."""
import os
import json
import sys


def test_skill_md_frontmatter():
    """SKILL.md should have required frontmatter fields."""
    skill_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'boycott-filter', 'SKILL.md')
    with open(skill_path) as f:
        content = f.read()
    assert content.startswith('---')
    for field in ['name:', 'description:', 'version:', 'author:', 'license:', 'allowed-tools:']:
        assert field in content, f'Missing frontmatter field: {field}'


def test_plugin_json():
    """plugin.json should have all required fields."""
    pj_path = os.path.join(os.path.dirname(__file__), '..', '.claude-plugin', 'plugin.json')
    with open(pj_path) as f:
        data = json.load(f)
    for field in ['name', 'description', 'version', 'author', 'license']:
        assert field in data, f'Missing plugin.json field: {field}'
    assert data['name'] == 'boycott-filter'


def test_marketplace_json():
    """marketplace.json should be valid and reference the plugin."""
    mp_path = os.path.join(os.path.dirname(__file__), '..', '.claude-plugin', 'marketplace.json')
    with open(mp_path) as f:
        data = json.load(f)
    assert 'name' in data
    assert 'plugins' in data
    assert len(data['plugins']) > 0
    assert data['plugins'][0]['name'] == 'boycott-filter'


def test_extension_manifest():
    """Chrome extension should have a valid manifest.json."""
    ext_path = os.path.join(os.path.dirname(__file__), '..', 'extension', 'manifest.json')
    if os.path.exists(ext_path):
        with open(ext_path) as f:
            data = json.load(f)
        assert 'name' in data
        assert 'version' in data
        assert 'manifest_version' in data


def test_no_secrets():
    """Scripts should not contain hardcoded API keys or tokens."""
    scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    import re
    secret_patterns = [
        r'sk[-_][a-zA-Z0-9]{20,}',
        r'AKIA[A-Z0-9]{16}',
        r'ghp_[a-zA-Z0-9]{36}',
    ]
    for root, dirs, files in os.walk(scripts_dir):
        for f in files:
            filepath = os.path.join(root, f)
            with open(filepath) as fh:
                content = fh.read()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content)
                assert not matches, f'Potential secret in {f}: {matches[0][:20]}...'


if __name__ == '__main__':
    tests = [test_skill_md_frontmatter, test_plugin_json, test_marketplace_json,
             test_extension_manifest, test_no_secrets]
    passed = 0
    for t in tests:
        try:
            t()
            print(f'  PASS: {t.__name__}')
            passed += 1
        except Exception as e:
            print(f'  FAIL: {t.__name__} — {e}')
    print(f'\n{passed}/{len(tests)} tests passed')
    sys.exit(0 if passed == len(tests) else 1)
