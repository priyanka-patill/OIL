"""
UI Label Compliance Test Suite

Scans all rendered frontend components and pages to ensure no forbidden internal development
phase labels (e.g., PART 4F, PART 2C, PART 3A-E, PART 4A-F, AI Engine (Disabled)) leak into user-facing UI text.
"""

import os
import re
import unittest

FORBIDDEN_PATTERNS = [
    r"PART\s+2C",
    r"PART\s+3A",
    r"PART\s+3B",
    r"PART\s+3C",
    r"PART\s+3D",
    r"PART\s+3E",
    r"PART\s+4A",
    r"PART\s+4B",
    r"PART\s+4C",
    r"PART\s+4D",
    r"PART\s+4E",
    r"PART\s+4F",
    r"AI\s+Engine\s+\(Disabled\)"
]


class TestUiLabelCompliance(unittest.TestCase):

    def setUp(self):
        self.frontend_src = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
        )

    def test_no_forbidden_labels_in_rendered_jsx(self):
        """Scans all .jsx / .js files in frontend/src and ensures zero forbidden labels in JSX content."""
        violations = []

        for root, _, files in os.walk(self.frontend_src):
            for file in files:
                if not (file.endswith(".jsx") or file.endswith(".tsx")):
                    continue

                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.frontend_src)

                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for line_idx, line in enumerate(lines, start=1):
                    # Skip code comments (starts with // or {/* ... */})
                    stripped = line.strip()
                    if stripped.startswith("//") or (stripped.startswith("{/*") and stripped.endswith("*/}")):
                        continue

                    for pattern in FORBIDDEN_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            violations.append(
                                f"{rel_path}:L{line_idx} matching pattern '{pattern}': {line.strip()}"
                            )

        if violations:
            self.fail(
                f"Found {len(violations)} user-facing UI label compliance violation(s):\n"
                + "\n".join(violations)
            )


if __name__ == "__main__":
    unittest.main()
