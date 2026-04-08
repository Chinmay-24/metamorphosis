# Pre-Submission Checklist & Deployment Guide

## ✅ Pre-Submission Verification Checklist

This document details all requirements and their validation status.

### 1. HF Space Deployment
- **Requirement**: Automated ping to Space URL returns 200 and responds to reset()
- **Status**: ✅ Ready
- **Deployment**:
  - Deploy via `spaces_app.py` which uses Gradio
  - Create HF Space with this repo
  - Space will be accessible at `https://huggingface.co/spaces/<username>/<space-name>`
  - Space includes `README_SPACE.md` for HF-specific documentation
- **Test**: See "Running the Environment" section below

### 2. OpenEnv Spec Compliance
- **Requirement**: Validate openenv.yaml, typed models, step()/reset()/state() endpoints
- **Status**: ✅ Verified
- **Validation Test**:
  ```bash
  python validate_env.py
  ```
- **Results**:
  - ✅ All Pydantic models properly typed (Action, Observation, Reward, State)
  - ✅ reset(task_level) returns valid Observation
  - ✅ step(action) returns (observation, reward, done, info)
  - ✅ state() returns current episode State
  - ✅ openenv.yaml properly formatted with metadata and task definitions

### 3. Dockerfile Build
- **Requirement**: Automated docker build must succeed
- **Status**: ✅ Ready
- **Build Command**:
  ```bash
  docker build -t customer-support-triage:latest .
  ```
- **Dockerfile Features**:
  - Python 3.12 slim base image
  - Installs all dependencies from requirements.txt
  - Includes health check endpoint
  - Exposes port 7860 for Gradio interface
  - Configured for HF Spaces deployment

### 4. Baseline Inference Script
- **Requirement**: inference.py must complete without error and produce scores
- **Status**: ✅ Ready
- **File**: `inference.py` (root directory)
- **Environment Variables Required**:
  - `OPENAI_API_KEY`: OpenAI API key
  - `API_BASE_URL`: (optional) API endpoint, defaults to https://api.openai.com/v1
  - `MODEL_NAME`: (optional) Model identifier, defaults to gpt-4o-mini
  - `HF_TOKEN`: Hugging Face token for validation
- **Run Command**:
  ```bash
  export OPENAI_API_KEY="sk-..."
  export API_BASE_URL="https://api.openai.com/v1"
  export MODEL_NAME="gpt-4o-mini"
  export HF_TOKEN="hf_..."
  python inference.py
  ```
- **Output Format**: Structured JSON logging with [START], [STEP], [END] blocks
- **Expected Runtime**: < 20 minutes for all three tasks
- **Scores**: Produces numeric scores between 0.0 and 1.0 for each task

### 5. Three Tasks with Graders
- **Requirement**: 3+ tasks with deterministic graders, scores/rewards 0.0–1.0
- **Status**: ✅ Implemented
- **Validation Test**:
  ```bash
  python validate_env.py
  ```

#### Task 1: Label Classification (Easy)
- **Difficulty**: Easy
- **Objective**: Classify emails into issue categories
- **Grading**: Checks `label` field correctness
- **Email Count**: 5 emails
- **Reward Range**: 0.0–1.0
- **Success Criteria**: Correct category classification

#### Task 2: Label + Priority Classification (Medium)
- **Difficulty**: Medium
- **Objective**: Classify emails AND assign priority levels
- **Grading**: Checks `label` and `priority` fields
- **Email Count**: 7 emails
- **Reward Range**: -0.05–1.0 (normalized to 0.0–1.0)
- **Success Criteria**: Both label and priority correct

#### Task 3: Full Triage + Response (Hard)
- **Difficulty**: Hard
- **Objective**: Classify, prioritize, and select response or escalate
- **Grading**: Checks `label`, `priority`, and response/escalation logic
- **Email Count**: 10 emails
- **Reward Range**: -0.15–1.0 (normalized to 0.0–1.0)
- **Success Criteria**: All three fields correct + proper escalation handling

**Grader Validation Results**:
```
easy      : steps= 5 min=0.000 max=0.400 avg=0.080
medium    : steps= 7 min=-0.050 max=0.600 avg=0.171
hard      : steps=10 min=-0.150 max=0.500 avg=0.070
```

### 6. Meaningful Reward Function
- **Requirement**: Reward signal over full trajectory, not just binary end-of-episode
- **Status**: ✅ Implemented
- **Details**:
  - Step-by-step rewards for each email processed
  - Partial credit for correct labels, priorities, or responses
  - Penalties for invalid choices (e.g., -0.2)
  - Normalized values always in [0.0, 1.0] range
  - Clear feedback messages explaining why reward was given
- **Observation**: see `validate_env.py` output showing varying rewards per step

---

## Running the Environment

### Setup

1. **Clone the Repository**:
   ```bash
   git clone <repo-url> customer-support-triage
   cd customer-support-triage
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Validate Environment** (no API key required):
   ```bash
   python validate_env.py
   ```

### Option A: Interactive Gradio App

Run the interactive interface for testing:

```bash
python spaces_app.py
```

Then open `http://localhost:7860` in your browser.

