from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from openenv_customer_support import CustomerSupportTriageEnv
import json

app = FastAPI(title="Metamorphosis OpenEnv", version="1.0.0")

# Session storage
env_sessions = {}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reset")
async def reset(difficulty: str = "easy", session_id: str = "default"):
    try:
        env = CustomerSupportTriageEnv()
        state = env.reset(difficulty)
        env_sessions[session_id] = env
        return state.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: str, session_id: str = "default"):
    try:
        if session_id not in env_sessions:
            raise HTTPException(status_code=400, detail="Session not initialized. Call /reset first.")
        
        env = env_sessions[session_id]
        obs, reward, done, info = env.step(action)
        
        return {
            "observation": obs.dict(),
            "reward": reward.dict(),
            "done": done,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "name": "Metamorphosis OpenEnv",
        "endpoints": {
            "GET /health": "Health check",
            "POST /reset": "Reset environment",
            "POST /step": "Execute action"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
