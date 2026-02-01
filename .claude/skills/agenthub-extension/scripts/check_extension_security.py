#!/usr/bin/env python3
"""
Chrome Extension Security Scanner for AgentHub

Scans extension code for common security vulnerabilities:
- XSS risks (innerHTML with external data)
- Token leakage (console.log with tokens)
- CSP violations (inline scripts, eval)
- Insecure storage (tokens in localStorage)
- Missing authentication headers
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Security patterns to detect
SECURITY_PATTERNS = {
    'xss_innerHTML': {
        'pattern': r'\.innerHTML\s*=(?!\s*[\'"`])',
        'severity': 'HIGH',
        'message': 'Potential XSS: innerHTML with dynamic content. Use textContent or createElement.',
    },
    'token_console_log': {
        'pattern': r'console\.(log|info|debug|warn)\([^)]*[Tt]oken',
        'severity': 'HIGH',
        'message': 'Token leakage: Logging token to console.',
    },
    'inline_script': {
        'pattern': r'<script[^>]*>(?!.*src=)',
        'severity': 'MEDIUM',
        'message': 'CSP violation: Inline script detected. Use external script files.',
    },
    'inline_handler': {
        'pattern': r'on(click|load|error|submit)\s*=',
        'severity': 'MEDIUM',
        'message': 'CSP violation: Inline event handler. Use addEventListener instead.',
    },
    'eval_usage': {
        'pattern': r'\beval\s*\(',
        'severity': 'HIGH',
        'message': 'CSP violation: eval() is not allowed in Manifest V3.',
    },
    'new_function': {
        'pattern': r'new\s+Function\s*\(',
        'severity': 'HIGH',
        'message': 'CSP violation: new Function() is not allowed in Manifest V3.',
    },
    'local_storage_token': {
        'pattern': r'localStorage\.(set|get)Item\([^)]*[Tt]oken',
        'severity': 'MEDIUM',
        'message': 'Insecure storage: Tokens should use chrome.storage.session, not localStorage.',
    },
    'missing_auth_header': {
        'pattern': r'fetch\([^)]*localhost:8000(?![^)]*X-Extension-Token)',
        'severity': 'HIGH',
        'message': 'Missing authentication: API request without X-Extension-Token header.',
    },
}

class SecurityIssue:
    def __init__(self, file_path: Path, line_num: int, severity: str, message: str, line: str):
        self.file_path = file_path
        self.line_num = line_num
        self.severity = severity
        self.message = message
        self.line = line.strip()

    def __repr__(self):
        return f"{self.severity}: {self.file_path}:{self.line_num} - {self.message}\n  {self.line}"


def scan_file(file_path: Path) -> List[SecurityIssue]:
    """Scan a single file for security issues."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            for pattern_name, config in SECURITY_PATTERNS.items():
                if re.search(config['pattern'], line):
                    issues.append(SecurityIssue(
                        file_path=file_path,
                        line_num=line_num,
                        severity=config['severity'],
                        message=config['message'],
                        line=line,
                    ))

    except Exception as e:
        print(f"Error scanning {file_path}: {e}", file=sys.stderr)

    return issues


def scan_directory(directory: Path, extensions: Tuple[str, ...] = ('.ts', '.tsx', '.js', '.jsx', '.html')) -> List[SecurityIssue]:
    """Scan all files in directory recursively."""
    all_issues = []

    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            # Skip node_modules and build outputs
            if 'node_modules' in file_path.parts or '.output' in file_path.parts:
                continue

            issues = scan_file(file_path)
            all_issues.extend(issues)

    return all_issues


def print_report(issues: List[SecurityIssue]):
    """Print security scan report."""
    if not issues:
        print("✅ No security issues found!")
        return

    # Group by severity
    high = [i for i in issues if i.severity == 'HIGH']
    medium = [i for i in issues if i.severity == 'MEDIUM']
    low = [i for i in issues if i.severity == 'LOW']

    print(f"\n{'='*60}")
    print(f"Security Scan Results: {len(issues)} issues found")
    print(f"{'='*60}\n")

    if high:
        print(f"❌ HIGH Severity Issues ({len(high)}):")
        print("-" * 60)
        for issue in high:
            print(issue)
            print()

    if medium:
        print(f"⚠️  MEDIUM Severity Issues ({len(medium)}):")
        print("-" * 60)
        for issue in medium:
            print(issue)
            print()

    if low:
        print(f"ℹ️  LOW Severity Issues ({len(low)}):")
        print("-" * 60)
        for issue in low:
            print(issue)
            print()

    # Exit code
    if high:
        sys.exit(1)  # Fail on high severity
    elif medium:
        sys.exit(0)  # Warn but pass on medium
    else:
        sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_extension_security.py <extension_directory>")
        print("\nExample:")
        print("  python check_extension_security.py ./extension")
        sys.exit(1)

    extension_dir = Path(sys.argv[1])

    if not extension_dir.exists():
        print(f"Error: Directory not found: {extension_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning extension directory: {extension_dir}")
    print(f"Looking for: TypeScript, JavaScript, HTML files")
    print()

    issues = scan_directory(extension_dir)
    print_report(issues)


if __name__ == '__main__':
    main()
