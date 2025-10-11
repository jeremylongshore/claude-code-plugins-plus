#!/usr/bin/env python3
"""
Professional Emoji Removal Script
Removes all emojis from Claude Code Plugins repository for professional presentation
"""

import os
import re
import shutil
from pathlib import Path

# Define the emoji pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # Miscellaneous Symbols and Pictographs, Emoticons, etc
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U00002600-\U000026FF"  # Miscellaneous Symbols
    "\U00002700-\U000027BF"  # Dingbats
    "\U0001F1E0-\U0001F1FF"  # Regional indicators (flags)
    "\U00002B50-\U00002B55"  # Stars
    "\U0001F004-\U0001F0CF"  # Mahjong/Playing cards
    "\U0001F200-\U0001F2FF"  # Enclosed characters
    "]+",
    flags=re.UNICODE
)

# Base directory
BASE_DIR = Path("/home/jeremy/projects/claude-code-plugins")

# File extensions to process
EXTENSIONS = {'.md', '.astro', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.json', '.yml', '.yaml', '.txt'}

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', 'dist', '.cache', '.astro'}

def should_process_file(filepath):
    """Determine if a file should be processed"""
    path = Path(filepath)

    # Skip if in a directory we should ignore
    for parent in path.parents:
        if parent.name in SKIP_DIRS:
            return False

    # Skip if not a supported extension
    if path.suffix not in EXTENSIONS:
        return False

    return True

def remove_emojis_from_file(filepath):
    """Remove emojis from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, FileNotFoundError):
        return False

    # Check if content has emojis
    if not EMOJI_PATTERN.search(content):
        return False

    # Remove emojis
    cleaned_content = EMOJI_PATTERN.sub('', content)

    # Create backup
    backup_path = str(filepath) + '.bak'
    shutil.copy2(filepath, backup_path)

    # Write cleaned content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    # Remove backup
    os.remove(backup_path)

    return True

def main():
    print("=== PROFESSIONAL EMOJI REMOVAL ===")
    print("Cleaning repository for professional presentation\n")

    total_files = 0
    modified_files = 0

    # Walk through all files
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            filepath = os.path.join(root, filename)

            if should_process_file(filepath):
                total_files += 1

                if remove_emojis_from_file(filepath):
                    modified_files += 1
                    # Print relative path for cleaner output
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                    print(f"  [CLEANED] {rel_path}")

    print(f"\n=== EMOJI REMOVAL COMPLETE ===")
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"\nRepository is now professional and emoji-free.")

if __name__ == "__main__":
    main()