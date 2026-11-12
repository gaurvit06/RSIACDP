"""Checks that HTTP integration suites remain isolated from app imports."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


RUNNER_PATH = Path(__file__).resolve().parents[1] / "run_ci_tests.py"
SPEC = importlib.util.spec_from_file_location("rsaicdp_ci_runner_under_test", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load backend CI test runner")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class CiRunnerTests(unittest.TestCase):
    def test_api_flow_and_proxy_suites_are_explicitly_isolated(self):
        self.assertEqual(
            runner.ISOLATED_MODULES,
            ("test_api_flow.py", "test_inline_worker_api.py", "test_proxy_headers.py"),
        )

    def test_isolated_suite_runs_unittest_in_a_fresh_interpreter(self):
        expected = [
            runner.sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_api_flow.py",
            "-v",
        ]
        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            self.assertTrue(runner.run_isolated("test_api_flow.py"))
        run.assert_called_once_with(expected, cwd=runner.ROOT, check=False)

    def test_failed_isolated_suite_is_reported_as_failure(self):
        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
            self.assertFalse(runner.run_isolated("test_proxy_headers.py"))


if __name__ == "__main__":
    unittest.main()
