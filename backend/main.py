"""Apex Loyalty System — FastAPI backend."""
import os
import sys

# Allow imports from agents/ sub-package
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from agents import orchestration_agent, scoring_agent

app = FastAPI(title="Apex Loyalty — AI Agent Pipeline", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/high-risk-customers")
def high_risk_customers():
    """
    Full two-agent pipeline:
      1. OrchestrationAgent consolidates all data sources
      2. ScoringAgent applies the zero-redemption rule and scores customers
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Step 1 — OrchestrationAgent
        consolidated = orchestration_agent.run(api_key=api_key)

        # Step 2 — ScoringAgent
        scoring_result = scoring_agent.run(consolidated, api_key=api_key)

        return {
            "customers":           scoring_result["customers"],
            "summary":             scoring_result["summary"],
            "orchestration_summary": consolidated.get("agent_summary", ""),
            "agent_mode":          scoring_result["agent_mode"],
            "total_sources":       consolidated.get("total_customers", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
