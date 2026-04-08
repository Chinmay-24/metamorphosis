# Customer Support Triage OpenEnv

A real-world OpenEnv environment that simulates customer support email triage and resolution. The agent must classify inbound support emails, assign priority levels, and in the hardest task, provide the correct canned response or escalate sensitive cases to specialists.

This environment implements the full OpenEnv specification with typed Pydantic models, meaningful trajectory-based rewards, and three difficulty levels (easy → medium → hard) with deterministic graders producing scores in the 0.0–1.0 range.

## 🎯 Environment Overview

**Motivation**: Customer support teams handle hundreds of emails daily. This environment trains agents to perform email triage—the process of classifying, prioritizing, and routing emails to the appropriate team or response path. This is a real-world task humans perform constantly.

### Core Workflow
1. Agent receives an email with subject and body
2. Agent classifies the issue (category), assigns priority, and chooses action
3. Environment provides step-by-step reward feedback
4. Agent processes multiple emails in sequence
5. Episode ends when all emails in the queue are triaged

## 📦 OpenEnv Specification

### API Endpoints

```python
from openenv_customer_support import CustomerSupportTriageEnv, Action, Observation, Reward

# Initialize
env = CustomerSupportTriageEnv(task_level="easy")

# Reset episode
obs: Observation = env.reset("easy")

# Step through environment
action = Action(
    label="billing",
    priority="high",
    response_template="Confirm the charge and offer a refund if eligible.",
    escalate=False
)
obs, reward, done, info = env.step(action)

# Get current state
state = env.state()  # Returns State object with episode metadata
```

### Observation Space

The `Observation` Pydantic model contains:

| Field | Type | Description |
|-------|------|-------------|
| `email_subject` | `str` | Subject line of the current email |
| `email_body` | `str` | Body text of the current email |
| `available_labels` | `List[str]` | Valid issue categories (billing, technical, account, feedback, cancellation) |
| `available_priorities` | `List[str]` | Valid priority levels (low, medium, high) |
| `available_responses` | `List[str]` | Canned response templates the agent can choose |
| `remaining_emails` | `int` | Number of unprocessed emails in the queue |
| `task_level` | `str` | Current task difficulty (easy, medium, hard) |
| `step_index` | `int` | Zero-indexed position in the episode |

### Action Space

The `Action` Pydantic model for agent decisions:

| Field | Type | Description |
|-------|------|-------------|
| `label` | `str` | Issue category classification (required) |
| `priority` | `str` | Priority level assignment (required) |
| `response_template` | `Optional[str]` | Selected canned response or `None` |
| `escalate` | `bool` | Whether to escalate to specialist (escalates take precedence) |

### Reward Space

The `Reward` Pydantic model provides step-level feedback:

| Field | Type | Description |
|-------|------|-------------|
| `value` | `float` | Raw reward value (may be negative for wrong actions) |
| `normalized_value` | `float` | Normalized score in [0.0, 1.0] range (always valid) |
| `message` | `str` | Human-readable explanation of the reward |

### State Space

The `State` Pydantic model tracks episode progress:

| Field | Type | Description |
|-------|------|-------------|
| `task_level` | `str` | Current task difficulty |
| `step_index` | `int` | Current step in episode |
| `remaining_emails` | `int` | Emails left to process |
| `cumulative_reward` | `float` | Sum of all rewards so far |
| `done` | `bool` | Whether episode is complete |

## 🎓 Tasks & Grading

Three difficulty levels with increasing complexity:

### Task 1: Label Classification (Easy)
- **Objective**: Classify emails into the correct issue category
- **Grading**: Checks if selected `label` matches ground truth
- **Queue Size**: 5 emails
- **Reward Structure**:
  - Correct label: +0.4
  - Incorrect label: 0.0
  - Invalid label: -0.2 (penalty)
- **Difficulty**: Basic multi-class classification
- **Expected Baseline**: 40–60% accuracy

### Task 2: Label + Priority Classification (Medium)
- **Objective**: Classify emails AND assign the correct priority level
- **Grading**: Checks both `label` and `priority` fields
- **Queue Size**: 7 emails
- **Reward Structure**:
  - Correct label: +0.4
  - Correct priority: +0.2
  - Wrong priority: -0.05
  - Invalid inputs: -0.2 each
- **Difficulty**: Multi-dimensional classification with coupling
- **Expected Baseline**: 25–50% accuracy

### Task 3: Full Triage + Response (Hard)
- **Objective**: Classify, prioritize, AND provide correct response or escalate appropriately
- **Grading**: Checks `label`, `priority`, `response_template`, and `escalate` logic
- **Queue Size**: 10 emails
- **Reward Structure**:
  - Correct label: +0.4
  - Correct priority: +0.2
  - Correct response OR correct escalation: +0.4
  - Wrong response/escalation: -0.1
  - Invalid inputs: -0.2 each
  - Penalties prevent scores below -0.2
- **Difficulty**: Complex decision-making with multiple correct paths
- **Expected Baseline**: 10–30% accuracy

## 💰 Reward Function

The reward function provides meaningful gradient signals throughout the episode:

- **Step-Level Rewards**: Each action receives immediate feedback, not just end-of-episode scores
- **Partial Credit**: Correct classifications give positive rewards even if future decisions are wrong
- **Penalty Signal**: Invalid actions and wrong decisions receive negative rewards to discourage them
- **Normalization**: All normalized rewards stay within [0.0, 1.0] for consistency
- **Trajectory Signal**: Cumulative rewards monotonically increase with correct actions
- **Detailed Feedback**: Each reward includes a human-readable message explaining the score

