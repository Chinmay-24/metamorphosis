import random
from typing import Tuple, Dict, Any, Optional
from .models import Action, Observation, Reward, State

class CustomerSupportTriageEnv:
    CATEGORIES = ["urgent", "standard", "followup"]
    
    EMAILS = {
        "easy": [
            {"id": "e1", "subject": "System Down!", "sender": "customer@example.com", "content": "Our system is completely down. Immediate help needed!"},
            {"id": "e2", "subject": "Billing Question", "sender": "user@example.com", "content": "Can you explain my invoice from last month?"},
        ],
        "medium": [
            {"id": "m1", "subject": "Feature Request", "sender": "dev@example.com", "content": "Would like to request a new feature for the dashboard."},
            {"id": "m2", "subject": "Integration Issue", "sender": "admin@example.com", "content": "Having trouble connecting to your API. Could use some guidance."},
        ],
        "hard": [
            {"id": "h1", "subject": "Subtle Bug Report", "sender": "test@example.com", "content": "Sometimes the dropdown doesn't refresh correctly in edge cases."},
            {"id": "h2", "subject": "Performance Feedback", "sender": "ops@example.com", "content": "Query times seem slow during peak hours. Not critical but noticeable."},
        ]
    }
    
    CORRECT_CATEGORIES = {
        "e1": "urgent", "e2": "standard",
        "m1": "followup", "m2": "standard",
        "h1": "standard", "h2": "standard"
    }
    
    def __init__(self):
        self.difficulty = "easy"
        self.current_email = None
        self.step_count = 0
        self.total_reward = 0.0
        self.max_steps = 5
        self.trajectory_rewards = []
        
    def reset(self, difficulty: str = "easy") -> State:
        self.difficulty = difficulty
        self.step_count = 0
        self.total_reward = 0.0
        self.trajectory_rewards = []
        self.current_email = random.choice(self.EMAILS[difficulty])
        return self.state()
    
    def step(self, action_str: str) -> Tuple[Observation, Reward, bool, Dict]:
        self.step_count += 1
        obs = self._get_observation()
        
        # Parse action (simple format: "category:priority")
        try:
            parts = action_str.split(":")
            category = parts[0].strip().lower()
            priority = int(parts[1].strip()) if len(parts) > 1 else 3
        except:
            category = "standard"
            priority = 3
        
        # Calculate reward
        correct_category = self.CORRECT_CATEGORIES.get(self.current_email["id"], "standard")
        is_correct = (category == correct_category)
        
        step_reward = 0.4 if is_correct else 0.1
        trajectory_reward = step_reward * (1.0 - (self.step_count / self.max_steps) * 0.2)
        
        self.trajectory_rewards.append(trajectory_reward)
        self.total_reward += trajectory_reward
        
        done = self.step_count >= self.max_steps
        
        reward = Reward(
            reward=step_reward,
            trajectory_reward=trajectory_reward,
            bonus=0.3 if is_correct else 0.0
        )
        
        return obs, reward, done, {"correct": is_correct}
    
    def _get_observation(self) -> Observation:
        return Observation(
            email_id=self.current_email["id"],
            subject=self.current_email["subject"],
            sender=self.current_email["sender"],
            content=self.current_email["content"],
            step=self.step_count
        )
    
    def state(self) -> State:
        return State(
            task="email_triage",
            difficulty=self.difficulty,
            email_id=self.current_email["id"] if self.current_email else "",
            subject=self.current_email["subject"] if self.current_email else "",
            sender=self.current_email["sender"] if self.current_email else "",
            content=self.current_email["content"] if self.current_email else "",
            current_step=self.step_count,
            max_steps=self.max_steps,
            total_reward=self.total_reward,
            done=self.step_count >= self.max_steps
        )
