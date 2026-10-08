"""Run the offline suite and persist the audit-friendly result files."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()


def main():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_agent_rag.py")
    tests = list(flatten(suite))
    # Discovery consumes nested suite iterators, so build a fresh suite to run.
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_agent_rag.py")
    text_path = HERE / "evidence" / "offline_tests.txt"
    with text_path.open("w") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    test_file = HERE / "test_agent_rag.py"
    payload = {
        "tests": tests,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failures": [test.id() for test, _ in result.failures],
        "errors": [test.id() for test, _ in result.errors],
        "test_file_sha256": hashlib.sha256(test_file.read_bytes()).hexdigest(),
    }
    (HERE / "evidence" / "offline_tests.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    if result.failures or result.errors:
        raise SystemExit(1)
    print(f"{payload['passed']} offline tests passed")


if __name__ == "__main__":
    main()
