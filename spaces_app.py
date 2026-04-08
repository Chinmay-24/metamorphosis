"""
Hugging Face Space application for interactive triage demonstration.
Deployed at the root of the repository.
"""

import gradio as gr
from openenv_customer_support import Action, CustomerSupportTriageEnv


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
    interface = create_interface()
    interface.launch(server_name="0.0.0.0", server_port=7860, share=False)
