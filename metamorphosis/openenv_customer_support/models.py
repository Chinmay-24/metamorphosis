from pydantic import BaseModel, Field
from typing import Optional

class Action(BaseModel):
    category: str = Field(..., description="Category: urgent, standard, or followup")
    priority: int = Field(..., ge=1, le=5, description="Priority level 1-5")
    response: Optional[str] = Field(None, description="Optional response template")

class Observation(BaseModel):
    email_id: str
    subject: str
    sender: str
    content: str
    current_category: Optional[str] = None
    step: int

class Reward(BaseModel):
    reward: float = Field(default=0.0, description="Step reward")
    trajectory_reward: float = Field(default=0.0, description="Accumulated trajectory reward")
    bonus: float = Field(default=0.0, description="Bonus reward for correctness")

class State(BaseModel):
    task: str
    difficulty: str
    email_id: str
    subject: str
    sender: str
    content: str
    current_step: int
    max_steps: int
    total_reward: float
    done: bool
