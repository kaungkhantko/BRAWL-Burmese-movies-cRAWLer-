import subprocess
import os

def test_mock_mode_smoke_run():
    env = os.environ.copy()
    env["MOCK_MODE"] = "true"

    result = subprocess.run(
        ["python", "run_spider.py"],
        capture_output=True,
        text=True,
        env=env
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    assert result.returncode == 0, f"Mock mode run failed: {result.stderr}"