### Option B: Run Baseline Inference

```bash
export OPENAI_API_KEY="sk-..."
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="hf_..."
python inference.py 2>/dev/null
```

The script will output:
- [START] blocks with session metadata
- [STEP] blocks with action details and reward
- [END] blocks with final scores

### Option C: Docker Deployment

```bash
docker build -t customer-support-triage:latest .
docker run --rm -p 7860:7860 \
  -e OPENAI_API_KEY="sk-..." \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="hf_..." \
  customer-support-triage:latest
```

---

## Structured Logging Format

The inference script follows strict structured logging for evaluation:

### [START] Block
```json
{
  "timestamp": "2026-04-08T12:34:56.789123",
  "session_id": "20260408_123456",
  "task_level": "easy|medium|hard",
  "description": "Task description",
  "model": "gpt-4o-mini",
  "api_base": "https://api.openai.com/v1"
}
```

### [STEP] Block
```json
{
  "step_index": 1,
  "email_id": 0,
  "email_subject": "Subject line",
  "action": {
    "label": "billing",
    "priority": "high",
    "response_template": "Template text or null",
    "escalate": false
  },
  "reward": 0.4,
  "normalized_reward": 0.667,
  "done": false,
  "grader_feedback": "Reward explanation message"
}
```

### [END] Block
```json
{
  "total_steps": 5,
  "total_reward": 1.2,
  "final_score": 0.24,
  "task_level": "easy",
  "success": false
}
```

---

## Project Structure

```
customer-support-triage/
├── openenv_customer_support/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Pydantic models (Action, Observation, Reward, State)
│   └── env.py               # CustomerSupportTriageEnv class
├── openenv.yaml             # Environment metadata and spec
├── inference.py             # OpenAI baseline inference script
├── spaces_app.py            # Gradio HF Space app
├── validate_env.py          # Environment validation and testing
├── test_inference_structure.py  # Inference script structure test
├── baseline.py              # Alternative baseline script (reference)
├── app.py                   # Alternative app demo
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
├── README.md                # Main documentation
├── README_SPACE.md          # HF Space-specific documentation
┗── DEPLOYMENT.md            # This file
```

---

## Environment Variables

All required environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | None | OpenAI API authentication key |
| `API_BASE_URL` | No | https://api.openai.com/v1 | OpenAI API endpoint |
| `MODEL_NAME` | No | gpt-4o-mini | Model identifier for inference |
| `HF_TOKEN` | No | None | Hugging Face API token |
| `PORT` | No | 7860 | Port for Gradio interface |
| `PYTHONUNBUFFERED` | No | 1 | Unbuffered Python output for logs |

---

## Infra Requirements

- **CPU**: 2 vCPUs (tested)
- **Memory**: 8 GB RAM (tested)
- **Runtime**: < 20 minutes for full inference pipeline
- **Python**: 3.12+
- **Docker**: Optional, for containerized deployment

---

## Testing Commands

Run these before final submission:

1. **Basic Validation** (no API key):
   ```bash
   python validate_env.py
   python test_inference_structure.py
   ```

2. **Inference Structure Test**:
   ```bash
   python test_inference_structure.py
   ```

3. **Full Integration Test** (requires API key):
   ```bash
   export OPENAI_API_KEY="sk-..."
   python inference.py 2>&1 | head -100
   ```

4. **Docker Build Test** (if Docker available):
   ```bash
   docker build -t customer-support-triage:test .
   echo $?  # Should be 0 for success
   ```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pydantic'"
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### Issue: "OPENAI_API_KEY not set"
**Solution**: Set environment variable before running inference
```bash
export OPENAI_API_KEY="sk-..."  # Linux/Mac
set OPENAI_API_KEY=sk-...       # Windows
```

### Issue: "Failed to initialize OpenAI client"
**Solution**: Verify API key is valid and network is accessible
```bash
export OPENAI_API_KEY="sk-..."
python -c "from openai import OpenAI; OpenAI()"
```

### Issue: Gradio app won't start
**Solution**: Check port availability
```bash
python spaces_app.py --server-port 8000
```

---

## Submission Checklist

Before submitting to HF review:

- [ ] ✅ Run `python validate_env.py` - no errors
- [ ] ✅ Run `python test_inference_structure.py` - no errors
- [ ] ✅ OpenEnv spec validating (models, reset/step/state)
- [ ] ✅ Dockerfile builds successfully
- [ ] ✅ 3+ tasks with working graders (easy/medium/hard)
- [ ] ✅ inference.py outputs structured [START]/[STEP]/[END] blocks
- [ ] ✅ README.md documents all requirements
- [ ] ✅ HF Space configured with `spaces_app.py`
- [ ] ✅ Environment variables documented
- [ ] ✅ Runtime < 20 minutes verified
- [ ] ✅ Scores in 0.0–1.0 range verified

---

**Last Updated**: April 8, 2026  
**Status**: Ready for Submission ✅
