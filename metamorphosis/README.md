---
title: Customer Support Triage
emoji: 🦋
colorFrom: purple
colorTo: blue
sdk: docker
app_file: spaces_app.py
pinned: false
---

# Metamorphosis: Customer Support Triage OpenEnv

An OpenEnv environment for training baseline agents on customer support email triage tasks.

## Features

- **3 Difficulty Levels**: Easy, Medium, Hard
- **Deterministic Graders**: Consistent evaluation across runs
- **Trajectory-based Rewards**: Meaningful feedback for agent learning
- **REST API**: FastAPI endpoints for evaluation
- **Interactive UI**: Gradio interface for manual testing
- **Production Ready**: Docker-based deployment

## Quick Start

### Local Testing

```bash
pip install -r requirements.txt
python inference.py
```

### Web Interface

```bash
python spaces_app.py
```

Visit `http://localhost:7860/ui` for the Gradio interface.

### API Endpoints

- `POST /reset` - Reset environment
- `POST /step` - Execute action
- `GET /health` - Health check
- `GET /` - API documentation

## Environment Structure

- `openenv_customer_support/` - Core environment package
  - `models.py` - Pydantic models
  - `env.py` - Main environment class
  - `__init__.py` - Package exports
- `inference.py` - Baseline OpenAI agent
- `spaces_app.py` - FastAPI + Gradio application
- `openenv.yaml` - Environment specification

## Validation

```bash
python validate_env.py
python test_inference_structure.py
```

## Documentation

- [Pre-Submission Requirements](PRE_SUBMISSION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Submission Status](SUBMISSION_READY.md)
