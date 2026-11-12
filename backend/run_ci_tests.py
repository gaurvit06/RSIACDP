"""Run unit tests together and integration suites in isolated processes.

The API-flow module sets DATABASE_URL and UPLOAD_DIR before importing the app.
Run it in a fresh interpreter so another test module cannot initialize the
application's import-time engine and settings first.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent
TESTS = ROOT / "tests"
ISOLATED_MODULES = ("test_api_flow.py", "test_inline_worker_api.py", "test_proxy_headers.py")


def load_unit_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name in ISOLATED_MODULES:
            continue
        module_name = f"_rsaicdp_ci_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load test module {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def run_isolated(pattern: str) -> bool:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
    return subprocess.run(command, cwd=ROOT, check=False).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="run all non-HTTP unit/handler modules without the isolated API and proxy suites",
    )
    args = parser.parse_args()

    result = unittest.TextTestRunner(verbosity=2).run(load_unit_suite())
    success = result.wasSuccessful()
    if not args.unit_only:
        for pattern in ISOLATED_MODULES:
            print(f"\nRunning isolated integration suite: {pattern}", flush=True)
            success = run_isolated(pattern) and success
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
