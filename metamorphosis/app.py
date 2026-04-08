#!/usr/bin/env python3
"""
Gradio interface for Metamorphosis OpenEnv Space
"""

import gradio as gr
from openenv_customer_support import CustomerSupportTriageEnv
import json

# Initialize environment
env = CustomerSupportTriageEnv()
state = None

def reset_env():
    global state
    state = env.reset()
    return json.dumps(state, indent=2)

def step_env(action_text: str):
    global state
    if state is None:
        return "Error: Environment not initialized. Click 'Reset' first."
    
    try:
        obs, reward_data, done, info = env.step(action_text)
        state = env.state()
        
        result = {
            "observation": obs,
            "reward": reward_data.reward,
            "trajectory_reward": reward_data.trajectory_reward,
            "done": done,
            "info": info
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# Build Gradio interface
with gr.Blocks(title="Metamorphosis: Customer Support Triage") as demo:
    gr.Markdown("""
    # 🦋 Metamorphosis: Customer Support Triage
    
    An OpenEnv environment for training baseline agents on customer support email triage tasks.
    
    **Features:**
    - 3 Difficulty Levels (Easy, Medium, Hard)
    - Deterministic Graders
    - Trajectory-based Rewards
    """)
    
    with gr.Row():
        reset_btn = gr.Button("Reset Environment", scale=1, variant="primary")
        difficulty_dropdown = gr.Dropdown(
            choices=["easy", "medium", "hard"],
            value="easy",
            label="Difficulty Level",
            scale=1
        )
    
    state_output = gr.Textbox(
        label="Environment State",
        interactive=False,
        lines=10
    )
    
    with gr.Row():
        action_input = gr.Textbox(
            label="Action",
            placeholder="Enter your action...",
            scale=4
        )
        step_btn = gr.Button("Step", scale=1, variant="primary")
    
    result_output = gr.Textbox(
        label="Result",
        interactive=False,
        lines=10
    )
    
    # Event handlers
    reset_btn.click(reset_env, outputs=state_output)
    step_btn.click(step_env, inputs=action_input, outputs=result_output)

if __name__ == "__main__":
    demo.launch(share=False)
