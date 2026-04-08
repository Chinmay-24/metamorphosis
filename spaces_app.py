"""
Hugging Face Space application with REST API + Gradio UI.
Deployed at the root of the repository.

Serves both:
- REST API endpoints for validation (POST /reset, etc.)
- Gradio UI for interactive triage at /
"""

import json
from typing import Dict, Any

import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from openenv_customer_support import Action, CustomerSupportTriageEnv


# Initialize FastAPI app for REST API
api = FastAPI(title="Customer Support Triage OpenEnv")

# Store active sessions (simple in-memory state)
_sessions: Dict[str, Any] = {}


@api.post("/reset")
async def reset_endpoint(task_level: str = "easy") -> JSONResponse:
    """Reset a triage session and return initial observation."""
    try:
        if task_level not in ["easy", "medium", "hard"]:
            raise HTTPException(status_code=400, detail=f"Invalid task_level: {task_level}")
        
        env = CustomerSupportTriageEnv(task_level=task_level)
        obs = env.reset(task_level)
        
        # Store session
        session_id = f"session_{len(_sessions)}"
        _sessions[session_id] = {"env": env, "obs": obs}
        
        return JSONResponse({
            "status": "ok",
            "session_id": session_id,
            "task_level": task_level,
            "email_subject": obs.email_subject,
            "email_body": obs.email_body,
            "remaining_emails": obs.remaining_emails,
            "available_labels": obs.available_labels,
            "available_priorities": obs.available_priorities,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/step")
async def step_endpoint(session_id: str, action: Dict[str, Any]) -> JSONResponse:
    """Execute one step in the environment."""
    try:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        
        session = _sessions[session_id]
        env = session["env"]
        
        # Parse action
        agent_action = Action(
            label=action.get("label", ""),
            priority=action.get("priority", ""),
            response_template=action.get("response_template"),
            escalate=bool(action.get("escalate", False)),
        )
        
        obs, reward, done, info = env.step(agent_action)
        
        # Update session
        _sessions[session_id]["obs"] = obs
        
        return JSONResponse({
            "status": "ok",
            "email_subject": obs.email_subject if not done else "",
            "email_body": obs.email_body if not done else "",
            "remaining_emails": obs.remaining_emails,
            "reward": reward.value,
            "normalized_reward": reward.normalized_value,
            "done": done,
            "message": reward.message,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "customer-support-triage"})


@api.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service info."""
    return {
        "service": "Customer Support Triage OpenEnv",
        "status": "running",
        "endpoints": {
            "POST /reset": "Reset a triage session",
            "POST /step": "Execute one step",
            "GET /health": "Health check",
            "GET /": "This endpoint",
        },
    }


# Gradio UI
def create_interface():
    """Create and return the Gradio interface for the environment."""
    
    def start_session(task_level: str):
        """Initialize a new triage session."""
        try:
            env = CustomerSupportTriageEnv(task_level=task_level)
            obs = env.reset(task_level)
            return (
                env,
                obs.email_subject,
                obs.email_body,
                "Ready to triage the first email.",
                obs.remaining_emails,
                "Session initialized.",
            )
        except Exception as e:
            return None, "", "", f"Error: {str(e)}", 0, "Failed to initialize."
    
    def step_session(env, label, priority, response_template, escalate):
        """Process an action and move to the next email."""
        if env is None:
            return None, "", "", "Error: Session not initialized.", 0, "Failed."
        
        try:
            action = Action(
                label=label,
                priority=priority,
                response_template=response_template or None,
                escalate=escalate,
            )
            obs, reward, done, info = env.step(action)
            
            status = "Finished all emails." if done else "Continue to the next email."
            return (
                env,
                obs.email_subject if not done else "",
                obs.email_body if not done else "",
                reward.message,
                obs.remaining_emails,
                status,
            )
        except Exception as e:
            return env, "", "", f"Error: {str(e)}", 0, "Failed."
    
    with gr.Blocks(title="Customer Support Triage OpenEnv") as demo:
        gr.Markdown("# Customer Support Triage OpenEnv")
        gr.Markdown(
            "Classify support emails, assign priorities, and provide responses or escalations. "
            "This environment simulates real-world customer support workflows."
        )
        
        with gr.Row():
            task_dropdown = gr.Radio(
                ["easy", "medium", "hard"],
                label="Task Difficulty",
                value="easy",
            )
            reset_button = gr.Button("🔄 Reset Task", variant="primary")
        
        gr.Markdown("### Current Email")
        subject = gr.Textbox(label="Subject", interactive=False, lines=1)
        body = gr.Textbox(label="Body", interactive=False, lines=5)
        
        gr.Markdown("### Your Response")
        with gr.Row():
            label_input = gr.Dropdown(
                choices=CustomerSupportTriageEnv.CATEGORIES,
                label="Category",
            )
            priority_input = gr.Dropdown(
                choices=CustomerSupportTriageEnv.PRIORITIES,
                label="Priority",
            )
        
        response_input = gr.Dropdown(
            choices=CustomerSupportTriageEnv.RESPONSE_TEMPLATES,
            label="Response Template",
        )
        escalate_input = gr.Checkbox(label="Escalate to Specialist")
        
        gr.Markdown("### Feedback")
        feedback = gr.Textbox(label="Grader Feedback", interactive=False, lines=3)
        
        with gr.Row():
            remaining = gr.Number(label="Remaining Emails", value=0, interactive=False)
            status = gr.Textbox(label="Status", interactive=False)
        
        state = gr.State(None)
        
        reset_button.click(
            fn=start_session,
            inputs=[task_dropdown],
            outputs=[state, subject, body, feedback, remaining, status],
        )
        
        gr.Button("✓ Submit Action", variant="primary").click(
            fn=step_session,
            inputs=[state, label_input, priority_input, response_input, escalate_input],
            outputs=[state, subject, body, feedback, remaining, status],
        )
    
    return demo


if __name__ == "__main__":
    import uvicorn
    
    # Create Gradio interface
    interface = create_interface()
    
    # Mount Gradio on FastAPI
    app = gr.mount_gradio_app(api, interface, path="/ui")
    
    # Run combined server
    uvicorn.run(app, host="0.0.0.0", port=7860)