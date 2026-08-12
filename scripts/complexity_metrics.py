#!/usr/bin/env python3
"""
Check complexity metrics for the quality gate (Contract 2).

Maintainability Index follows a two-tier blocking scheme:
- worst MI >= 70 -> pass (exit 0)
- 30 <= worst MI < 70 -> [Warning], non-blocking (exit 0)
- worst MI < 30 -> [Blocking], **fails the gate** (exit 1)
- empty/unparseable MI -> treated as blocking (fail-loud), never a silent pass.

Halstead metrics are reported as warning/informational and never fail the gate.
"""

import re
import subprocess
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RADON = ROOT / ".venv" / "bin" / "radon"
IGNORE = "tests,build,dist,ccache,mutants,.venv,.opencode"


def _radon_mi() -> str:
    result = subprocess.run(
        [str(RADON), "mi", "-s", "-i", IGNORE, "src/"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def main() -> int:
    output = _radon_mi()
    print(output.rstrip())
    scores = [float(m) for m in re.findall(r"\(([\d.]+)\)\s*$", output, re.MULTILINE)]
    if not scores:
        print("[BLOCKING] Maintainability Index: no modules evaluated (fail-loud)")
        return 1
    worst = min(scores)
    if worst < 30:
        print(f"[BLOCKING] Maintainability Index: worst {worst:.1f} < 30")
        return 1
    if worst < 70:
        print(f"[WARNING] Maintainability Index: worst {worst:.1f} (30-70, non-blocking)")
        return 0
    print(f"[PASS] Maintainability Index: worst {worst:.1f} >= 70")
    return 0


if __name__ == "__main__":
    sys.exit(main())
