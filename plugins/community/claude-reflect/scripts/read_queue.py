#!/usr/bin/env python3
"""Print the current project's learnings queue as JSON. Helper for slash commands."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import load_queue
import json

print(json.dumps(load_queue(), indent=2))
