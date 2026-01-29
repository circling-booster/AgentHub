"""문서 참조 검증 - CLAUDE.md, README.md, roadmap.md

@경로 참조가 실제 파일을 가리키는지 검증합니다.
누락된 참조 발견 시 경고를 출력합니다.
"""

import re
import sys
from pathlib import Path


def validate_file_references(file_path: str, pattern: str) -> list[str]:
    """파일 내 @경로 참조 검증"""
    path = Path(file_path)
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    references = re.findall(pattern, content)

    missing = []
    for ref in references:
        # @docs/... 또는 @.claude/... 형태에서 경로 추출
        if "/" not in ref:
            continue
        # #앵커 제거 (예: @docs/guide.md#section → docs/guide.md)
        clean_ref = ref.split("#")[0]
        if not Path(clean_ref).exists():
            missing.append(f"{file_path}: @{ref} 파일 없음")

    return missing


def main() -> int:
    files_to_check = {
        "CLAUDE.md": r"@([^\s\)]+)",
        "README.md": r"@([^\s\)]+)",
        "docs/roadmap.md": r"@([^\s\)]+)",
    }

    all_missing: list[str] = []
    for file_path, pattern in files_to_check.items():
        missing = validate_file_references(file_path, pattern)
        all_missing.extend(missing)

    if all_missing:
        print("Missing file references found:")
        for msg in all_missing:
            print(f"   {msg}")
        return 1

    print("All file references valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
