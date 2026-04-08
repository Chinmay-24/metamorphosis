import random
from typing import Dict, List, Optional, Tuple

from .models import Action, Observation, Reward, State


class CustomerSupportTriageEnv:
    CATEGORIES = ["billing", "technical", "account", "feedback", "cancellation"]
    PRIORITIES = ["low", "medium", "high"]

    RESPONSE_TEMPLATES = [
        "Request more information and reassure the customer.",
        "Provide a step-by-step technical workaround.",
        "Confirm the billing charge and offer a refund if eligible.",
        "Explain account security and help with sign-in recovery.",
        "Pass the request to the cancellation team and confirm next steps.",
        "Thank the customer for feedback and promise a follow-up.",
    ]

    EMAILS = [
        {
            "subject": "Incorrect charge on my account",
            "body": "I was billed twice this month and I need this fixed immediately.",
            "label": "billing",
            "priority": "high",
            "correct_response": "Confirm the billing charge and offer a refund if eligible.",
            "should_escalate": False,
        },
        {
            "subject": "App crashes during login",
            "body": "Every time I try to log in, the app closes. I cannot access my account.",
            "label": "technical",
            "priority": "high",
            "correct_response": "Provide a step-by-step technical workaround.",
            "should_escalate": False,
        },
        {
            "subject": "Need to change my subscription plan",
            "body": "I want to upgrade from basic to premium and want to know how much it costs.",
            "label": "account",
            "priority": "medium",
            "correct_response": "Explain account security and help with sign-in recovery.",
            "should_escalate": False,
        },
        {
            "subject": "Feedback about recent update",
            "body": "The latest update is slower and the design is confusing. Please share with the product team.",
            "label": "feedback",
            "priority": "low",
            "correct_response": "Thank the customer for feedback and promise a follow-up.",
            "should_escalate": False,
        },
        {
            "subject": "Cancel my membership",
            "body": "I want to cancel my membership immediately and make sure I am not charged again.",
            "label": "cancellation",
            "priority": "high",
            "correct_response": "Pass the request to the cancellation team and confirm next steps.",
            "should_escalate": True,
        },
        {
            "subject": "Unable to reset password",
            "body": "I tried to reset my password, but the reset link expired before I could use it.",
            "label": "technical",
            "priority": "medium",
            "correct_response": "Explain account security and help with sign-in recovery.",
            "should_escalate": False,
        },
        {
            "subject": "Question about invoice details",
            "body": "Can you explain why my invoice includes two setup fees?",            
            "label": "billing",
            "priority": "medium",
            "correct_response": "Confirm the billing charge and offer a refund if eligible.",
            "should_escalate": False,
        },
        {
            "subject": "Account locked after suspicious activity",
            "body": "My account was locked after a suspicious login attempt. I need help getting back in.",
            "label": "account",
            "priority": "high",
            "correct_response": "Explain account security and help with sign-in recovery.",
            "should_escalate": False,
        },
        {
            "subject": "Feature request for dark mode",
            "body": "I would love it if your product had a dark mode option.",
            "label": "feedback",
            "priority": "low",
            "correct_response": "Thank the customer for feedback and promise a follow-up.",
            "should_escalate": False,
        },
        {
            "subject": "I need help updating my payment card",
            "body": "My current card expired and I cannot update the payment method in the app.",
            "label": "billing",
            "priority": "medium",
            "correct_response": "Confirm the billing charge and offer a refund if eligible.",
            "should_escalate": False,
        },
    ]

    TASKS = {
        "easy": {
            "description": "Classify incoming support emails into categories.",
            "email_indices": [0, 1, 2, 3, 4],
            "grade_fields": ["label"],
        },
        "medium": {
            "description": "Classify categories and assign priority levels.",
            "email_indices": [0, 1, 2, 4, 5, 6, 7],
            "grade_fields": ["label", "priority"],
        },
        "hard": {
            "description": "Classify emails, prioritize them, and provide the correct response or escalate when needed.",
            "email_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "grade_fields": ["label", "priority", "response"],
        },
    }

    def __init__(self, task_level: str = "easy", seed: int = 42):
        self.seed = seed
        self.task_level = task_level
        self._reset_state()

    def _reset_state(self):
        self.step_index = 0
        self.cumulative_reward = 0.0
        self.current_task = self.TASKS[self.task_level]
        self.email_order = list(self.current_task["email_indices"])
        random.Random(self.seed).shuffle(self.email_order)
        self.history: List[Dict] = []
        self.done = False

    def reset(self, task_level: Optional[str] = None) -> Observation:
        if task_level is not None:
            if task_level not in self.TASKS:
                raise ValueError(f"Unknown task level {task_level}")
            self.task_level = task_level
        self._reset_state()
        return self._current_observation()

    def state(self) -> State:
        return State(
            task_level=self.task_level,
            step_index=self.step_index,
            remaining_emails=len(self.email_order) - self.step_index,
            cumulative_reward=self.cumulative_reward,
            done=self.done,
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        if self.done:
            raise RuntimeError("Cannot call step() after the episode is done. Call reset() first.")

        current_email = self._current_email()
        step_result = self._score_action(current_email, action)
        self.cumulative_reward += step_result["value"]
        self.history.append({"email_index": self.email_order[self.step_index], **step_result})

        self.step_index += 1
        self.done = self.step_index >= len(self.email_order)

        observation = self._current_observation() if not self.done else self._final_observation()
        reward = Reward(
            value=step_result["value"],
            normalized_value=self._normalize_reward(step_result["value"]),
            message=step_result["message"],
        )
        info = {
            "label_correct": step_result["label_correct"],
            "priority_correct": step_result["priority_correct"],
            "response_correct": step_result["response_correct"],
            "should_escalate": current_email["should_escalate"],
            "email_index": self.email_order[self.step_index - 1],
        }
        return observation, reward, self.done, info

    def _current_email(self) -> Dict:
        index = self.email_order[self.step_index]
        return self.EMAILS[index]

    def _current_observation(self) -> Observation:
        email = self._current_email()
        return Observation(
            email_subject=email["subject"],
            email_body=email["body"],
            available_labels=self.CATEGORIES,
            available_priorities=self.PRIORITIES,
            available_responses=self.RESPONSE_TEMPLATES,
            remaining_emails=len(self.email_order) - self.step_index,
            task_level=self.task_level,
            step_index=self.step_index,
        )

    def _final_observation(self) -> Observation:
        return Observation(
            email_subject="",
            email_body="",
            available_labels=self.CATEGORIES,
            available_priorities=self.PRIORITIES,
            available_responses=self.RESPONSE_TEMPLATES,
            remaining_emails=0,
            task_level=self.task_level,
            step_index=self.step_index,
        )

    def _score_action(self, email: Dict, action: Action) -> Dict:
        label_correct = action.label.strip().lower() == email["label"]
        priority_correct = action.priority.strip().lower() == email["priority"]
        response_correct = False
        invalid_action = False
        message = []

        if action.label.strip().lower() not in self.CATEGORIES:
            invalid_action = True
            message.append("Invalid label selected.")
        if action.priority.strip().lower() not in self.PRIORITIES:
            invalid_action = True
            message.append("Invalid priority selected.")

        if self.task_level == "hard":
            if email["should_escalate"]:
                response_correct = action.escalate is True
                if response_correct:
                    message.append("Correctly escalated a sensitive request.")
                else:
                    message.append("Sensitive request should have been escalated.")
            else:
                response_correct = (
                    action.response_template is not None
                    and action.response_template.strip() == email["correct_response"]
                    and action.escalate is False
                )
                if response_correct:
                    message.append("Correct response selected.")
                else:
                    message.append("Response did not match the expected canned answer.")
        else:
            response_correct = True

        reward_value = 0.0
        if invalid_action:
            reward_value -= 0.2
        reward_value += 0.4 if label_correct else 0.0
        if self.task_level in ["medium", "hard"]:
            reward_value += 0.2 if priority_correct else -0.05
        if self.task_level == "hard":
            reward_value += 0.4 if response_correct else -0.1

        if reward_value < -0.2:
            reward_value = -0.2
        if reward_value > 1.0:
            reward_value = 1.0

        if not message:
            message.append("Action scored with partial progress toward the task objective.")

        return {
            "value": reward_value,
            "label_correct": label_correct,
            "priority_correct": priority_correct,
            "response_correct": response_correct,
            "message": " ".join(message),
        }

    def _normalize_reward(self, value: float) -> float:
        return max(0.0, min(1.0, (value + 0.2) / 1.2))
