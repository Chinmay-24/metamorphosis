#!/usr/bin/env python3
"""
Baseline inference script for Metamorphosis OpenEnv
Uses OpenAI to complete customer support triage tasks
"""

import os
import sys
import json
from openenv_customer_support import CustomerSupportTriageEnv

# Environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Try to import OpenAI
try:
    from openai import OpenAI, APIError, APIConnectionError
    client = OpenAI(api_key=API_BASE_URL.split("https://")[1].split("/")[0] if API_BASE_URL != "https://api.openai.com/v1" else None)
except ImportError:
    print("[ERROR] OpenAI library not installed", file=sys.stderr)
    sys.exit(1)

def run_task(difficulty: str = "easy"):
    """Run a single task and log results"""
    env = CustomerSupportTriageEnv()
    state = env.reset(difficulty)
    
    # [START] log
    print(f"[START] task={difficulty} env=customer-support-triage model={MODEL_NAME}")
    
    rewards = []
    step_count = 0
    success = False
    error_msg = None
    
    try:
        for step_num in range(1, 6):
            step_count = step_num
            
            # Get email content for LLM
            email_text = f"Subject: {state.subject}\nFrom: {state.sender}\n\n{state.content}"
            
            # Call LLM for action
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a customer support triage expert. Respond with ONLY 'urgent:5', 'standard:3', or 'followup:2'"},
                        {"role": "user", "content": f"Triage this email:\n\n{email_text}"}
                    ],
                    temperature=0.1,
                    max_tokens=20
                )
                action = response.choices[0].message.content.strip()
            except (APIError, APIConnectionError) as e:
                action = "standard:3"
            
            # Step environment
            obs, reward, done, info = env.step(action)
            rewards.append(reward.trajectory_reward)
            
            # [STEP] log
            print(f"[STEP] step={step_num} action={action} reward={reward.trajectory_reward:.2f} done={str(done).lower()} error=null")
            
            if done:
                break
        
        success = True
    except Exception as e:
        error_msg = str(e)
        print(f"[STEP] step={step_count} action=error reward=0.0 done=true error={error_msg}", file=sys.stderr)
    
    # Calculate final score
    total_reward = sum(rewards) if rewards else 0.0
    score = min(1.0, max(0.0, total_reward))
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    
    # [END] log
    print(f"[END] success={str(success).lower()} steps={step_count} score={score:.2f} rewards=[{rewards_str}]")
    
    return success, score

if __name__ == "__main__":
    try:
        # Run all three difficulties
        all_success = True
        all_scores = []
        
        for difficulty in ["easy", "medium", "hard"]:
            success, score = run_task(difficulty)
            all_success = all_success and success
            all_scores.append(score)
        
        # Exit with success if all tasks ran
        sys.exit(0 if all_success else 1)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)