Example trajectory (3 steps in easy task):
```
Step 1: +0.4 (correct label) → normalized: 0.667
Step 2:  0.0 (wrong label)   → normalized: 0.167
Step 3: +0.4 (correct label) → normalized: 0.667
```

## 🚀 Baseline Inference

The repository includes `inference.py`, a baseline agent using gpt-4o-mini via OpenAI API.

### Running Baseline

```bash
export OPENAI_API_KEY="sk-..."
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="hf_..."

python inference.py
```

### Output Format

The inference script logs structured JSON for evaluation:

```
[START] {"timestamp": "2026-04-08T12:34:56.789123", "session_id": "20260408_123456", "task_level": "easy", ...}
[STEP] {"step_index": 1, "email_id": 0, "action": {...}, "reward": 0.4, "normalized_reward": 0.667, ...}
[STEP] {"step_index": 2, "email_id": 1, "action": {...}, "reward": 0.0, "normalized_reward": 0.167, ...}
[END] {"total_steps": 5, "total_reward": 1.2, "final_score": 0.24, "task_level": "easy", "success": false}
```

### Expected Scores
- Easy: 0.3–0.6 (35–60% of emails correct)
- Medium: 0.1–0.4 (20–45% of emails correct)
- Hard: 0.05–0.25 (10–30% of emails correct)

## 📥 Setup & Installation

### Prerequisites
- Python 3.10+
- pip or conda
- OpenAI API key (for baseline inference)
- Hugging Face token (optional, for Space deployment)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd customer-support-triage

# Install dependencies
pip install -r requirements.txt

# Validate environment (no API key required)
python validate_env.py

# Run Gradio demo (local testing)
python spaces_app.py
# Open: http://localhost:7860
```

## 🐳 Docker & Deployment

### Docker Build

```bash
docker build -t customer-support-triage:latest .
```

### Docker Run

```bash
docker run --rm -it -p 7860:7860 \
  -e OPENAI_API_KEY="sk-..." \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="hf_..." \
  customer-support-triage:latest
```

### Hugging Face Spaces

Deploy directly to HF Spaces:
1. Create new Space at https://huggingface.co/spaces
2. Set SDK to Gradio
3. Push this repository as the Space code
4. Space will run `spaces_app.py` automatically

## 📚 Project Structure

```
customer-support-triage/
├── openenv_customer_support/     # Main package
│   ├── __init__.py               # Package exports
│   ├── models.py                 # Pydantic models
│   └── env.py                    # Environment implementation
├── inference.py                  # OpenAI baseline script
├── spaces_app.py                 # HF Spaces Gradio app
├── validate_env.py               # Environment validator
├── test_inference_structure.py   # Inference structure tests
├── Dockerfile                    # Container definition
├── openenv.yaml                  # OpenEnv metadata
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── README_SPACE.md               # HF Space documentation
└── DEPLOYMENT.md                 # Deployment guide
```

## 🧪 Validation

Run validation without an API key:

```bash
# Validate environment spec compliance
python validate_env.py

# Validate inference script structure
python test_inference_structure.py
```

Expected output: ✅ All validation checks pass

## 🎮 Interactive Usage

### Web Interface (Gradio)

```bash
python spaces_app.py
```

Then interact at http://localhost:7860

### Python API

```python
from openenv_customer_support import CustomerSupportTriageEnv, Action

env = CustomerSupportTriageEnv("easy")
obs = env.reset("easy")

# Get first email
print(f"Subject: {obs.email_subject}")
print(f"Body: {obs.email_body}")

# Take action
action = Action(
    label="billing",
    priority="high",
    response_template=obs.available_responses[0],
    escalate=False
)

obs, reward, done, info = env.step(action)
print(f"Reward: {reward.value:.3f} ({reward.message})")
```

## 📋 Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | Yes* | N/A | OpenAI API authentication |
| `API_BASE_URL` | No | https://api.openai.com/v1 | Custom LLM endpoint |
| `MODEL_NAME` | No | gpt-4o-mini | Model identifier |
| `HF_TOKEN` | No | N/A | Hugging Face authentication |
| `PORT` | No | 7860 | Gradio server port |

\* Only required when running `inference.py`

## ⚙️ Infra Requirements

- **Minimum CPU**: 2 vCPUs
- **Minimum Memory**: 8 GB
- **Python Version**: 3.10–3.12
- **Runtime**: < 20 minutes for full inference
- **Network**: Required for OpenAI API calls

## 🔗 Files & Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide and pre-submission checklist
- [openenv.yaml](openenv.yaml) - OpenEnv specification metadata
- [inference.py](inference.py) - Baseline agent implementation
- [spaces_app.py](spaces_app.py) - Interactive Gradio interface

## 📝 Notes

- This environment does NOT simulate game play or toy tasks—it models actual real-world customer support workflows
- The reward function provides trajectory-level signals suitable for RL training
- Graders are deterministic and fully reproducible across runs
- All models are strongly typed using Pydantic for API safety
- Scores and rewards are normalized to [0.0, 1.0] for consistency

## 🎓 Citation

If you use this environment in your research, please cite:

```bibtex
@software{customer_support_triage_env,
  title = {Customer Support Triage OpenEnv},
  author = {GitHub Copilot},
  year = {2026},
  month = {April},
  license = {Apache-2.0}
}
```

## 📄 License

This project is licensed under the Apache 2.0 License. See LICENSE file for details.

---

**Last Updated**: April 8, 2026  
**Status**: Ready for Submission ✅

