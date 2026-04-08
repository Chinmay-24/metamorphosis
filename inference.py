"""
Inference script for the Customer Support Triage OpenEnv.

This script demonstrates baseline agent performance using the OpenAI API client.
It follows the strict structured logging format required for evaluation:
- [START] block with environment metadata
- [STEP] blocks for each action taken
- [END] block with final metrics and scores

Environment variables required:
- API_BASE_URL: The API endpoint for the LLM (e.g., https://api.openai.com/v1)
- MODEL_NAME: The model identifier (e.g., gpt-4o-mini)
- HF_TOKEN: Hugging Face API key (required for validation)
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI

from openenv_customer_support import Action, CustomerSupportTriageEnv

# Configuration from environment
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Validate required environment variables
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set. Validation features may not work.", file=sys.stderr)

# Initialize OpenAI client (lazy-loaded)
_client = None


def get_client():
    """Get or initialize the OpenAI client."""
    global _client
    if _client is None:
        try:
            _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=API_BASE_URL if API_BASE_URL else None)
        except Exception as e:
            print(f"ERROR: Failed to initialize OpenAI client: {e}", file=sys.stderr)
            sys.exit(1)
    return _client

# Structured logging constants
# NOTE: Using key=value format as per spec, not JSON
LOG_FORMAT_SPEC = """
[START] task=<task_name> env=customer-support-triage model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

PROMPT_TEMPLATE = """You are a customer support triage assistant. The goal is to classify the email, assign a priority, and provide the correct canned response or escalate if required.

Available labels: {labels}
Available priorities: {priorities}
Available response templates:
{responses}

Current email subject: {subject}
Current email body: {body}

Return ONLY a valid JSON object with these exact keys:
{{
  "label": "<one of the available labels>",
  "priority": "<one of the available priorities>",
  "response_template": "<exact response template or null>",
  "escalate": <true or false>
}}

Do not include any other text or markdown formatting.
"""


def parse_model_output(raw: str) -> Dict[str, Any]:
    """Parse JSON output from the model with error handling."""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract JSON from plain text
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse model output as JSON: {raw[:100]}")


def infer_action(obs) -> Action:
    """Use the OpenAI API to infer the next action."""
    client = get_client()
    
    prompt = PROMPT_TEMPLATE.format(
        labels=", ".join(obs.available_labels),
        priorities=", ".join(obs.available_priorities),
        responses="\n".join(f"- {r}" for r in obs.available_responses),
        subject=obs.email_subject,
        body=obs.email_body,
    )
    
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=250,
    )
    
    output = completion.choices[0].message.content
    parsed = parse_model_output(output)
    
    return Action(
        label=parsed.get("label", ""),
        priority=parsed.get("priority", ""),
        response_template=parsed.get("response_template"),
        escalate=bool(parsed.get("escalate", False)),
    )


def run_task(task_level: str) -> Dict[str, Any]:
    """Run a single task and collect metrics."""
    env = CustomerSupportTriageEnv(task_level=task_level)
    obs = env.reset(task_level)
    
    # Log START block (key=value format)
    print(f"[START] task={task_level} env=customer-support-triage model={MODEL_NAME}")
    
    total_reward = 0.0
    step_count = 0
    rewards = []
    
    while True:
        try:
            action = infer_action(obs)
        except Exception as e:
            error_msg = str(e)
            print(f"[STEP] step={step_count + 1} action=fallback reward=0.00 done=false error={error_msg}", flush=True)
            # Use a fallback action
            action = Action(label="technical", priority="medium", response_template=None, escalate=False)
        
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        step_count += 1
        rewards.append(reward.value)
        
        # Format action as string
        action_str = f"{action.label}|{action.priority}|{action.response_template or 'none'}|{action.escalate}"
        
        # Log STEP block (key=value format)
        done_str = str(done).lower()
        print(f"[STEP] step={step_count} action={action_str} reward={reward.value:.2f} done={done_str} error=null", flush=True)
        
        if done:
            break
    
    # Compute final score (normalized to [0, 1])
    num_emails = len(env.email_order)
    final_score = max(0.0, min(1.0, total_reward / num_emails)) if num_emails > 0 else 0.0
    success = final_score >= 0.5
    
    # Log END block (key=value format)
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={step_count} score={final_score:.2f} rewards={rewards_str}", flush=True)
    
    return {
        "task_level": task_level,
        "score": final_score,
        "total_reward": total_reward,
        "steps": step_count,
        "success": success,
    }


def main():
    """Run baseline inference on all three task levels."""
    
    print(f"Model: {MODEL_NAME}", file=sys.stderr)
    print(f"API Base: {API_BASE_URL}", file=sys.stderr)
    
    results = {}
    for level in ["easy", "medium", "hard"]:
        print(f"\n--- Running task: {level} ---", file=sys.stderr)
        try:
            results[level] = run_task(level)
            print(f"Task {level} score: {results[level]['score']:.3f}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Task {level} failed: {e}", file=sys.stderr)
            results[level] = {
                "task_level": level,
                "score": 0.0,
                "success": False,
                "error": str(e),
            }
    
    # Print summary to stderr
    print("\n" + "="*60, file=sys.stderr)
    print("BASELINE INFERENCE SUMMARY", file=sys.stderr)
    print("="*60, file=sys.stderr)
    for level in ["easy", "medium", "hard"]:
        score = results[level].get("score", 0.0)
        success = results[level].get("success", False)
        print(f"{level:8s}: score={score:.3f} success={success}", file=sys.stderr)
    
    avg_score = sum(r.get("score", 0.0) for r in results.values()) / len(results)
    print(f"{'AVERAGE':8s}: score={avg_score:.3f}", file=sys.stderr)


if __name__ == "__main__":
    main()
