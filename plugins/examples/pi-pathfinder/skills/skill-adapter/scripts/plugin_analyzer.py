#!/usr/bin/env python3
"""
pi-pathfinder - Analysis Script
Analyzes a given plugin directory, extracts skill descriptions, and returns a structured summary.
Generated: 2025-12-10 03:48:17
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class Analyzer:
    def __init__(self, target_path: str):
        self.target_path = Path(target_path)
        self.stats = {
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'issues': [],
            'recommendations': []
        }

    def analyze_directory(self) -> Dict:
        """Analyze directory structure and contents."""
        if not self.target_path.exists():
            self.stats['issues'].append(f"Path does not exist: {self.target_path}")
            return self.stats

        for file_path in self.target_path.rglob('*'):
            if file_path.is_file():
                self.analyze_file(file_path)

        return self.stats

    def analyze_file(self, file_path: Path):
        """Analyze individual file."""
        self.stats['total_files'] += 1
        self.stats['total_size'] += file_path.stat().st_size

        # Track file types
        ext = file_path.suffix.lower()
        if ext:
            self.stats['file_types'][ext] = self.stats['file_types'].get(ext, 0) + 1

        # Check for potential issues
        if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
            self.stats['issues'].append(f"Large file: {file_path} ({file_path.stat().st_size // 1024 // 1024}MB)")

        if file_path.stat().st_size == 0:
            self.stats['issues'].append(f"Empty file: {file_path}")

    def generate_recommendations(self):
        """Generate recommendations based on analysis."""
        if self.stats['total_files'] == 0:
            self.stats['recommendations'].append("No files found - check target path")

        if len(self.stats['file_types']) > 20:
            self.stats['recommendations'].append("Many file types detected - consider organizing")

        if self.stats['total_size'] > 1024 * 1024 * 1024:  # 1GB
            self.stats['recommendations'].append("Large total size - consider archiving old data")

    def generate_report(self) -> str:
        """Generate analysis report."""
        report = []
        report.append("\n" + "="*60)
        report.append(f"ANALYSIS REPORT - pi-pathfinder")
        report.append("="*60)
        report.append(f"Target: {self.target_path}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Statistics
        report.append("📊 STATISTICS")
        report.append(f"  Total Files: {self.stats['total_files']:,}")
        report.append(f"  Total Size: {self.stats['total_size'] / 1024 / 1024:.2f} MB")
        report.append(f"  File Types: {len(self.stats['file_types'])}")

        # Top file types
        if self.stats['file_types']:
            report.append("\n📁 TOP FILE TYPES")
            sorted_types = sorted(self.stats['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
            for ext, count in sorted_types:
                report.append(f"  {ext or 'no extension'}: {count} files")

        # Issues
        if self.stats['issues']:
            report.append(f"\n⚠️  ISSUES ({len(self.stats['issues'])})")
            for issue in self.stats['issues'][:10]:
                report.append(f"  - {issue}")
            if len(self.stats['issues']) > 10:
                report.append(f"  ... and {len(self.stats['issues']) - 10} more")

        # Recommendations
        if self.stats['recommendations']:
            report.append("\n💡 RECOMMENDATIONS")
            for rec in self.stats['recommendations']:
                report.append(f"  - {rec}")

        report.append("")
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Analyzes a given plugin directory, extracts skill descriptions, and returns a structured summary.")
    parser.add_argument('target', help='Target directory to analyze')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    print(f"🔍 Analyzing {args.target}...")
    analyzer = Analyzer(args.target)
    stats = analyzer.analyze_directory()
    analyzer.generate_recommendations()

    if args.json:
        output = json.dumps(stats, indent=2)
    else:
        output = analyzer.generate_report()

    if args.output:
        Path(args.output).write_text(output)
        print(f"✓ Report saved to {args.output}")
    else:
        print(output)

    return 0 if len(stats['issues']) == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
