#!/usr/bin/env python3
"""
CHANGELOG Auto-Update Script

Updates CHANGELOG.md with new entry when PR is merged.

Usage:
    python update_changelog.py --type Added --description "Feature X" --pr-number 123
"""

import argparse
import re
from datetime import datetime
from pathlib import Path


def update_changelog(changelog_path: str, entry_type: str, description: str, pr_number: int) -> bool:
    """Add entry to CHANGELOG Unreleased section."""
    changelog_file = Path(changelog_path)

    if not changelog_file.exists():
        print(f"❌ CHANGELOG not found at {changelog_path}")
        return False

    content = changelog_file.read_text(encoding='utf-8')

    # Find the Unreleased section and the target section type (Added, Fixed, etc.)
    unreleased_pattern = r'(## \[Unreleased\]\n)(### Added\n(.*?)(?=###|---|\Z)|(?!### Added))'

    entry = f"- **{description}** (PR #{pr_number})"

    # Check if Unreleased and target section exist
    if '## [Unreleased]' not in content:
        print("❌ No [Unreleased] section found in CHANGELOG")
        return False

    # Find the target section (Added, Fixed, etc.)
    section_pattern = f'(### {entry_type}\n)'

    if re.search(section_pattern, content):
        # Section exists, add entry at the beginning of section
        new_content = re.sub(
            f'(### {entry_type}\n)',
            f'### {entry_type}\n{entry}\n',
            content,
            count=1
        )
    else:
        # Section doesn't exist, create it after Unreleased header
        unreleased_pos = content.find('## [Unreleased]')
        if unreleased_pos == -1:
            print("❌ Could not find [Unreleased] section")
            return False

        # Find the end of Unreleased header
        newline_pos = content.find('\n', unreleased_pos)
        insert_pos = newline_pos + 1

        # Check if there's already content after Unreleased
        next_section = content.find('### ', insert_pos)
        if next_section != -1:
            insert_pos = next_section
            new_section = f'### {entry_type}\n{entry}\n\n'
        else:
            new_section = f'\n### {entry_type}\n{entry}\n'

        new_content = content[:insert_pos] + new_section + content[insert_pos:]

    # Write updated CHANGELOG
    changelog_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Added {entry_type}: {description} (PR #{pr_number})")
    return True


def main():
    parser = argparse.ArgumentParser(description='Auto-update CHANGELOG from merged PR')
    parser.add_argument('--type', required=True, help='Entry type (Added, Fixed, Changed, Removed, Security)')
    parser.add_argument('--description', required=True, help='Entry description')
    parser.add_argument('--pr-number', type=int, required=True, help='PR number')
    parser.add_argument('--changelog', default='CHANGELOG.md', help='Path to CHANGELOG.md')

    args = parser.parse_args()

    # Validate entry type
    valid_types = ['Added', 'Fixed', 'Changed', 'Removed', 'Security']
    if args.type not in valid_types:
        print(f"❌ Invalid type '{args.type}'. Must be one of: {', '.join(valid_types)}")
        return 1

    success = update_changelog(args.changelog, args.type, args.description, args.pr_number)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
