"""
Validation script to test environment compliance with OpenEnv spec.
Runs task graders, validates score ranges, and tests API endpoints.
"""

import json
from openenv_customer_support import Action, CustomerSupportTriageEnv


def validate_task_graders():
    """Validate that all tasks have functioning graders with correct score ranges."""
    print("="*70)
    print("VALIDATING TASK GRADERS")
    print("="*70)
    
    results = {}
    
    for task_level in ["easy", "medium", "hard"]:
        print(f"\n--- Task: {task_level} ---")
        env = CustomerSupportTriageEnv(task_level=task_level)
        obs = env.reset(task_level)
        
        task_info = CustomerSupportTriageEnv.TASKS[task_level]
        print(f"Description: {task_info['description']}")
        print(f"Email indices: {task_info['email_indices']}")
        print(f"Grading fields: {task_info['grade_fields']}")
        
        scores = []
        step = 0
        
        while True:
            step += 1
            # Test with random valid action
            action = Action(
                label=env.CATEGORIES[0],
                priority=env.PRIORITIES[1],
                response_template=env.RESPONSE_TEMPLATES[0],
                escalate=False,
            )
            
            obs, reward, done, info = env.step(action)
            
            # Validate reward ranges
            assert 0.0 <= reward.value <= 1.0 or -0.2 <= reward.value <= 1.0, \
                f"Step {step}: reward.value {reward.value} out of expected range"
            assert 0.0 <= reward.normalized_value <= 1.0, \
                f"Step {step}: normalized_value {reward.normalized_value} not in [0.0, 1.0]"
            
            scores.append(reward.value)
            print(f"  Step {step}: reward={reward.value:.3f}, normalized={reward.normalized_value:.3f}")
            
            if done:
                break
        
        avg_score = sum(scores) / len(scores)
        results[task_level] = {
            "steps": step,
            "min_reward": min(scores),
            "max_reward": max(scores),
            "avg_reward": avg_score,
            "valid": True,
        }
        
        print(f"  Total steps: {step}")
        print(f"  Min reward: {min(scores):.3f}")
        print(f"  Max reward: {max(scores):.3f}")
        print(f"  Avg reward: {avg_score:.3f}")
    
    print("\n" + "="*70)
    print("GRADER VALIDATION SUMMARY")
    print("="*70)
    for level, result in results.items():
        print(f"{level:10s}: steps={result['steps']:2d} min={result['min_reward']:.3f} max={result['max_reward']:.3f} avg={result['avg_reward']:.3f}")
    
    return results


def validate_api_endpoints():
    """Validate step(), reset(), and state() endpoints."""
    print("\n" + "="*70)
    print("VALIDATING API ENDPOINTS")
    print("="*70)
    
    env = CustomerSupportTriageEnv("easy")
    
    # Test reset()
    print("\n--- Testing reset() ---")
    obs = env.reset("easy")
    assert obs is not None, "reset() returned None"
    assert hasattr(obs, "email_subject"), "Observation missing email_subject"
    assert hasattr(obs, "email_body"), "Observation missing email_body"
    print("[OK] reset() returns valid Observation")
    
    # Test state()
    print("\n--- Testing state() ---")
    state = env.state()
    assert state is not None, "state() returned None"
    assert hasattr(state, "task_level"), "State missing task_level"
    assert hasattr(state, "step_index"), "State missing step_index"
    assert hasattr(state, "remaining_emails"), "State missing remaining_emails"
    assert hasattr(state, "cumulative_reward"), "State missing cumulative_reward"
    assert hasattr(state, "done"), "State missing done"
    print("[OK] state() returns valid State object")
    print(f"  task_level={state.task_level}, step_index={state.step_index}, remaining={state.remaining_emails}")
    
    # Test step()
    print("\n--- Testing step() ---")
    action = Action(label="billing", priority="high", response_template=None, escalate=False)
    obs, reward, done, info = env.step(action)
    assert obs is not None, "step() obs is None"
    assert reward is not None, "step() reward is None"
    assert isinstance(done, bool), "step() done is not bool"
    assert isinstance(info, dict), "step() info is not dict"
    assert hasattr(reward, "value"), "Reward missing value"
    assert hasattr(reward, "normalized_value"), "Reward missing normalized_value"
    assert hasattr(reward, "message"), "Reward missing message"
    print("[OK] step() returns valid (obs, reward, done, info)")
    print(f"  reward.value={reward.value:.3f}, normalized={reward.normalized_value:.3f}")
    
    return True


def validate_typed_models():
    """Validate that models are properly typed Pydantic objects."""
    print("\n" + "="*70)
    print("VALIDATING TYPED MODELS")
    print("="*70)
    
    # Validate Action
    print("\n--- Action Model ---")
    action = Action(label="billing", priority="high", response_template="test", escalate=False)
    action_dict = action.model_dump()
    print(f"[OK] Action model is valid Pydantic")
    print(f"  Fields: {list(action_dict.keys())}")
    
    # Validate Observation
    print("\n--- Observation Model ---")
    env = CustomerSupportTriageEnv("easy")
    obs = env.reset("easy")
    obs_dict = obs.model_dump()
    print(f"[OK] Observation model is valid Pydantic")
    print(f"  Fields: {list(obs_dict.keys())}")
    
    # Validate Reward
    print("\n--- Reward Model ---")
    action = Action(label="billing", priority="high", response_template=None, escalate=False)
    obs, reward, done, info = env.step(action)
    reward_dict = reward.model_dump()
    print(f"[OK] Reward model is valid Pydantic")
    print(f"  Fields: {list(reward_dict.keys())}")
    
    # Validate State
    print("\n--- State Model ---")
    state = env.state()
    state_dict = state.model_dump()
    print(f"[OK] State model is valid Pydantic")
    print(f"  Fields: {list(state_dict.keys())}")
    
    return True


def main():
    """Run all validation checks."""
    try:
        validate_typed_models()
        validate_api_endpoints()
        validate_task_graders()
        
        print("\n" + "="*70)
        print("[OK] ALL VALIDATION CHECKS PASSED")
        print("="*70)
        return 0
    except Exception as e:
        print(f"\n[ERROR] VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
