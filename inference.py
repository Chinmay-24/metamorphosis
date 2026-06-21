"""Root-level inference script with strict structured stdout blocks."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from openai import OpenAI

from openenv_customer_support import Action, CustomerSupportTriageEnv

API_BASE_URL = os.environ.get("API_BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME")
HF_TOKEN = os.environ.get("HF_TOKEN")

START_BLOCK_TEMPLATE = {
    "timestamp": "",
    "session_id": "",
    "task_level": "",
    "description": "",
    "model": "",
    "api_base": "",
}

STEP_BLOCK_TEMPLATE = {
    "step_index": 0,
    "email_id": "",
    "email_subject": "",
    "action": {"label": "", "priority": "", "response_template": None, "escalate": False},
    "reward": 0.0,
    "normalized_reward": 0.0,
    "done": False,
    "grader_feedback": "",
}

END_BLOCK_TEMPLATE = {
    "total_steps": 0,
    "total_reward": 0.0,
    "final_score": 0.0,
    "task_level": "",
    "success": False,
}

PROMPT_TEMPLATE = """You are a customer support triage assistant.
Return only JSON with keys: label, priority, response_template, escalate.

Labels: {labels}
Priorities: {priorities}
Response templates:
{responses}

Email subject: {subject}
Email body: {body}
"""

_client: Optional[OpenAI] = None


def _require_env() -> None:
    missing = [k for k, v in {"API_BASE_URL": API_BASE_URL, "MODEL_NAME": MODEL_NAME, "HF_TOKEN": HF_TOKEN}.items() if not v]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _require_env()
        _client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
    return _client


def parse_model_output(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start : end + 1])
        raise


def infer_action(obs) -> Action:
    completion = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(
                    labels=", ".join(obs.available_labels),
                    priorities=", ".join(obs.available_priorities),
                    responses="\n".join(f"- {r}" for r in obs.available_responses),
                    subject=obs.email_subject,
                    body=obs.email_body,
                ),
            }
        ],
        temperature=0,
        max_tokens=220,
    )
    parsed = parse_model_output(completion.choices[0].message.content or "{}")
    return Action(
        label=str(parsed.get("label", "")),
        priority=str(parsed.get("priority", "")),
        response_template=parsed.get("response_template"),
        escalate=bool(parsed.get("escalate", False)),
    )


def _emit(tag: str, payload: Dict[str, Any]) -> None:
    print(f"{tag} {json.dumps(payload, separators=(',', ':'), ensure_ascii=True)}", flush=True)


def run_task(task_level: str) -> Dict[str, Any]:
    env = CustomerSupportTriageEnv(task_level=task_level)
    obs = env.reset(task_level)
    session_id = str(uuid.uuid4())

    start_payload = dict(START_BLOCK_TEMPLATE)
    start_payload.update(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "task_level": task_level,
            "description": env.TASKS[task_level]["description"],
            "model": MODEL_NAME,
            "api_base": API_BASE_URL,
        }
    )
    _emit("[START]", start_payload)

    total_reward = 0.0
    steps = 0
    done = False

    while not done:
        try:
            action = infer_action(obs)
        except Exception:
            # Keep run deterministic and bounded even if LLM call fails.
            action = Action(label="technical", priority="medium", response_template=None, escalate=False)
        obs_before = obs
        obs, reward, done, info = env.step(action)
        steps += 1
        total_reward += reward.normalized_value

        step_payload = dict(STEP_BLOCK_TEMPLATE)
        step_payload.update(
            {
                "step_index": steps,
                "email_id": str(info.get("email_index", steps - 1)),
                "email_subject": obs_before.email_subject,
                "action": action.model_dump(),
                "reward": float(reward.value),
                "normalized_reward": float(reward.normalized_value),
                "done": bool(done),
                "grader_feedback": reward.message,
            }
        )
        _emit("[STEP]", step_payload)

    final_score = max(0.0, min(1.0, total_reward / max(1, steps)))
    end_payload = dict(END_BLOCK_TEMPLATE)
    end_payload.update(
        {
            "total_steps": steps,
            "total_reward": round(total_reward, 6),
            "final_score": round(final_score, 6),
            "task_level": task_level,
            "success": final_score >= 0.5,
        }
    )
    _emit("[END]", end_payload)
    return end_payload


def main() -> int:
    _require_env()
    for level in ("easy", "medium", "hard"):
        run_task(level)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
