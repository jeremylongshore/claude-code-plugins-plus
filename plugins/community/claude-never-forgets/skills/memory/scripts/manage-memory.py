#!/usr/bin/env python3
"""
manage-memory.py - Manage project memories for Claude Never Forgets

Supports:
- Adding new memories
- Listing all memories
- Removing memories
- Searching memories
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MemoryManager:
    def __init__(self, memory_file: str = ".memories/project_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.memory_file.exists():
            self._initialize_memory_file()

    def _initialize_memory_file(self):
        """Initialize empty memory file"""
        initial_data = {
            "project_memories": [],
            "manual_memories": [],
            "last_updated": datetime.now().isoformat()
        }
        self._save_memories(initial_data)

    def _load_memories(self) -> Dict:
        """Load memories from file"""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memories: {e}")
            return {"project_memories": [], "manual_memories": []}

    def _save_memories(self, data: Dict):
        """Save memories to file"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_memory(self, text: str, category: str = "manual"):
        """Add a new memory"""
        memories = self._load_memories()

        memory_entry = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "category": category
        }

        if category == "manual":
            memories["manual_memories"].append(memory_entry)
        else:
            memories["project_memories"].append(memory_entry)

        self._save_memories(memories)
        print(f"✓ Memory added: {text[:50]}...")

    def list_memories(self):
        """List all memories"""
        memories = self._load_memories()

        print("\nProject Memories:")
        print("=" * 70)
        for i, mem in enumerate(memories.get("project_memories", []), 1):
            print(f"{i}. {mem['text']}")
            print(f"   Added: {mem['timestamp']}")
            print()

        print("\nManual Memories:")
        print("=" * 70)
        for i, mem in enumerate(memories.get("manual_memories", []), 1):
            print(f"{i}. {mem['text']}")
            print(f"   Added: {mem['timestamp']}")
            print()

    def remove_memory(self, text: str):
        """Remove memory by text match"""
        memories = self._load_memories()
        removed = False

        # Check project memories
        memories["project_memories"] = [
            m for m in memories["project_memories"]
            if text.lower() not in m["text"].lower()
        ]

        # Check manual memories
        original_count = len(memories["manual_memories"])
        memories["manual_memories"] = [
            m for m in memories["manual_memories"]
            if text.lower() not in m["text"].lower()
        ]

        if len(memories["manual_memories"]) < original_count:
            removed = True

        if removed:
            self._save_memories(memories)
            print(f"✓ Memory removed: {text}")
        else:
            print(f"✗ No matching memory found")

    def search_memories(self, query: str):
        """Search memories by query"""
        memories = self._load_memories()
        results = []

        for mem in memories.get("project_memories", []) + memories.get("manual_memories", []):
            if query.lower() in mem["text"].lower():
                results.append(mem)

        print(f"\nFound {len(results)} matching memories:")
        print("=" * 70)
        for mem in results:
            print(f"• {mem['text']}")
            print(f"  Added: {mem['timestamp']}")
            print()


def main():
    if len(sys.argv) < 2:
        print("Usage: manage-memory.py <command> [args]")
        print("\nCommands:")
        print("  add <text>       - Add new memory")
        print("  list             - List all memories")
        print("  remove <text>    - Remove memory")
        print("  search <query>   - Search memories")
        sys.exit(1)

    manager = MemoryManager()
    command = sys.argv[1]

    if command == "add" and len(sys.argv) > 2:
        manager.add_memory(" ".join(sys.argv[2:]))
    elif command == "list":
        manager.list_memories()
    elif command == "remove" and len(sys.argv) > 2:
        manager.remove_memory(" ".join(sys.argv[2:]))
    elif command == "search" and len(sys.argv) > 2:
        manager.search_memories(" ".join(sys.argv[2:]))
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
