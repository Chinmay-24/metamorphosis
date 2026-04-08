import gradio as gr
from openenv_customer_support import Action, CustomerSupportTriageEnv


def start_session(task_level: str):
    env = CustomerSupportTriageEnv(task_level=task_level)
    obs = env.reset(task_level)
    return env, obs.email_subject, obs.email_body, "Ready to triage the first email.", obs.remaining_emails, "Session initialized."


def step_session(env, label, priority, response_template, escalate):
    if env is None:
        return None, "", "", False, 0, "Session is not initialized."
    action = Action(label=label, priority=priority, response_template=response_template or None, escalate=escalate)
    obs, reward, done, info = env.step(action)
    status = (
        "Finished all emails." if done else "Continue to the next email."
    )
    return (
        env,
        obs.email_subject,
        obs.email_body,
        reward.message,
        obs.remaining_emails,
        status,
    )


def app():
    with gr.Blocks() as demo:
        gr.Markdown("# Customer Support Triage OpenEnv")
        gr.Markdown(
            "Use the form below to classify support emails, set priorities, and choose the best response or escalation action."
        )

        with gr.Row():
            task_dropdown = gr.Radio(["easy", "medium", "hard"], label="Task difficulty", value="easy")
            reset_button = gr.Button("Reset Task")

        subject = gr.Textbox(label="Email subject", interactive=False)
        body = gr.Textbox(label="Email body", lines=6, interactive=False)
        label_input = gr.Dropdown(choices=CustomerSupportTriageEnv.CATEGORIES, label="Label")
        priority_input = gr.Dropdown(choices=CustomerSupportTriageEnv.PRIORITIES, label="Priority")
        response_input = gr.Dropdown(choices=CustomerSupportTriageEnv.RESPONSE_TEMPLATES, label="Response template")
        escalate_input = gr.Checkbox(label="Escalate to specialist")
        feedback = gr.Textbox(label="Feedback", interactive=False)
        remaining = gr.Number(label="Remaining emails", value=0, interactive=False)
        status = gr.Textbox(label="Status", interactive=False)

        state = gr.State(None)

        reset_button.click(
            fn=start_session,
            inputs=[task_dropdown],
            outputs=[state, subject, body, feedback, remaining, status],
        )

        gr.Button("Submit Action").click(
            fn=step_session,
            inputs=[state, label_input, priority_input, response_input, escalate_input],
            outputs=[state, subject, body, feedback, remaining, status],
        )

    return demo


if __name__ == "__main__":
    app().launch(server_name="0.0.0.0", server_port=7860)
