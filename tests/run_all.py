"""Run every active regression suite from the project root.

Usage:
    python -X utf8 tests/run_all.py
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = [
    "tests/test_citation_integrity.py",
    "tests/test_eval_harness.py",
    "tests/test_measurement_integrity.py",
    "tests/test_rag_fallback.py",
]


def main() -> int:
    failures = []
    for rel in TESTS:
        print("\n" + "=" * 78)
        print(f"RUN {rel}")
        print("=" * 78, flush=True)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", os.path.join(BASE, rel)],
            cwd=BASE,
        )
        if proc.returncode != 0:
            failures.append(rel)
    print("\n" + "=" * 78)
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print(f"ALL {len(TESTS)} TEST SUITES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
