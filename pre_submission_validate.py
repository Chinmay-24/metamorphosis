"""End-to-end pre-submission validator for OpenEnv projects."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib import error, parse, request

import yaml

from openenv_customer_support import Action, CustomerSupportTriageEnv


ROOT = Path(__file__).parent
REQUIRED_ENV = ("API_BASE_URL", "MODEL_NAME", "HF_TOKEN")


def _run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def check_env_vars():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    print("[OK] Required environment variables are set.")


def check_openenv_yaml():
    cfg = yaml.safe_load((ROOT / "openenv.yaml").read_text(encoding="utf-8"))
    required_top = ("name", "version", "author", "license", "environment", "interface", "tasks")
    for key in required_top:
        if key not in cfg:
            raise RuntimeError(f"openenv.yaml missing key: {key}")
    if len(cfg["tasks"]) < 3:
        raise RuntimeError("openenv.yaml must define at least 3 tasks")
    print("[OK] openenv.yaml structure validated.")


def check_env_endpoints_and_scores():
    env = CustomerSupportTriageEnv("easy")
    obs = env.reset("easy")
    if obs is None:
        raise RuntimeError("reset() returned None")
    _ = env.state()
    obs2, reward, done, info = env.step(
        Action(label="billing", priority="high", response_template=None, escalate=False)
    )
    if obs2 is None or reward is None or not isinstance(done, bool) or not isinstance(info, dict):
        raise RuntimeError("step() return types invalid")

    for level in ("easy", "medium", "hard"):
        env = CustomerSupportTriageEnv(level)
        env.reset(level)
        done = False
        while not done:
            obs, reward, done, _ = env.step(
                Action(
                    label=env.CATEGORIES[0],
                    priority=env.PRIORITIES[1],
                    response_template=env.RESPONSE_TEMPLATES[0],
                    escalate=False,
                )
            )
            if not (0.0 <= reward.normalized_value <= 1.0):
                raise RuntimeError(f"normalized reward out of range for task {level}: {reward.normalized_value}")
    print("[OK] reset()/step()/state() and grader score ranges validated.")


def check_inference_script():
    path = ROOT / "inference.py"
    if not path.exists():
        raise RuntimeError("inference.py not found in repository root")
    code, out, err = _run([sys.executable, "inference.py"])
    if code != 0:
        raise RuntimeError(f"inference.py failed\nSTDERR:\n{err}\nSTDOUT:\n{out}")
    print("[OK] inference.py completed without error.")


def check_docker_build():
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI is not installed or not on PATH.")
    code, out, err = _run(["docker", "build", "-t", "customer-support-triage:presubmit", "."])
    if code != 0:
        raise RuntimeError(f"Docker build failed\nSTDERR:\n{err}\nSTDOUT:\n{out}")
    print("[OK] Docker build succeeded.")


def check_hf_space():
    space_url = os.environ.get("SPACE_URL")
    if not space_url:
        print("[WARN] SPACE_URL not set; skipping HF Space ping/reset checks.")
        return

    health_req = request.Request(space_url, method="GET")
    try:
        with request.urlopen(health_req, timeout=20) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Space root endpoint returned {resp.status}")
    except error.URLError as exc:
        raise RuntimeError(f"Space root check failed: {exc}") from exc

    reset_url = space_url.rstrip("/") + "/reset?" + parse.urlencode({"task_level": "easy"})
    reset_req = request.Request(reset_url, method="POST")
    try:
        with request.urlopen(reset_req, timeout=20) as resp:
            if resp.status != 200:
                raise RuntimeError(f"/reset returned {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))
            if "session_id" not in payload:
                raise RuntimeError("/reset response missing session_id")
    except error.URLError as exc:
        raise RuntimeError(f"Space reset check failed: {exc}") from exc
    print("[OK] HF Space root and /reset checks succeeded.")


def main():
    print("=" * 72)
    print("PRE-SUBMISSION VALIDATION")
    print("=" * 72)
    check_env_vars()
    check_openenv_yaml()
    check_env_endpoints_and_scores()
    check_hf_space()
    check_docker_build()
    check_inference_script()
    print("=" * 72)
    print("[OK] ALL PRE-SUBMISSION CHECKS PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1)
