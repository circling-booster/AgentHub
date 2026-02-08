#!/usr/bin/env python3
"""
Documentation Structure Validator

Validates that:
1. All paths referenced in MAP.md exist
2. All section directories have README.md
3. No broken links in core documentation
4. Documentation structure matches best practices

Usage:
    python scripts/validate_docs.py
    python scripts/validate_docs.py --fix  # Auto-create missing READMEs
"""

import argparse
import re
import sys
from pathlib import Path


class DocValidator:
    def __init__(self, root: Path):
        self.root = root
        self.docs_dir = root / "docs"
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks. Returns True if all passed."""
        print("🔍 Validating documentation structure...\n")

        self.check_core_files()
        self.check_map_references()
        self.check_section_readmes()
        self.check_depth_limits()
        self.check_llms_txt()

        self.print_results()
        return len(self.errors) == 0

    def check_core_files(self):
        """Verify core documentation files exist."""
        core_files = [
            self.root / "CLAUDE.md",
            self.root / "README.md",
            self.docs_dir / "MAP.md",
            self.root / "tests" / "README.md",
        ]

        for file_path in core_files:
            if not file_path.exists():
                self.errors.append(f"Missing core file: {file_path.relative_to(self.root)}")
            else:
                self.info.append(f"✓ Found: {file_path.relative_to(self.root)}")

    def check_map_references(self):
        """Check that paths mentioned in MAP.md exist."""
        map_file = self.docs_dir / "MAP.md"
        if not map_file.exists():
            return

        content = map_file.read_text(encoding="utf-8")

        # Extract markdown links: [text](path)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, content)

        checked_paths = set()
        for text, link in links:
            # Skip external links and anchors
            if link.startswith(("http://", "https://", "#")):
                continue

            # Convert relative link to absolute path
            full_path = (self.docs_dir / link).resolve()

            # Avoid duplicate checks
            if str(full_path) in checked_paths:
                continue
            checked_paths.add(str(full_path))

            if not full_path.exists():
                # Check if it's a directory reference without README.md
                if not link.endswith("README.md") and (full_path.parent / (full_path.name + ".md")).exists():
                    continue

                self.errors.append(
                    f"MAP.md references non-existent path: {link} "
                    f"(resolved to: {full_path.relative_to(self.root)})"
                )

    def check_section_readmes(self):
        """Verify all section directories have README.md."""
        required_sections = [
            self.docs_dir / "developers",
            self.docs_dir / "operators",
            self.docs_dir / "project",
        ]

        for section in required_sections:
            if not section.exists():
                self.warnings.append(f"Missing section directory: {section.relative_to(self.root)}")
                continue

            readme = section / "README.md"
            if not readme.exists():
                self.errors.append(f"Missing README.md in: {section.relative_to(self.root)}")
            else:
                self.info.append(f"✓ Section README: {section.name}/README.md")

            # Check subsections (1 level deep only)
            for subdir in section.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("."):
                    sub_readme = subdir / "README.md"
                    if not sub_readme.exists():
                        self.warnings.append(
                            f"Subsection missing README.md: {subdir.relative_to(self.docs_dir)}"
                        )

    def check_depth_limits(self):
        """Check that documentation doesn't exceed 3-level depth."""
        max_depth = 3

        for path in self.docs_dir.rglob("*.md"):
            relative = path.relative_to(self.docs_dir)
            depth = len(relative.parts) - 1  # Subtract 1 for the file itself

            if depth > max_depth:
                self.warnings.append(
                    f"Exceeds {max_depth}-level depth: {relative} (depth: {depth})"
                )

    def check_llms_txt(self):
        """Verify llms.txt exists and references core files."""
        llms_txt = self.docs_dir / "llms.txt"

        if not llms_txt.exists():
            self.warnings.append("Missing docs/llms.txt (AI accessibility standard)")
            return

        content = llms_txt.read_text(encoding="utf-8")

        # Check for essential references
        essential = ["/CLAUDE.md", "/docs/MAP.md", "/tests/README.md"]
        for ref in essential:
            if ref not in content:
                self.warnings.append(f"llms.txt missing reference to: {ref}")

        # Validate that all referenced paths actually exist
        import re
        # Match lines starting with "- /" (file references in llms.txt)
        path_pattern = r'^- (/[^\s]+)'
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(path_pattern, line.strip())
            if match:
                ref_path = match.group(1)
                # Convert to actual file path (remove leading /)
                actual_path = self.root / ref_path.lstrip('/')

                # Check if it's a file or directory reference
                if not actual_path.exists():
                    # Try adding .md if it's missing
                    if not ref_path.endswith('.md') and not (self.root / (ref_path.lstrip('/') + '/README.md')).exists():
                        self.warnings.append(
                            f"llms.txt line {line_num} references non-existent path: {ref_path}"
                        )

        self.info.append("✓ llms.txt exists and core paths validated")

    def print_results(self):
        """Print validation results."""
        print("\n" + "=" * 70)

        if self.info:
            print("\n📋 Info:")
            for msg in self.info:
                print(f"  {msg}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for msg in self.warnings:
                print(f"  {msg}")

        if self.errors:
            print("\n❌ Errors:")
            for msg in self.errors:
                print(f"  {msg}")

        print("\n" + "=" * 70)
        print(f"\nSummary: {len(self.errors)} errors, {len(self.warnings)} warnings")

        if len(self.errors) == 0 and len(self.warnings) == 0:
            print("✅ All documentation validation checks passed!")
        elif len(self.errors) == 0:
            print("✅ No critical errors, but warnings should be addressed.")
        else:
            print("❌ Validation failed. Please fix the errors above.")


def main():
    parser = argparse.ArgumentParser(description="Validate documentation structure")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-create missing README.md files (not implemented yet)",
    )

    args = parser.parse_args()

    validator = DocValidator(args.root)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
