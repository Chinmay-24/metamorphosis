import json
import os
from typing import List

import openai
from openenv_customer_support import Action, CustomerSupportTriageEnv


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_API_KEY is None:
    raise EnvironmentError("OPENAI_API_KEY must be set to run the baseline script.")

openai.api_key = OPENAI_API_KEY

PROMPT_TEMPLATE = """
You are a customer support triage assistant. The goal is to classify the email, assign a priority, and provide the correct canned response or escalate if required.

Available labels: {labels}
Available priorities: {priorities}
Available response templates:
{responses}

Current email subject: {subject}
Current email body: {body}

Return only a JSON object with keys:
- label
- priority
- response_template
- escalate

The response_template should be one of the available options or null.
The escalate field should be true only if escalation is required.
"""


def parse_model_output(raw: str):
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract JSON from plain text
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start : end + 1])
        raise


def infer_action(obs):
    prompt = PROMPT_TEMPLATE.format(
        labels=", ".join(obs.available_labels),
        priorities=", ".join(obs.available_priorities),
        responses="\n".join(f"- {r}" for r in obs.available_responses),
        subject=obs.email_subject,
        body=obs.email_body,
    )
    completion = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=250,
    )
    output = completion["choices"][0]["message"]["content"]
    parsed = parse_model_output(output)
    return Action(
        label=parsed.get("label", ""),
        priority=parsed.get("priority", ""),
        response_template=parsed.get("response_template"),
        escalate=bool(parsed.get("escalate", False)),
    )


def run_task(task_level: str):
    env = CustomerSupportTriageEnv(task_level=task_level)
    obs = env.reset(task_level)
    total_reward = 0.0
    step = 0

    while True:
        action = infer_action(obs)
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        step += 1
        print(f"[{task_level}] step={step} label={action.label} priority={action.priority} escalate={action.escalate} reward={reward.value:.3f}")
        if done:
            break

    normalized_score = max(0.0, min(1.0, total_reward / len(env.email_order)))
    return normalized_score


def main():
    scores = {}
    for level in ["easy", "medium", "hard"]:
        print(f"Running baseline for task: {level}")
        scores[level] = run_task(level)
        print(f"Baseline {level}: {scores[level]:.3f}\n")
    print("Summary:")
    for level, score in scores.items():
        print(f"{level}: {score:.3f}")


if __name__ == "__main__":
    main()
