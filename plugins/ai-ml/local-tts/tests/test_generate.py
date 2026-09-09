#!/usr/bin/env python3
"""Basic tests for the Local TTS generate.py script."""
import subprocess
import sys
import os
import json

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate.py')


def test_help():
    """Script should show help and exit 0."""
    result = subprocess.run(
        [sys.executable, SCRIPT, '--help'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'Local TTS via VoxCPM2' in result.stdout


def test_no_text_error():
    """Script should error when no text is provided."""
    result = subprocess.run(
        [sys.executable, SCRIPT, '--out', '/tmp/test_notxt.wav'],
        capture_output=True, text=True
    )
    assert result.returncode == 2
    assert 'no text provided' in result.stderr


def test_prompt_wav_without_text_error():
    """Script should error when --prompt-wav is used without --prompt-text."""
    result = subprocess.run(
        [sys.executable, SCRIPT, '--text', 'hello', '--prompt-wav', '/tmp/fake.wav', '--out', '/tmp/test.wav'],
        capture_output=True, text=True
    )
    assert result.returncode == 2
    assert 'prompt-text' in result.stderr


def test_skill_md_frontmatter():
    """SKILL.md should have required frontmatter fields."""
    skill_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'local-tts', 'SKILL.md')
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
    assert data['name'] == 'local-tts'


if __name__ == '__main__':
    tests = [test_help, test_no_text_error, test_prompt_wav_without_text_error,
             test_skill_md_frontmatter, test_plugin_json]
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
