from typing import List, Optional
from pydantic import BaseModel, Field


class Observation(BaseModel):
    email_subject: str = Field(..., description="Subject line of the current support email")
    email_body: str = Field(..., description="Body text of the current support email")
    available_labels: List[str] = Field(..., description="Valid issue categories for classification")
    available_priorities: List[str] = Field(..., description="Valid priority levels")
    available_responses: List[str] = Field(..., description="Valid canned response templates")
    remaining_emails: int = Field(..., description="Number of emails left in the triage queue")
    task_level: str = Field(..., description="Task difficulty level: easy, medium, or hard")
    step_index: int = Field(..., description="Zero-based index of the current email within the task")


class Action(BaseModel):
    label: str = Field(..., description="Issue category assigned to this email")
    priority: str = Field(..., description="Priority level assigned to this email")
    response_template: Optional[str] = Field(
        None,
        description="Selected canned response template. Use None when escalating or when not required.",
    )
    escalate: bool = Field(False, description="Whether the email should be escalated to a specialist")


class Reward(BaseModel):
    value: float = Field(..., description="Reward value for the last action step")
    normalized_value: float = Field(..., description="Normalized score between 0.0 and 1.0 for the action step")
    message: str = Field(..., description="Human-readable explanation of the reward and progress signal")


class State(BaseModel):
    task_level: str = Field(..., description="The current task difficulty level")
    step_index: int = Field(..., description="Zero-based index of the current email")
    remaining_emails: int = Field(..., description="Number of emails left in the queue")
    cumulative_reward: float = Field(..., description="Cumulative reward accumulated so far")
    done: bool = Field(..., description="Whether the current episode has finished")
